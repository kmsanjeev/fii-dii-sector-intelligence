"""
Technical Pattern Feature Engine -- Phase 12B
Computes RSI(14), MACD(12,26,9), Bollinger %B (20,2), ADX(14) for every
EQ-series symbol from the adjusted bhavcopy parquets.

Output: data/intelligence/technical_pattern_features.csv

Run: py -3.11 -m engines.ml.technical_feature_engine
"""

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import talib

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ADJ_DIR  = cfg.DATA_DIR / "NSE" / "adjusted_equity"
OUTPUT   = cfg.INTELLIGENCE_DIR / "technical_pattern_features.csv"
LOOKBACK = 300   # trading sessions (~14 months); enough for all indicators
MIN_BARS = 50    # minimum sessions to compute any indicator

# RSI zone thresholds
RSI_OB = 70   # overbought
RSI_OS = 30   # oversold


# ---------------------------------------------------------------------------
# Helper: vectorised RSI zone encoding
#   OVERSOLD (potential buy)  -> 2
#   NEUTRAL                   -> 1
#   OVERBOUGHT (potential top)-> 0
# ---------------------------------------------------------------------------
def _rsi_zone(rsi: float) -> int:
    if np.isnan(rsi):
        return 1
    if rsi <= RSI_OS:
        return 2
    if rsi >= RSI_OB:
        return 0
    return 1


# ---------------------------------------------------------------------------
# Helper: MACD crossover/momentum encoding
#   Uses histogram direction (not just sign) to catch momentum shifts
#   BULLISH  -> 2  (hist > 0 AND hist rising)
#   BEARISH  -> 0  (hist < 0 AND hist falling)
#   NEUTRAL  -> 1  (everything else)
# ---------------------------------------------------------------------------
def _macd_signal_enc(hist: np.ndarray) -> int:
    if len(hist) < 2:
        return 1
    cur  = hist[-1]
    prev = hist[-2]
    if np.isnan(cur) or np.isnan(prev):
        return 1
    if cur > 0 and cur > prev:   # positive and growing
        return 2
    if cur < 0 and cur < prev:   # negative and worsening
        return 0
    return 1


