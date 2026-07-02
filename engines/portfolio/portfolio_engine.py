"""
Portfolio Engine -- Phase 20
Tracks user holdings and overlays the full intelligence stack on each position.

Managed (append-only):
  data/portfolio/transactions.csv

Derived (rebuilt on every transaction + daily pipeline):
  data/portfolio/positions.csv
  data/portfolio/portfolio_intelligence.csv
"""

import shutil
from datetime import date
from pathlib import Path
import sys

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

PORTFOLIO_DIR    = cfg.DATA_DIR / "portfolio"
TRANSACTIONS_CSV = PORTFOLIO_DIR / "transactions.csv"
POSITIONS_CSV    = PORTFOLIO_DIR / "positions.csv"
INTEL_CSV        = PORTFOLIO_DIR / "portfolio_intelligence.csv"

# Intelligence sources (read-only -- G-D-01)
BULL_RUN_CSV   = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
ML_SCORES_CSV  = cfg.INTELLIGENCE_DIR / "ml_bull_run_scores.csv"
ANN_CSV        = cfg.INTELLIGENCE_DIR / "company_announcements.csv"
CONFIDENCE_CSV = cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
ROTATION_CSV   = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"

TRANSACTION_COLS = ["date", "symbol", "action", "qty", "price", "notes"]
POSITION_COLS    = ["symbol", "qty", "avg_cost", "invested", "first_bought", "last_action_date"]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _atomic_save(df: pd.DataFrame, path: Path) -> None:
    tmp = path.with_suffix(".tmp.csv")
    df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(path))


def _ensure_dir() -> None:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    if not TRANSACTIONS_CSV.exists():
        pd.DataFrame(columns=TRANSACTION_COLS).to_csv(TRANSACTIONS_CSV, index=False)


# ── Transaction I/O ───────────────────────────────────────────────────────────

def load_transactions() -> pd.DataFrame:
    _ensure_dir()
    df = pd.read_csv(TRANSACTIONS_CSV, dtype=str)
    if df.empty:
        return df
    df["qty"]    = pd.to_numeric(df["qty"],   errors="coerce").fillna(0)
    df["price"]  = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["date"]   = pd.to_datetime(df["date"],  errors="coerce")
    df["symbol"] = df["symbol"].str.strip().str.upper()
    df["action"] = df["action"].str.strip().str.upper()
    return df.dropna(subset=["date", "symbol"]).sort_values("date")


def add_transaction(symbol: str, action: str, qty: float, price: float,
                    txn_date: str = "", notes: str = "") -> bool:
    """Append a transaction then rebuild positions and intelligence."""
    _ensure_dir()
    action = action.upper()
    if action not in ("BUY", "SELL"):
        raise ValueError(f"action must be BUY or SELL, got: {action!r}")
    if qty <= 0:
        raise ValueError("qty must be positive")
    if price <= 0:
        raise ValueError("price must be positive")

    dt = txn_date or date.today().isoformat()
    row = pd.DataFrame([{
        "date":   dt,
        "symbol": symbol.upper().strip(),
        "action": action,
        "qty":    qty,
        "price":  price,
        "notes":  notes,
    }])
    row.to_csv(TRANSACTIONS_CSV, mode="a", header=False, index=False)
    logger.info("[Portfolio] %s %s x%s @ %.2f", action, symbol.upper(), qty, price)
    rebuild()
    return True


def delete_symbol(symbol: str) -> int:
    """Remove all transactions for a symbol; returns rows deleted."""
    txns   = load_transactions()
    before = len(txns)
    keep   = txns[txns["symbol"] != symbol.upper().strip()]
    _atomic_save(keep, TRANSACTIONS_CSV)
    removed = before - len(keep)
    rebuild()
    return removed


# ── Position computation (average-cost method) ────────────────────────────────

