"""
Forward Return Label Generator -- Phase 12C
Builds a historical training dataset from realized forward price returns,
breaking the circular dependency on Phase 8B rule-based labels.

For each of ~53 reference dates (bi-weekly, 2024-03-12 to 2026-04-06):
  - Computes 6 price-based features AT the reference date using TA-Lib
  - Computes realized forward returns 20D, 45D, 60D AFTER the reference date
  - Creates binary labels: is_up_10_20d, is_up_15_45d, is_up_20_60d

Output: data/intelligence/ml_forward_labels.csv

Run: py -3.11 -m engines.ml.label_generator
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
ADJ_DIR       = cfg.DATA_DIR / "NSE" / "adjusted_equity"
OUTPUT        = cfg.INTELLIGENCE_DIR / "ml_forward_labels.csv"

LOAD_SESSIONS = 790   # sessions loaded (~3 years); covers all windows below
WARMUP        = 200   # sessions needed before first ref date (DMA200 lookback)
FORWARD_MAX   = 60    # sessions after last ref date (longest forward window)
REF_STEP      = 10    # ref dates every 10 sessions (~bi-weekly)
FWD_WINDOWS   = [20, 45, 60]
MIN_VALID_BARS = 30   # minimum non-NaN bars a symbol needs at ref date

# Forward return thresholds for binary labels
THRESH_10_20D  = 0.10   # 10% in 20 sessions
THRESH_15_45D  = 0.15   # 15% in 45 sessions (primary training target)
THRESH_20_60D  = 0.20   # 20% in 60 sessions


# ---------------------------------------------------------------------------
# Feature computation for a single symbol (returns arrays aligned to dates)
# ---------------------------------------------------------------------------
def _compute_arrays(cl: np.ndarray, hi: np.ndarray, lo: np.ndarray, vol: np.ndarray):
    """Return per-session indicator arrays. NaN where insufficient history."""
    n = len(cl)
    nan = np.full(n, np.nan)
    try:
        rsi   = talib.RSI(cl, timeperiod=14)
        _, _, mh = talib.MACD(cl, fastperiod=12, slowperiod=26, signalperiod=9)
        bbu, bbm, bbl = talib.BBANDS(cl, timeperiod=20, nbdevup=2, nbdevdn=2)
        adx   = talib.ADX(hi, lo, cl, timeperiod=14)
        dma200 = talib.SMA(cl, timeperiod=200)
        vol20  = talib.SMA(vol, timeperiod=20)
    except Exception:
        return nan, nan, nan, nan, nan, nan

    # Bollinger %B
    band_width = bbu - bbl
    with np.errstate(invalid="ignore", divide="ignore"):
        bb_pct = np.where(band_width > 0, (cl - bbl) / band_width, np.nan)

    # % vs 200 DMA
    with np.errstate(invalid="ignore", divide="ignore"):
        vs_200 = np.where(dma200 > 0, (cl / dma200 - 1) * 100, np.nan)

    # 5D vol / 20D vol ratio (rolling 5D mean — forward-build via convolution)
    vol5 = np.full(n, np.nan)
    for i in range(4, n):
        window = vol[i - 4:i + 1]
        valid = window[~np.isnan(window)]
        if len(valid) >= 3:
            vol5[i] = np.mean(valid)

    with np.errstate(invalid="ignore", divide="ignore"):
        vol_ratio = np.where(vol20 > 0, vol5 / vol20, np.nan)

    return rsi, mh, bb_pct, adx, vs_200, vol_ratio


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
def run() -> dict:
    all_files = sorted(ADJ_DIR.glob("**/*.parquet"))
    if len(all_files) < LOAD_SESSIONS:
        return {"status": "ERROR", "error": f"Need {LOAD_SESSIONS} parquets, found {len(all_files)}"}

    files = all_files[-LOAD_SESSIONS:]
    logger.info("[LabelGen] Loading %d parquet files", len(files))

    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(
                f, columns=["SYMBOL", "CLOSE_PRICE", "HIGH_PRICE", "LOW_PRICE", "TTL_TRD_QNTY"]
            )
            date_str = f.stem.replace("bhavcopy_", "")
            df["_date"] = pd.to_datetime(date_str, format="%Y%m%d")
            dfs.append(df)
        except Exception as e:
            logger.debug("[LabelGen] Skip %s: %s", f.name, e)

    if not dfs:
        return {"status": "ERROR", "error": "No parquet files loaded"}

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined[combined["CLOSE_PRICE"] > 0]

    close_piv = combined.pivot_table(index="_date", columns="SYMBOL", values="CLOSE_PRICE",  aggfunc="last").sort_index()
    high_piv  = combined.pivot_table(index="_date", columns="SYMBOL", values="HIGH_PRICE",   aggfunc="last").sort_index()
    low_piv   = combined.pivot_table(index="_date", columns="SYMBOL", values="LOW_PRICE",    aggfunc="last").sort_index()
    vol_piv   = combined.pivot_table(index="_date", columns="SYMBOL", values="TTL_TRD_QNTY", aggfunc="last").sort_index()

    date_index = close_piv.index
    n_dates    = len(date_index)
    symbols    = close_piv.columns.tolist()

    # Reference date indices — valid if both warmup and forward window fit
    valid_end   = n_dates - FORWARD_MAX - 1
    ref_indices = list(range(WARMUP, valid_end + 1, REF_STEP))

    logger.info(
        "[LabelGen] %d reference dates: %s -> %s",
        len(ref_indices),
        date_index[ref_indices[0]].date(),
        date_index[ref_indices[-1]].date(),
    )
    logger.info("[LabelGen] Computing indicators for %d symbols...", len(symbols))

    records = []
    skipped_sym = 0

    for i, sym in enumerate(symbols):
        if i > 0 and i % 500 == 0:
            logger.info("[LabelGen] %d/%d symbols processed (%d rows so far)", i, len(symbols), len(records))

        cl  = close_piv[sym].values.astype(np.float64)
        hi  = high_piv[sym].values.astype(np.float64)  if sym in high_piv.columns  else cl.copy()
        lo  = low_piv[sym].values.astype(np.float64)   if sym in low_piv.columns   else cl.copy()
        vol = vol_piv[sym].values.astype(np.float64)   if sym in vol_piv.columns   else np.full_like(cl, np.nan)

        rsi, mh, bb_pct, adx, vs_200, vol_ratio = _compute_arrays(cl, hi, lo, vol)

        sym_added = 0
        for ref_idx in ref_indices:
            close_now = cl[ref_idx]
            if np.isnan(close_now) or close_now <= 0:
                continue

            valid_bars = int(np.sum(~np.isnan(cl[:ref_idx + 1])))
            if valid_bars < MIN_VALID_BARS:
                continue

            # Forward returns (use actual parquet close prices)
            fwd = {}
            for h in FWD_WINDOWS:
                fwd_idx = ref_idx + h
                p = cl[fwd_idx] if fwd_idx < n_dates else np.nan
                fwd[h] = (float(p) / float(close_now) - 1) if not np.isnan(p) and p > 0 else np.nan

            # Primary label (45D) must exist; secondary allowed to be NaN
            if np.isnan(fwd[45]):
                continue

            records.append({
                "symbol":    sym,
                "ref_date":  str(date_index[ref_idx].date()),
                # Features
                "rsi_14":    round(float(rsi[ref_idx]),  2)  if not np.isnan(rsi[ref_idx])      else None,
                "macd_hist": round(float(mh[ref_idx]),   4)  if not np.isnan(mh[ref_idx])       else None,
                "bb_pct_b":  round(float(np.clip(bb_pct[ref_idx], -0.5, 1.5)), 4) if not np.isnan(bb_pct[ref_idx]) else None,
                "adx_14":    round(float(adx[ref_idx]),  2)  if not np.isnan(adx[ref_idx])      else None,
                "vs_dma_200": round(float(np.clip(vs_200[ref_idx], -60, 100)), 2) if not np.isnan(vs_200[ref_idx]) else None,
                "vol_ratio": round(float(np.clip(vol_ratio[ref_idx], 0, 10)), 3) if not np.isnan(vol_ratio[ref_idx]) else None,
                # Realized returns
                "fwd_ret_20d": round(fwd[20], 4) if not np.isnan(fwd[20]) else None,
                "fwd_ret_45d": round(fwd[45], 4),
                "fwd_ret_60d": round(fwd[60], 4) if not np.isnan(fwd[60]) else None,
                # Binary labels
                "is_up_10_20d": int(fwd[20] >= THRESH_10_20D) if not np.isnan(fwd[20]) else None,
                "is_up_15_45d": int(fwd[45] >= THRESH_15_45D),
                "is_up_20_60d": int(fwd[60] >= THRESH_20_60D) if not np.isnan(fwd[60]) else None,
            })
            sym_added += 1

        if sym_added == 0:
            skipped_sym += 1

    if not records:
        return {"status": "ERROR", "error": "No records generated"}

    df_out = pd.DataFrame(records)

    # Summary stats
    pos_rate = df_out["is_up_15_45d"].mean()
    logger.info(
        "[LabelGen] %d rows, %d symbols, %d skipped | is_up_15_45d positive rate: %.1f%%",
        len(df_out), df_out["symbol"].nunique(), skipped_sym, pos_rate * 100
    )

    cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp.csv")
    df_out.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT))
    logger.info("[LabelGen] Saved -> %s", OUTPUT)

    return {
        "status":      "DONE",
        "rows":        len(df_out),
        "symbols":     df_out["symbol"].nunique(),
        "ref_dates":   len(ref_indices),
        "pos_rate_pct": round(pos_rate * 100, 1),
        "date_range":  f"{df_out['ref_date'].min()} to {df_out['ref_date'].max()}",
    }


if __name__ == "__main__":
    r = run()
    if r["status"] != "DONE":
        print("ERROR:", r.get("error"))
    else:
        print(f"Status:    {r['status']}")
        print(f"Rows:      {r['rows']:,}")
        print(f"Symbols:   {r['symbols']}")
        print(f"Ref dates: {r['ref_dates']}")
        print(f"Pos rate:  {r['pos_rate_pct']}%  (is_up_15_45d = 1)")
        print(f"Range:     {r['date_range']}")
        print(f"Output:    {OUTPUT}")
