"""
Broker Sync Engine -- Phase 22

Orchestrates:
  1. Load adapter (Dhan API or CSV fallback)
  2. Fetch holdings + optional trade history
  3. Persist to broker_holdings.csv
  4. Merge trade history into portfolio transactions.csv (with dedup)
  5. Trigger Phase 20 portfolio rebuild

Credentials live in data/portfolio/broker_auth.json (gitignored, never in .env).
Run:  py -3.11 -m engines.broker.sync_engine
"""

import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.broker.base import BrokerAdapter, Holding, Trade

logger = get_logger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

PORTFOLIO_DIR    = cfg.DATA_DIR / "portfolio"
BROKER_HOLDINGS  = PORTFOLIO_DIR / "broker_holdings.csv"
TRANSACTIONS_CSV = PORTFOLIO_DIR / "transactions.csv"
BROKER_AUTH      = PORTFOLIO_DIR / "broker_auth.json"     # gitignored via data/**/*.json
SYNC_LOG         = PORTFOLIO_DIR / "broker_sync_log.csv"

HOLDINGS_COLS = [
    "symbol", "exchange", "isin", "qty", "avg_cost",
    "ltp", "current_value", "pnl", "pnl_pct", "last_synced",
]

TRANSACTION_COLS = ["date", "symbol", "action", "qty", "price", "notes"]


# ── Auth helpers ───────────────────────────────────────────────────────────────

def save_credentials(broker: str, client_id: str, access_token: str) -> None:
    """Persist credentials to broker_auth.json (never committed)."""
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "broker":       broker,
        "client_id":    client_id,
        "access_token": access_token,
        "set_at":       datetime.now().isoformat(),
    }
    tmp = BROKER_AUTH.with_suffix(".tmp.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    shutil.move(str(tmp), str(BROKER_AUTH))
    logger.info("[Broker] Credentials saved for broker=%s client=%s****",
                broker, client_id[:4])


def load_credentials() -> Optional[dict]:
    if not BROKER_AUTH.exists():
        return None
    try:
        with open(BROKER_AUTH, encoding="utf-8") as f:
            return json.load(f)
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
        "client_id":      (creds.get("client_id", "")[:4] + "****") if creds else None,
        "credentials_set_at": creds.get("set_at") if creds else None,
        "holdings_count": holdings_count,
        "last_synced":    last_synced,
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

    if label == "STRONG_CANDIDATE":          return "STRONG BUY"
    if label == "AVOID":                     return "REVIEW POSITION"
    if label == "EMERGING" and ann > 60:     return "MOMENTUM BUILDING"
    if rot   == "EARLY_ROTATION":            return "SECTOR ROTATING IN"
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
