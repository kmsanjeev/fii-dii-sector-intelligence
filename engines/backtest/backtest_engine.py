"""
Backtesting Framework -- Phase 21

Three strategies:
  1. Label Screen    -- current EMERGING/WATCHLIST stocks tested over past N days
  2. Momentum Screen -- scan historical price data for momentum entry signals
  3. Portfolio Trades -- forward returns from user's actual buy dates

Uses Phase 17 symbol resolution for renamed companies.
Price data sourced from per-symbol parquet cache (data/NSE/nsecache/stock_history/).

Run standalone:
    py -3.11 -m engines.backtest.backtest_engine
"""

import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.backtest.metrics import compute_metrics

logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

BACKTEST_DIR  = cfg.DATA_DIR / "backtest"
RESULTS_CSV   = BACKTEST_DIR / "last_results.csv"
SUMMARY_JSON  = BACKTEST_DIR / "summary.json"

BULL_RUN_CSV  = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
PORTFOLIO_CSV = cfg.DATA_DIR / "portfolio" / "transactions.csv"

HORIZONS = [30, 60, 90, 180, 365]


# ── Price utilities ───────────────────────────────────────────────────────────

def _load_price_series(symbol: str) -> Optional[pd.Series]:
    """
    Load close price series from parquet cache, resolving symbol renames via Phase 17.
    Returns pd.Series indexed by Timestamp, sorted ascending; None if unavailable.
    """
    try:
        from engines.foundation.symbol_change_engine import resolve_current_symbol
        resolved = resolve_current_symbol(symbol)
    except Exception:
        resolved = symbol

    for sym in (resolved, symbol):
        parquet = cfg.STOCK_HISTORY_CACHE / f"{sym}.parquet"
        if parquet.exists():
            try:
                df = pd.read_parquet(parquet, columns=["date", "close"])
                df["date"]  = pd.to_datetime(df["date"], errors="coerce")
                df["close"] = pd.to_numeric(df["close"], errors="coerce")
                df = df.dropna(subset=["date", "close"]).sort_values("date").set_index("date")
                df = df[df["close"] > 0]
                if not df.empty:
                    return df["close"]
            except Exception as exc:
                logger.debug("[Backtest] Parquet load failed %s: %s", sym, exc)
    return None


def _price_on_or_before(series: pd.Series, date: pd.Timestamp) -> Optional[float]:
    """Closest available close price on or before `date`."""
    mask = series.index <= date
    if not mask.any():
        return None
    return float(series[mask].iloc[-1])


def _trade_row(symbol: str, sector: str, entry_date: pd.Timestamp,
               series: pd.Series, strategy: str,
               label: str = "", score: float = 0.0,
               entry_price: Optional[float] = None) -> dict:
    """Build one trade result row with forward returns at all standard horizons."""
    ep = entry_price if (entry_price and entry_price > 0) else _price_on_or_before(series, entry_date)
    row: dict = {
        "symbol":       symbol,
        "sector":       sector,
        "entry_date":   entry_date.strftime("%Y-%m-%d"),
        "entry_price":  round(ep, 2) if ep else None,
        "label":        label,
        "bull_run_score": round(score, 1),
        "strategy":     strategy,
    }
    for h in HORIZONS:
        if ep and ep > 0:
            exit_dt    = entry_date + pd.Timedelta(days=h)
            exit_price = _price_on_or_before(series, exit_dt)
            row[f"ret_{h}d"] = (
                round((exit_price - ep) / ep * 100, 2) if exit_price else None
            )
        else:
            row[f"ret_{h}d"] = None
    return row


# ── Reference data ─────────────────────────────────────────────────────────────

def _load_bull_universe() -> pd.DataFrame:
    if not BULL_RUN_CSV.exists():
        return pd.DataFrame(columns=["symbol", "sector", "label", "bull_run_score"])
    df = pd.read_csv(
        BULL_RUN_CSV,
        usecols=["symbol", "sector", "label", "bull_run_score"],
        dtype=str,
    )
    df["symbol"]        = df["symbol"].str.strip().str.upper()
    df["bull_run_score"] = pd.to_numeric(df["bull_run_score"], errors="coerce").fillna(0)
    return df.drop_duplicates(subset=["symbol"])


# ── Strategy 1: Label Screen ──────────────────────────────────────────────────

