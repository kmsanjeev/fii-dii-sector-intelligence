"""
Broker Sync Engine -- Phase 22

Orchestrates:
  1. Load a selected provider adapter (Dhan API or CSV fallback)
  2. Fetch holdings + optional trade history
  3. Persist to broker_holdings.csv
  4. Merge trade history into portfolio transactions.csv (with dedup)
  5. Trigger Phase 20 portfolio rebuild

Credentials live in data/portfolio/broker_auth.json (gitignored, never in .env).
Run:  py -3.11 -m engines.broker.sync_engine
"""

import json
import base64
import hashlib
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from cryptography.fernet import Fernet, InvalidToken

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.broker.base import BrokerAdapter, Holding, Trade
from engines.providers.fabric import Capability, ProviderFabric, default_provider_fabric
from engines.providers.dhan_auth import DhanAuthManager

logger = get_logger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

PORTFOLIO_DIR    = cfg.DATA_DIR / "portfolio"
BROKER_HOLDINGS  = PORTFOLIO_DIR / "broker_holdings.csv"
TRANSACTIONS_CSV = PORTFOLIO_DIR / "transactions.csv"
BROKER_AUTH      = PORTFOLIO_DIR / "broker_auth.json"     # gitignored via data/**/*.json
BROKER_KEY       = cfg.DATA_DIR / "auth" / "broker_credentials.key"
SYNC_LOG         = PORTFOLIO_DIR / "broker_sync_log.csv"

HOLDINGS_COLS = [
    "symbol", "exchange", "isin", "qty", "avg_cost",
    "ltp", "current_value", "pnl", "pnl_pct", "last_synced",
]

TRANSACTION_COLS = ["date", "symbol", "action", "qty", "price", "notes"]


def get_provider_fabric() -> ProviderFabric:
    """Return policy metadata without reading or exposing provider secrets."""
    fabric = default_provider_fabric()
    creds = load_credentials()
    auth_manager = DhanAuthManager()
    dhan_configured = auth_manager.has_credentials()
    if creds or dhan_configured:
        provider_id = str((creds or {}).get("broker", "dhan")).lower()
        state = auth_manager.read_validation_state() if provider_id == "dhan" else {}
        state_caps = set()
        for value in state.get("validated_capabilities", []):
            try:
                state_caps.add(Capability(str(value)))
            except ValueError:
                continue
        capabilities = frozenset({
            Capability.HOLDINGS, Capability.POSITIONS, Capability.FUNDS,
            Capability.TRADES, Capability.ORDER_HISTORY,
        } | state_caps)
        data_plan = str(state.get("data_plan", "UNKNOWN")).upper()
        authenticated = bool(state.get("authenticated"))
        validated = bool(authenticated and state.get("runtime_health") == "HEALTHY")
        try:
            from engines.providers.fabric import ProviderConnection
            fabric.upsert_connection(ProviderConnection(
                connection_id=f"local-{provider_id}",
                provider_id=provider_id,
                display_name=f"Configured {provider_id}",
                auth_state="VALID" if authenticated else "CONFIGURED",
                connection_state="CONNECTED" if authenticated else "AVAILABLE",
                credential_reference="local-encrypted-broker-auth",
                authorized_capabilities=capabilities,
                entitlement_state="ENTITLED" if data_plan == "ACTIVE" else "ENTITLEMENT_REQUIRED" if data_plan not in {"", "UNKNOWN"} else "UNKNOWN",
                health="HEALTHY" if validated else "ENTITLEMENT_BLOCKED" if data_plan not in {"", "UNKNOWN", "ACTIVE"} else "UNKNOWN",
                limitations=("Health and data entitlement are provider-specific and must be validated by the adapter.",),
            ))
        except ValueError:
            logger.warning("[ProviderFabric] Stored provider is not registered: %s", provider_id)
    return fabric


