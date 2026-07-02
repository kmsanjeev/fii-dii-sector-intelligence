"""
Technical Indicators Engine
Computes 52W High/Low, 20/50/200 DMA, trend signal from daily adjusted parquets.
Output: data/intelligence/technical_indicators.csv

Run: py -3.11 -m engines.intelligence.technical_engine
"""

import shutil
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT  = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"
ADJ_DIR = cfg.DATA_DIR / "NSE" / "adjusted_equity"
LOOKBACK = 252  # trading sessions ~ 1 year


def _trend_signal(close: float, d20, d50, d200) -> str:
    if d200 is None:
        return "INSUFFICIENT_DATA"
    above_200 = close > d200
    above_50  = d50  is not None and close > d50
    above_20  = d20  is not None and close > d20
    if above_200 and above_50 and above_20:
        return "STRONG_UPTREND"
    if above_200 and above_50:
        return "UPTREND"
    if above_200:
        return "CONSOLIDATING"
    return "DOWNTREND"


def run() -> dict:
    all_files = sorted(ADJ_DIR.glob("**/*.parquet"))
    if len(all_files) < 20:
        return {"status": "ERROR", "error": f"Only {len(all_files)} parquet files found"}

    files = all_files[-LOOKBACK:]
    logger.info("[Technical] Reading %d parquet files for indicators", len(files))

    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(
                f, columns=["SYMBOL", "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRICE", "TTL_TRD_QNTY"]
            )
            date_str = f.stem.replace("bhavcopy_", "")
            df["_date"] = pd.to_datetime(date_str, format="%Y%m%d")
            dfs.append(df)
        except Exception as exc:
            logger.warning("[Technical] Skip %s: %s", f.name, exc)

    if not dfs:
        return {"status": "ERROR", "error": "No parquet files readable"}

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.dropna(subset=["SYMBOL", "CLOSE_PRICE"])
    combined = combined[combined["CLOSE_PRICE"] > 0]

    # Pivot to (date, symbol) matrices
    close_piv = combined.pivot_table(index="_date", columns="SYMBOL", values="CLOSE_PRICE",  aggfunc="last").sort_index()
    high_piv  = combined.pivot_table(index="_date", columns="SYMBOL", values="HIGH_PRICE",   aggfunc="last").sort_index()
    low_piv   = combined.pivot_table(index="_date", columns="SYMBOL", values="LOW_PRICE",    aggfunc="last").sort_index()
    vol_piv   = combined.pivot_table(index="_date", columns="SYMBOL", values="TTL_TRD_QNTY", aggfunc="last").sort_index()

    as_of_date = str(close_piv.index[-1].date())
    symbols = close_piv.columns.tolist()
    logger.info("[Technical] Computing for %d symbols, as_of=%s", len(symbols), as_of_date)

    records = []
    for sym in symbols:
        cl = close_piv[sym].dropna()
        hi = high_piv[sym].dropna()
        lo = low_piv[sym].dropna()
        vo = vol_piv[sym].dropna() if sym in vol_piv.columns else pd.Series(dtype=float)

        if len(cl) < 5:
            continue

        close_now = float(cl.iloc[-1])
        high_52w  = float(hi.max()) if len(hi) > 0 else close_now
        low_52w   = float(lo.min()) if len(lo) > 0 else close_now

        prox_52w_high = round((close_now - high_52w) / high_52w * 100, 2) if high_52w > 0 else 0.0
        prox_52w_low  = round((close_now - low_52w)  / low_52w  * 100, 2) if low_52w  > 0 else 0.0

        dma_20  = round(float(cl.tail(20).mean()),  2) if len(cl) >= 20  else None
        dma_50  = round(float(cl.tail(50).mean()),  2) if len(cl) >= 50  else None
        dma_200 = round(float(cl.tail(200).mean()), 2) if len(cl) >= 200 else None

        vs_dma_20  = round((close_now - dma_20)  / dma_20  * 100, 2) if dma_20  else None
        vs_dma_50  = round((close_now - dma_50)  / dma_50  * 100, 2) if dma_50  else None
        vs_dma_200 = round((close_now - dma_200) / dma_200 * 100, 2) if dma_200 else None

        trend = _trend_signal(close_now, dma_20, dma_50, dma_200)
        vol_20d_avg = round(float(vo.tail(20).mean()), 0) if len(vo) >= 5 else None

        records.append({
            "symbol":        sym,
            "close_now":     round(close_now, 2),
            "high_52w":      round(high_52w, 2),
            "low_52w":       round(low_52w, 2),
            "prox_52w_high": prox_52w_high,
            "prox_52w_low":  prox_52w_low,
            "dma_20":        dma_20,
            "dma_50":        dma_50,
            "dma_200":       dma_200,
            "vs_dma_20":     vs_dma_20,
            "vs_dma_50":     vs_dma_50,
            "vs_dma_200":    vs_dma_200,
            "trend_signal":  trend,
            "vol_20d_avg":   vol_20d_avg,
            "as_of_date":    as_of_date,
        })

    if not records:
        return {"status": "ERROR", "error": "No indicators computed"}

    df_out = pd.DataFrame(records)
    cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp.csv")
    df_out.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT))
    logger.info("[Technical] Saved %d rows to %s", len(df_out), OUTPUT.name)
    return {"status": "DONE", "symbols": len(df_out), "as_of_date": as_of_date}


if __name__ == "__main__":
    r = run()
    print(f"Status:  {r['status']}")
    print(f"Symbols: {r.get('symbols', 0)}")
    print(f"As of:   {r.get('as_of_date', '')}")
    if r.get("error"):
        print(f"Error:   {r['error']}")