# ---------------------------------------------------------------------------
# Core computation for a single symbol
# ---------------------------------------------------------------------------
def _compute_symbol(sym: str,
                    close_s: pd.Series,
                    high_s: pd.Series,
                    low_s: pd.Series) -> dict | None:
    cl = close_s.dropna().values.astype(np.float64)
    hi = high_s.reindex(close_s.index).dropna().values.astype(np.float64)
    lo = low_s.reindex(close_s.index).dropna().values.astype(np.float64)

    n = len(cl)
    if n < MIN_BARS:
        return None

    # Align hi/lo to same length as cl if needed
    n_hi = min(n, len(hi))
    n_lo = min(n, len(lo))
    cl_a = cl[:n_hi]
    hi_a = hi[:n_hi]
    lo_a = lo[:n_lo]
    n_use = min(len(cl_a), len(hi_a), len(lo_a))
    cl_a, hi_a, lo_a = cl_a[:n_use], hi_a[:n_use], lo_a[:n_use]

    if n_use < MIN_BARS:
        return None

    try:
        # RSI (14)
        rsi_arr = talib.RSI(cl_a, timeperiod=14)
        rsi_val = float(rsi_arr[-1]) if not np.isnan(rsi_arr[-1]) else np.nan

        # MACD (12, 26, 9)
        macd_line, macd_sig, macd_hist = talib.MACD(
            cl_a, fastperiod=12, slowperiod=26, signalperiod=9
        )
        # last 2 hist values for direction detection
        hist_tail = macd_hist[~np.isnan(macd_hist)][-2:]
        macd_hist_val = float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else np.nan

        # Bollinger Bands (20, 2)
        bb_upper, bb_mid, bb_lower = talib.BBANDS(
            cl_a, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        cu, cm, clo = bb_upper[-1], bb_mid[-1], bb_lower[-1]
        if not np.isnan(cu) and not np.isnan(clo) and (cu - clo) > 0:
            bb_pct_b   = float((cl_a[-1] - clo) / (cu - clo))
            bb_squeeze = float((cu - clo) / cm * 100) if cm > 0 else np.nan
        else:
            bb_pct_b   = np.nan
            bb_squeeze = np.nan

        # ADX (14) — needs high & low
        adx_arr = talib.ADX(hi_a, lo_a, cl_a, timeperiod=14)
        adx_val = float(adx_arr[-1]) if not np.isnan(adx_arr[-1]) else np.nan

    except Exception as e:
        logger.debug("[TechPattern] %s computation error: %s", sym, e)
        return None

    return {
        "symbol":         sym,
        "rsi_14":         round(rsi_val, 2) if not np.isnan(rsi_val) else None,
        "rsi_zone_enc":   _rsi_zone(rsi_val),
        "macd_hist":      round(macd_hist_val, 4) if not np.isnan(macd_hist_val) else None,
        "macd_signal_enc": _macd_signal_enc(hist_tail),
        "bb_pct_b":       round(max(-0.5, min(1.5, bb_pct_b)), 4) if not np.isnan(bb_pct_b) else None,
        "bb_squeeze":     round(bb_squeeze, 2) if bb_squeeze is not None and not np.isnan(bb_squeeze) else None,
        "adx_14":         round(adx_val, 2) if not np.isnan(adx_val) else None,
        "adx_trending":   int(adx_val >= 25) if not np.isnan(adx_val) else None,
    }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
def run() -> dict:
    all_files = sorted(ADJ_DIR.glob("**/*.parquet"))
    if len(all_files) < MIN_BARS:
        return {"status": "ERROR", "error": f"Only {len(all_files)} parquets in {ADJ_DIR}"}

    files = all_files[-LOOKBACK:]
    as_of_date = files[-1].stem.replace("bhavcopy_", "")
    try:
        as_of_date = pd.to_datetime(as_of_date, format="%Y%m%d").strftime("%Y-%m-%d")
    except Exception:
        pass

    logger.info("[TechPattern] Loading %d parquet files (as_of=%s)", len(files), as_of_date)

    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(
                f, columns=["SYMBOL", "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRICE"]
            )
            date_str = f.stem.replace("bhavcopy_", "")
            df["_date"] = pd.to_datetime(date_str, format="%Y%m%d")
            dfs.append(df)
        except Exception as e:
            logger.debug("[TechPattern] Skip %s: %s", f.name, e)

    if not dfs:
        return {"status": "ERROR", "error": "No parquet files loaded"}

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.dropna(subset=["SYMBOL", "CLOSE_PRICE"])
    combined = combined[combined["CLOSE_PRICE"] > 0]

    close_piv = combined.pivot_table(index="_date", columns="SYMBOL", values="CLOSE_PRICE", aggfunc="last").sort_index()
    high_piv  = combined.pivot_table(index="_date", columns="SYMBOL", values="HIGH_PRICE",  aggfunc="last").sort_index()
    low_piv   = combined.pivot_table(index="_date", columns="SYMBOL", values="LOW_PRICE",   aggfunc="last").sort_index()

    symbols = close_piv.columns.tolist()
    logger.info("[TechPattern] Computing indicators for %d symbols", len(symbols))

    records = []
    skipped = 0
    for sym in symbols:
        cl = close_piv[sym]
        hi = high_piv[sym]  if sym in high_piv.columns  else pd.Series(dtype=float)
        lo = low_piv[sym]   if sym in low_piv.columns   else pd.Series(dtype=float)

        row = _compute_symbol(sym, cl, hi, lo)
        if row is None:
            skipped += 1
            continue
        row["as_of_date"] = as_of_date
        records.append(row)

    if not records:
        return {"status": "ERROR", "error": "No indicators computed"}

    df_out = pd.DataFrame(records)
    cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp.csv")
    df_out.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT))

    logger.info(
        "[TechPattern] Saved %d symbols (%d skipped) to %s",
        len(df_out), skipped, OUTPUT.name
    )
    return {
        "status":     "DONE",
        "symbols":    len(df_out),
        "skipped":    skipped,
        "as_of_date": as_of_date,
    }


if __name__ == "__main__":
    r = run()
    print(f"Status:   {r['status']}")
    if r.get("error"):
        print(f"Error:    {r['error']}")
    else:
        print(f"Symbols:  {r['symbols']} computed, {r['skipped']} skipped")
        print(f"As of:    {r['as_of_date']}")
        print(f"Output:   {OUTPUT}")