def resolve_provider(capability: str) -> dict:
    """Resolve a capability into a safe, serializable policy result."""
    try:
        requested = Capability(str(capability).upper())
    except ValueError:
        return {"capability": capability, "selected_provider": None, "reason": "UNKNOWN_CAPABILITY"}
    return get_provider_fabric().resolve(requested).__dict__


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _mask_client_id(client_id: str) -> str:
    return (client_id[:4] + "****") if client_id else ""


def _derive_fernet_key(secret: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())


def _get_fernet() -> Fernet:
    env_secret = os.environ.get("VEDA_BROKER_CREDENTIAL_SECRET", "").strip()
    if env_secret:
        return Fernet(_derive_fernet_key(env_secret))

    BROKER_KEY.parent.mkdir(parents=True, exist_ok=True)
    if BROKER_KEY.exists():
        return Fernet(BROKER_KEY.read_bytes().strip())

    key = Fernet.generate_key()
    tmp = BROKER_KEY.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        f.write(key)
    shutil.move(str(tmp), str(BROKER_KEY))
    try:
        os.chmod(BROKER_KEY, 0o600)
    except OSError:
        pass
    return Fernet(key)


def _write_credentials_file(payload: dict) -> None:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BROKER_AUTH.with_suffix(".tmp.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    shutil.move(str(tmp), str(BROKER_AUTH))


def save_credentials(broker: str, client_id: str, access_token: str) -> None:
    """Persist broker credentials without leaving the access token in plaintext on disk."""
    now = datetime.now().isoformat()
    cipher = _get_fernet().encrypt(
        json.dumps(
            {
                "broker": broker,
                "client_id": client_id,
                "access_token": access_token,
                "set_at": now,
            }
        ).encode("utf-8")
    ).decode("utf-8")
    payload = {
        "version": 2,
        "broker": broker,
        "client_id_mask": _mask_client_id(client_id),
        "set_at": now,
        "ciphertext": cipher,
    }
    _write_credentials_file(payload)
    logger.info("[Broker] Credentials saved for broker=%s client=%s", broker, _mask_client_id(client_id))


def load_credentials() -> Optional[dict]:
    if not BROKER_AUTH.exists():
        return None
    try:
        with open(BROKER_AUTH, encoding="utf-8") as f:
            payload = json.load(f)
        if "ciphertext" in payload:
            decrypted = _get_fernet().decrypt(str(payload["ciphertext"]).encode("utf-8"))
            data = json.loads(decrypted.decode("utf-8"))
            data["set_at"] = payload.get("set_at", data.get("set_at"))
            return data
        if "client_id" in payload and "access_token" in payload:
            logger.warning("[Broker] Legacy plaintext broker credentials detected; migrating to encrypted local storage")
            save_credentials(
                str(payload.get("broker", "dhan")),
                str(payload.get("client_id", "")),
                str(payload.get("access_token", "")),
            )
            return load_credentials()
    except (InvalidToken, ValueError, TypeError, json.JSONDecodeError):
        return None
    except Exception:
        return None


def get_adapter(creds: Optional[dict] = None) -> Optional[BrokerAdapter]:
    """
    Build adapter from stored credentials.
    Returns None if no credentials saved.
    """
    if creds is None:
        creds = load_credentials()
    if not creds:
        return None

    broker = str(creds.get("broker", "dhan")).lower()
    if broker == "dhan":
        from engines.broker.dhan_adapter import DhanAdapter
        return DhanAdapter(creds["client_id"], creds["access_token"])
    if broker == "csv":
        from engines.broker.csv_adapter import CsvAdapter
        return CsvAdapter(
            holdings_csv = creds.get("holdings_csv", ""),
            trades_csv   = creds.get("trades_csv", ""),
        )
    raise ValueError(f"Unknown broker: {broker}")


# ── Sync logic ─────────────────────────────────────────────────────────────────

def _save_holdings(holdings: list[Holding]) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        {
            "symbol":        h.symbol,
            "exchange":      h.exchange,
            "isin":          h.isin,
            "qty":           h.qty,
            "avg_cost":      h.avg_cost,
            "ltp":           h.ltp,
            "current_value": h.current_value,
            "pnl":           h.pnl,
            "pnl_pct":       h.pnl_pct,
            "last_synced":   now,
        }
        for h in holdings
    ]
    df  = pd.DataFrame(rows, columns=HOLDINGS_COLS)
    tmp = BROKER_HOLDINGS.with_suffix(".tmp.csv")
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(BROKER_HOLDINGS))
    logger.info("[Broker] Saved %d holdings to %s", len(holdings), BROKER_HOLDINGS)