def compute_positions(txns: pd.DataFrame) -> pd.DataFrame:
    if txns.empty:
        return pd.DataFrame(columns=POSITION_COLS)

    state: dict[str, dict] = {}

    for _, row in txns.sort_values("date").iterrows():
        sym    = row["symbol"]
        action = row["action"]
        qty    = float(row["qty"])
        price  = float(row["price"])
        dt     = row["date"]

        if sym not in state:
            state[sym] = {
                "symbol":           sym,
                "qty":              0.0,
                "avg_cost":         0.0,
                "invested":         0.0,
                "first_bought":     dt,
                "last_action_date": dt,
            }

        p = state[sym]

        if action == "BUY":
            total_cost = p["qty"] * p["avg_cost"] + qty * price
            p["qty"]  += qty
            p["avg_cost"] = total_cost / p["qty"] if p["qty"] > 0 else 0.0
        elif action == "SELL":
            p["qty"] = max(0.0, p["qty"] - qty)

        p["invested"]         = p["qty"] * p["avg_cost"]
        p["last_action_date"] = dt

    rows = [v for v in state.values() if v["qty"] > 0.0001]
    if not rows:
        return pd.DataFrame(columns=POSITION_COLS)

    df = pd.DataFrame(rows)
    df["first_bought"]     = pd.to_datetime(df["first_bought"]).dt.strftime("%Y-%m-%d")
    df["last_action_date"] = pd.to_datetime(df["last_action_date"]).dt.strftime("%Y-%m-%d")
    return df.round({"avg_cost": 4, "invested": 2})


# ── Pricing ───────────────────────────────────────────────────────────────────

def _get_ltp(symbol: str) -> float | None:
    """Latest closing price from per-symbol parquet cache. Returns None if unavailable."""
    parquet = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
    if not parquet.exists():
        return None
    try:
        df = pd.read_parquet(parquet, columns=["date", "close"])
        if df.empty:
            return None
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        latest = df.dropna(subset=["date"]).sort_values("date").iloc[-1]
        return float(latest["close"])
    except Exception:
        return None


# ── Intelligence overlay ──────────────────────────────────────────────────────