def run_label_screen(label: str = "EMERGING", lookback_days: int = 180) -> dict:
    """
    For each current {label} stock: set entry_date = today - lookback_days,
    compute forward returns at standard horizons.

    Validates label quality: were the stocks the system currently labels as
    EMERGING actually rising over the last N days?
    """
    logger.info("[Backtest/Label] label=%s lookback=%dd", label, lookback_days)
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

    universe = _load_bull_universe()
    subset   = universe[universe["label"] == label].reset_index(drop=True)
    if subset.empty:
        return {"error": f"No symbols found with label={label}"}

    today      = pd.Timestamp.now().normalize()
    entry_date = today - pd.Timedelta(days=lookback_days)
    trades: list[dict] = []

    for _, row in subset.iterrows():
        series = _load_price_series(str(row["symbol"]))
        if series is None or len(series) < 5:
            continue
        t = _trade_row(
            symbol     = str(row["symbol"]),
            sector     = str(row.get("sector") or ""),
            entry_date = entry_date,
            series     = series,
            strategy   = f"LABEL_SCREEN_{label}",
            label      = label,
            score      = float(row.get("bull_run_score") or 0),
        )
        if t["entry_price"]:
            trades.append(t)

    if not trades:
        return {"error": "No price data available for any symbol in this label"}

    # Use the closest HORIZONS column to lookback_days as the primary metric
    primary = min(HORIZONS, key=lambda h: abs(h - lookback_days))
    metrics  = compute_metrics(trades, ret_col=f"ret_{primary}d")
    _save(trades, {"strategy": f"LABEL_SCREEN_{label}",
                   "params": {"label": label, "lookback_days": lookback_days}, **metrics})
    logger.info("[Backtest/Label] %d trades, hit_rate=%.1f%%", len(trades), metrics["hit_rate"])
    return {"trades": trades, "metrics": metrics, "strategy": f"LABEL_SCREEN_{label}"}


# ── Strategy 2: Momentum Screen ───────────────────────────────────────────────

def _scan_symbol_momentum(row: pd.Series, start_dt: pd.Timestamp, end_dt: pd.Timestamp,
                          min_ret_30d: float, min_ret_365d: float) -> list[dict]:
    """Per-symbol scan for momentum signals. Runs in thread pool."""
    series = _load_price_series(str(row["symbol"]))
    if series is None or len(series) < 400:
        return []

    # Restrict to window + enough lookback for 365d return
    lookback_start = start_dt - pd.Timedelta(days=400)
    window_full = series[series.index >= lookback_start]
    if len(window_full) < 300:
        return []

    # Vectorised rolling returns (trading days)
    ret_30  = window_full.pct_change(periods=30)  * 100
    ret_365 = window_full.pct_change(periods=252) * 100

    aligned = pd.DataFrame({
        "close": window_full,
        "ret_30": ret_30,
        "ret_365": ret_365,
    }).dropna()

    # Only consider signals within [start_dt, end_dt]
    in_window = aligned[(aligned.index >= start_dt) & (aligned.index <= end_dt)]
    if in_window.empty:
        return []

    signal_dates = in_window.index[
        (in_window["ret_30"] >= min_ret_30d) & (in_window["ret_365"] >= min_ret_365d)
    ]
    if len(signal_dates) == 0:
        return []

    trades: list[dict] = []
    last_entry = pd.Timestamp("1970-01-01")

    for ed in signal_dates:
        # At most one signal per symbol per 45-day window (avoids clustered duplicates)
        if (ed - last_entry).days < 45:
            continue
        last_entry = ed
        t = _trade_row(
            symbol     = str(row["symbol"]),
            sector     = str(row.get("sector") or ""),
            entry_date = ed,
            series     = series,
            strategy   = "MOMENTUM_SCREEN",
            label      = str(row.get("label") or ""),
            score      = float(row.get("bull_run_score") or 0),
        )
        if t["entry_price"]:
            trades.append(t)

    return trades


def run_momentum_screen(
    min_ret_30d:  float = 15.0,
    min_ret_365d: float = 30.0,
    hold_days:    int   = 60,
    start_date:   str   = "",
    end_date:     str   = "",
    max_symbols:  int   = 1000,
) -> dict:
    """
    Scan the intelligence universe for momentum entry signals in historical data.
    Entry when ret_30d (30 trading days) AND ret_365d (252 trading days) cross thresholds.
    Deduplicates: at most one signal per symbol per 45-day period.
    """
    logger.info(
        "[Backtest/Momentum] ret30>=%.0f%% ret365>=%.0f%% hold=%dd max=%d",
        min_ret_30d, min_ret_365d, hold_days, max_symbols,
    )
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

    today    = pd.Timestamp.now().normalize()
    end_dt   = pd.Timestamp(end_date)   if end_date   else today - pd.Timedelta(days=hold_days + 5)
    start_dt = pd.Timestamp(start_date) if start_date else end_dt - pd.Timedelta(days=365)

    if start_dt >= end_dt:
        return {"error": "start_date must be before end_date"}

    universe = _load_bull_universe()
    if len(universe) > max_symbols:
        # Prioritise EMERGING + WATCHLIST over other labels
        priority = universe[universe["label"].isin(["EMERGING", "STRONG_CANDIDATE", "WATCHLIST"])]
        others   = universe[~universe["label"].isin(["EMERGING", "STRONG_CANDIDATE", "WATCHLIST"])]
        n_others = max(0, max_symbols - len(priority))
        sample   = others.sample(min(n_others, len(others)), random_state=42)
        universe = pd.concat([priority, sample]).reset_index(drop=True)

    all_trades: list[dict] = []
    workers = min(cfg.MAX_CONCURRENCY, 6)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(
                _scan_symbol_momentum,
                row, start_dt, end_dt, min_ret_30d, min_ret_365d,
            ): str(row["symbol"])
            for _, row in universe.iterrows()
        }
        for fut in as_completed(futs):
            try:
                all_trades.extend(fut.result())
            except Exception as exc:
                logger.debug("[Backtest/Momentum] %s error: %s", futs[fut], exc)

    if not all_trades:
        return {"error": "No momentum signals found in the specified window"}

    all_trades.sort(key=lambda t: t["entry_date"])

    # Primary metric: nearest HORIZONS to hold_days
    primary = min(HORIZONS, key=lambda h: abs(h - hold_days))
    metrics  = compute_metrics(all_trades, ret_col=f"ret_{primary}d")
    params = {
        "min_ret_30d": min_ret_30d, "min_ret_365d": min_ret_365d,
        "hold_days": hold_days, "start_date": str(start_dt.date()),
        "end_date": str(end_dt.date()), "max_symbols": max_symbols,
    }
    _save(all_trades, {"strategy": "MOMENTUM_SCREEN", "params": params, **metrics})
    logger.info("[Backtest/Momentum] %d signals, hit_rate=%.1f%%",
                len(all_trades), metrics["hit_rate"])
    return {"trades": all_trades, "metrics": metrics, "strategy": "MOMENTUM_SCREEN"}