def _merge_trades(trades: list[Trade]) -> int:
    """
    Append new trades from broker into transactions.csv (dedup by date+symbol+action+qty+price).
    Returns count of new rows added.
    """
    if not trades:
        return 0

    new_rows = pd.DataFrame([{
        "date":   t.date,
        "symbol": t.symbol,
        "action": t.action,
        "qty":    t.qty,
        "price":  t.price,
        "notes":  f"dhan:{t.order_id}" if t.order_id else "broker-import",
    } for t in trades])

    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

    if TRANSACTIONS_CSV.exists() and TRANSACTIONS_CSV.stat().st_size > 50:
        existing = pd.read_csv(TRANSACTIONS_CSV, dtype=str)
        combined = pd.concat([existing, new_rows], ignore_index=True)
        # Dedup on business key
        combined = combined.drop_duplicates(
            subset=["date", "symbol", "action", "qty", "price"]
        )
        added = len(combined) - len(existing)
    else:
        combined = new_rows
        added    = len(new_rows)

    if added > 0:
        tmp = TRANSACTIONS_CSV.with_suffix(".tmp.csv")
        combined.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(TRANSACTIONS_CSV))
        logger.info("[Broker] Merged %d new trades into transactions.csv", added)

    return max(added, 0)


def _log_sync(broker: str, holdings_count: int, trades_imported: int,
              status: str, error: str = "") -> None:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    header = not SYNC_LOG.exists()
    with open(SYNC_LOG, "a", encoding="utf-8") as f:
        if header:
            f.write("synced_at,broker,holdings_count,trades_imported,status,error\n")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        err = error.replace('"', "'").replace("\n", " ")[:200]
        f.write(f'"{now}","{broker}",{holdings_count},{trades_imported},"{status}","{err}"\n')


def run(import_trades: bool = False,
        from_date: str = "",
        to_date: str = "") -> dict:
    """
    Full sync: holdings + optional trade history import.

    Returns:
        dict with keys: broker, holdings_count, trades_imported, status, error
    """
    creds = load_credentials()
    if not creds:
        return {"status": "NO_CREDENTIALS", "error": "No broker credentials saved.", "holdings_count": 0}

    broker = creds.get("broker", "dhan")
    try:
        adapter = get_adapter(creds)
        if adapter is None:
            return {"status": "ERROR", "error": "Could not build adapter", "holdings_count": 0}

        holdings = adapter.get_holdings()
        _save_holdings(holdings)

        trades_imported = 0
        if import_trades:
            end   = to_date   or datetime.now().strftime("%Y-%m-%d")
            start = from_date or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            trades = adapter.get_trade_history(start, end)
            trades_imported = _merge_trades(trades)

        # Trigger portfolio rebuild so intelligence overlay is fresh
        try:
            from engines.portfolio.portfolio_engine import rebuild
            rebuild()
        except Exception as exc:
            logger.warning("[Broker] Portfolio rebuild after sync failed: %s", exc)

        _log_sync(broker, len(holdings), trades_imported, "DONE")
        return {
            "status":          "DONE",
            "broker":          broker,
            "holdings_count":  len(holdings),
            "trades_imported": trades_imported,
            "error":           "",
        }

    except Exception as exc:
        logger.error("[Broker] Sync failed: %s", exc)
        _log_sync(broker, 0, 0, "FAILED", str(exc))
        return {"status": "FAILED", "error": str(exc), "holdings_count": 0}


def load_broker_holdings() -> pd.DataFrame:
    """Load last synced holdings from disk."""
    if not BROKER_HOLDINGS.exists():
        return pd.DataFrame(columns=HOLDINGS_COLS)
    return pd.read_csv(BROKER_HOLDINGS)