def overlay_intelligence(positions: pd.DataFrame) -> pd.DataFrame:
    if positions.empty:
        return positions.copy()

    df = positions.copy()
    for col in ("qty", "avg_cost", "invested"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Current prices
    ltps            = {sym: _get_ltp(sym) for sym in df["symbol"]}
    df["ltp"]           = df["symbol"].map(ltps)
    df["current_value"] = df["qty"] * df["ltp"]
    df["unrealized_pnl"] = df["current_value"] - df["invested"]
    df["unrealized_pnl_pct"] = (
        (df["unrealized_pnl"] / df["invested"].replace(0, np.nan)) * 100
    ).round(2)

    # Bull run probability
    if BULL_RUN_CSV.exists():
        bull = pd.read_csv(BULL_RUN_CSV,
                           usecols=["symbol", "sector", "label", "bull_run_score", "as_of_date"])
        bull["symbol"] = bull["symbol"].str.strip().str.upper()
        df = df.merge(
            bull.rename(columns={"label": "bull_run_label", "as_of_date": "intel_as_of"}),
            on="symbol", how="left",
        )
    else:
        df[["sector", "bull_run_label", "bull_run_score", "intel_as_of"]] = None

    # ML scores
    if ML_SCORES_CSV.exists():
        ml = pd.read_csv(ML_SCORES_CSV, usecols=["symbol", "ml_bull_run_score", "ml_label"])
        ml["symbol"] = ml["symbol"].str.strip().str.upper()
        df = df.merge(ml, on="symbol", how="left")
    else:
        df[["ml_bull_run_score", "ml_label"]] = None

    # Announcement score (30-day rolling sum of signal_score)
    if ANN_CSV.exists():
        ann = pd.read_csv(ANN_CSV, usecols=["symbol", "date", "signal_score"], dtype=str)
        ann["date"]         = pd.to_datetime(ann["date"], errors="coerce")
        ann["signal_score"] = pd.to_numeric(ann["signal_score"], errors="coerce").fillna(0)
        ann["symbol"]       = ann["symbol"].str.strip().str.upper()
        cut30 = pd.Timestamp.now() - pd.Timedelta(days=30)
        s30 = (ann[ann["date"] >= cut30]
               .groupby("symbol")["signal_score"].sum()
               .rename("ann_score_30d").reset_index())
        df = df.merge(s30, on="symbol", how="left")
    else:
        df["ann_score_30d"] = None

    # Corporate confidence
    if CONFIDENCE_CSV.exists():
        conf = pd.read_csv(CONFIDENCE_CSV, usecols=["symbol", "confidence_score_12m"])
        conf["symbol"] = conf["symbol"].str.strip().str.upper()
        df = df.merge(conf.rename(columns={"confidence_score_12m": "corp_confidence"}),
                      on="symbol", how="left")
    else:
        df["corp_confidence"] = None

    # Sector rotation signal
    if ROTATION_CSV.exists():
        rot = pd.read_csv(ROTATION_CSV, usecols=["sector", "rotation_signal"])
        df = df.merge(rot, on="sector", how="left")
    else:
        df["rotation_signal"] = None

    # Key signal (one-liner for UI)
    df["key_signal"] = df.apply(_key_signal, axis=1)

    # Round numeric outputs
    for col in ["ltp", "current_value", "unrealized_pnl", "avg_cost", "invested",
                "bull_run_score", "ml_bull_run_score", "ann_score_30d", "corp_confidence"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    return df


def _key_signal(row) -> str:
    label   = str(row.get("bull_run_label") or "")
    rot     = str(row.get("rotation_signal") or "")
    ann     = float(row.get("ann_score_30d")      or 0)
    pnl_pct = float(row.get("unrealized_pnl_pct") or 0)

    if label == "STRONG_CANDIDATE":              return "STRONG BUY SIGNAL"
    if label == "AVOID":                         return "REVIEW POSITION"
    if label == "EMERGING" and ann > 100:        return "MOMENTUM BUILDING"
    if rot   == "EARLY_ROTATION":                return "SECTOR ROTATING IN"
    if label == "EMERGING":                      return "ACCUMULATION"
    if label == "WATCHLIST":                     return "WATCHLIST"
    if pnl_pct < -15:                            return "CONSIDER STOP LOSS"
    return "HOLD"


# ── Analytics ─────────────────────────────────────────────────────────────────

def compute_analytics(intel: pd.DataFrame) -> dict:
    if intel.empty:
        return {
            "total_invested": 0, "current_value": 0,
            "unrealized_pnl": 0, "unrealized_pnl_pct": 0,
            "num_positions": 0, "avg_bull_run_score": 0,
            "sector_concentration": [], "label_distribution": {},
        }

    total_invested = float(intel["invested"].fillna(0).sum())
    current_value  = float(
        intel["current_value"].fillna(intel["invested"]).fillna(0).sum()
    )
    unrealized_pnl = current_value - total_invested
    pnl_pct        = (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0.0
    avg_score      = float(
        pd.to_numeric(intel.get("bull_run_score"), errors="coerce").dropna().mean()
        if "bull_run_score" in intel.columns else 0
    )

    cv = current_value or 1
    sector_grp = (
        intel.assign(cv=intel["current_value"].fillna(intel["invested"]).fillna(0))
             .groupby("sector", dropna=False)["cv"]
             .sum()
             .sort_values(ascending=False)
    )
    sector_conc = [
        {"sector": str(s), "value": round(float(v), 2), "pct": round(float(v / cv * 100), 1)}
        for s, v in sector_grp.items()
    ]

    label_dist = (
        intel["bull_run_label"].value_counts().to_dict()
        if "bull_run_label" in intel.columns else {}
    )

    return {
        "total_invested":       round(total_invested, 2),
        "current_value":        round(current_value, 2),
        "unrealized_pnl":       round(unrealized_pnl, 2),
        "unrealized_pnl_pct":   round(pnl_pct, 2),
        "num_positions":        len(intel),
        "avg_bull_run_score":   round(avg_score, 1),
        "sector_concentration": sector_conc,
        "label_distribution":   label_dist,
    }


# ── Rebuild ───────────────────────────────────────────────────────────────────

def rebuild() -> bool:
    """Full rebuild: transactions -> positions -> intelligence. Called after every mutation."""
    _ensure_dir()
    txns      = load_transactions()
    positions = compute_positions(txns)
    _atomic_save(positions, POSITIONS_CSV)
    intel = overlay_intelligence(positions)
    _atomic_save(intel, INTEL_CSV)
    logger.info("[Portfolio] Rebuilt: %d active positions", len(positions))
    return True


def load_intelligence() -> pd.DataFrame:
    if not INTEL_CSV.exists():
        rebuild()
    return pd.read_csv(INTEL_CSV) if INTEL_CSV.exists() else pd.DataFrame()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    rebuild()
    df = load_intelligence()
    print(f"Portfolio: {len(df)} positions")
    if not df.empty:
        cols = [c for c in [
            "symbol", "qty", "avg_cost", "ltp", "unrealized_pnl_pct",
            "bull_run_label", "key_signal",
        ] if c in df.columns]
        print(df[cols].to_string(index=False))