# ── Strategy 3: Portfolio Trades ──────────────────────────────────────────────

def run_portfolio_trades() -> dict:
    """
    For each BUY in transactions.csv: compute forward returns at standard horizons
    using the user's actual buy price as entry.
    """
    logger.info("[Backtest/Portfolio] Portfolio trade replay")
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

    if not PORTFOLIO_CSV.exists() or PORTFOLIO_CSV.stat().st_size < 50:
        return {"error": "No portfolio transactions found. Add trades on the Portfolio page first."}

    txns = pd.read_csv(PORTFOLIO_CSV, dtype=str)
    txns.columns = [c.strip() for c in txns.columns]
    txns["date"]   = pd.to_datetime(txns["date"],  errors="coerce")
    txns["qty"]    = pd.to_numeric(txns["qty"],    errors="coerce")
    txns["price"]  = pd.to_numeric(txns["price"],  errors="coerce")
    txns["symbol"] = txns["symbol"].str.strip().str.upper()
    txns["action"] = txns["action"].str.strip().str.upper()
    buys = txns[txns["action"] == "BUY"].dropna(subset=["date", "symbol", "price"])

    if buys.empty:
        return {"error": "No BUY transactions found in portfolio."}

    universe = _load_bull_universe()
    sym_meta = universe.set_index("symbol")[["sector", "label", "bull_run_score"]].to_dict("index")

    trades: list[dict] = []
    for _, row in buys.iterrows():
        sym    = str(row["symbol"])
        series = _load_price_series(sym)
        if series is None:
            continue
        meta = sym_meta.get(sym, {})
        t = _trade_row(
            symbol      = sym,
            sector      = str(meta.get("sector") or ""),
            entry_date  = row["date"],
            series      = series,
            strategy    = "PORTFOLIO_TRADES",
            label       = str(meta.get("label") or ""),
            score       = float(meta.get("bull_run_score") or 0),
            entry_price = float(row["price"]),
        )
        trades.append(t)

    if not trades:
        return {"error": "Could not load price data for any portfolio symbol."}

    metrics = compute_metrics(trades, ret_col="ret_90d")
    _save(trades, {"strategy": "PORTFOLIO_TRADES", "params": {}, **metrics})
    return {"trades": trades, "metrics": metrics, "strategy": "PORTFOLIO_TRADES"}


# ── Persistence ───────────────────────────────────────────────────────────────

def _save(trades: list[dict], summary: dict) -> None:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    df  = pd.DataFrame(trades)
    tmp = RESULTS_CSV.with_suffix(".tmp.csv")
    df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(RESULTS_CSV))

    summary["as_of"]       = pd.Timestamp.now().isoformat()
    summary["trade_count"] = len(trades)
    tmp_j = SUMMARY_JSON.with_suffix(".tmp.json")
    with open(tmp_j, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    shutil.move(str(tmp_j), str(SUMMARY_JSON))


def load_results() -> tuple[list[dict], dict]:
    """Load last backtest results and summary."""
    trades:  list[dict] = []
    summary: dict       = {}
    if RESULTS_CSV.exists():
        df = pd.read_csv(RESULTS_CSV)
        trades = df.where(pd.notnull(df), None).to_dict(orient="records")
    if SUMMARY_JSON.exists():
        with open(SUMMARY_JSON, encoding="utf-8") as f:
            summary = json.load(f)
    return trades, summary


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[Backtest] Running Label Screen: EMERGING, 180d lookback")
    result = run_label_screen("EMERGING", lookback_days=180)
    m = result.get("metrics", {})
    n = len(result.get("trades", []))
    print(f"  Trades: {n}")
    print(f"  Hit rate:   {m.get('hit_rate')}%")
    print(f"  Avg return: {m.get('avg_return')}%")
    print(f"  Sharpe:     {m.get('sharpe')}")
    if result.get("error"):
        print(f"  Error: {result['error']}")