def get_status() -> dict:
    """Return current connection + sync status for the API."""
    creds = load_credentials()
    holdings_count = 0
    last_synced    = None

    if BROKER_HOLDINGS.exists():
        try:
            df = pd.read_csv(BROKER_HOLDINGS, usecols=["symbol", "last_synced"])
            holdings_count = len(df)
            if not df.empty:
                last_synced = str(df["last_synced"].iloc[0])
        except Exception:
            pass

    return {
        "connected":      creds is not None,
        "broker":         creds.get("broker") if creds else None,
        "client_id":      _mask_client_id(str(creds.get("client_id", ""))) if creds else None,
        "credentials_set_at": creds.get("set_at") if creds else None,
        "holdings_count": holdings_count,
        "last_synced":    last_synced,
        "provider_fabric": {
            "mode": "BROKER_CONNECTED" if creds else "NO_BROKER",
            "providers": [manifest.provider_id for manifest in get_provider_fabric().manifests()],
            "portfolio_import_available": True,
        },
    }


# ── Overlay intelligence on broker holdings ────────────────────────────────────

def overlay_intelligence(holdings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join broker holdings with intelligence outputs.
    Same columns as Portfolio page for consistency.
    """
    if holdings_df.empty:
        return holdings_df

    df = holdings_df.copy()
    df["symbol"] = df["symbol"].str.strip().str.upper()

    bull_csv  = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
    ml_csv    = cfg.INTELLIGENCE_DIR / "ml_bull_run_scores.csv"
    conf_csv  = cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
    rot_csv   = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"

    if bull_csv.exists():
        bull = pd.read_csv(bull_csv, usecols=["symbol", "label", "bull_run_score", "sector"])
        bull["symbol"] = bull["symbol"].str.strip().str.upper()
        df = df.merge(bull, on="symbol", how="left")

    if ml_csv.exists():
        ml = pd.read_csv(ml_csv, usecols=["symbol", "ml_bull_run_score"])
        ml["symbol"] = ml["symbol"].str.strip().str.upper()
        df = df.merge(ml, on="symbol", how="left")

    if conf_csv.exists():
        conf = pd.read_csv(conf_csv, usecols=["symbol", "confidence_score"])
        conf["symbol"] = conf["symbol"].str.strip().str.upper()
        df = df.merge(conf, on="symbol", how="left")

    if rot_csv.exists():
        rot = pd.read_csv(rot_csv, usecols=["sector", "rotation_signal"])
        if "sector" in df.columns:
            df = df.merge(rot, on="sector", how="left")

    df["key_signal"] = df.apply(_key_signal, axis=1)
    return df


def _key_signal(row) -> str:
    label   = str(row.get("label") or "")
    rot     = str(row.get("rotation_signal") or "")
    pnl_pct = float(row.get("pnl_pct") or 0)
    ann     = float(row.get("confidence_score") or 0)

    # Taxonomy fix (Phase V-DATA-2): was STRONG_CANDIDATE/AVOID, which
    # bull_run_probability_engine.py stopped producing a while back --
    # these two branches never fired. ACCUMULATION (a real current label,
    # distinct from the "ACCUMULATION" output text used below for EMERGING
    # positions) had no branch at all.
    if label == "BULL_RUN":                  return "STRONG BUY"
    if label == "MARKDOWN":                  return "REVIEW POSITION"
    if label == "EMERGING" and ann > 60:     return "MOMENTUM BUILDING"
    if rot   == "EARLY_ROTATION":            return "SECTOR ROTATING IN"
    if label == "ACCUMULATION":              return "BASE BUILDING"
    if label == "EMERGING":                  return "ACCUMULATION"
    if label == "WATCHLIST":                 return "WATCHLIST"
    if pnl_pct < -15:                        return "CONSIDER STOP LOSS"
    return "HOLD"


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run(import_trades=False)
    print(f"Status:   {result['status']}")
    print(f"Holdings: {result['holdings_count']}")
    if result.get("error"):
        print(f"Error:    {result['error']}")
