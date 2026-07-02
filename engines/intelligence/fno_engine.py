"""
F&O Intelligence Engine
Computes market PCR and per-stock futures OI signals from F&O bhavcopy CSVs.
Outputs:
  data/intelligence/fno_intelligence.csv   — per-stock OI + signal
  data/intelligence/market_context.json    — PCR + context for dashboard

Run: py -3.11 -m engines.intelligence.fno_engine
"""

import json
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

FNO_DIR    = cfg.NSE_DIR / "bhavcopy" / "fno"
FNO_OUTPUT = cfg.INTELLIGENCE_DIR / "fno_intelligence.csv"
CTX_OUTPUT = cfg.INTELLIGENCE_DIR / "market_context.json"
LOOKBACK   = 5   # sessions for 5D OI trend


def _find_fno_files(n: int) -> list[Path]:
    files: list[Path] = []
    for yr_dir in sorted(FNO_DIR.iterdir()):
        if yr_dir.is_dir():
            files.extend(sorted(yr_dir.glob("fo_*.csv")))
    return files[-n:]


def _oi_signal(oi_change: float, price_change: float) -> str:
    if oi_change > 0 and price_change >= 0:
        return "LONG_BUILDUP"
    if oi_change > 0 and price_change < 0:
        return "SHORT_BUILDUP"
    if oi_change < 0 and price_change < 0:
        return "LONG_UNWINDING"
    return "SHORT_COVERING"


def _pcr_signal(pcr: float | None) -> str:
    if pcr is None:
        return "UNKNOWN"
    if pcr > 1.2:
        return "BULLISH"
    if pcr < 0.7:
        return "BEARISH"
    return "NEUTRAL"


def run() -> dict:
    files = _find_fno_files(LOOKBACK)
    if not files:
        return {"status": "ERROR", "error": "No F&O CSV files found"}

    logger.info("[FNO] Processing %d F&O files", len(files))

    # ── Latest file → PCR + stock OI ──────────────────────────────────────────
    df_latest = pd.read_csv(files[-1], low_memory=False)
    trade_date = str(df_latest["TradDt"].iloc[0]) if "TradDt" in df_latest.columns else ""

    options = df_latest[df_latest["FinInstrmTp"] == "STO"].copy()
    calls_oi = float(options[options["OptnTp"] == "CE"]["OpnIntrst"].sum()) if not options.empty else 0
    puts_oi  = float(options[options["OptnTp"] == "PE"]["OpnIntrst"].sum()) if not options.empty else 0
    pcr      = round(puts_oi / calls_oi, 3) if calls_oi > 0 else None

    futures = df_latest[df_latest["FinInstrmTp"] == "STF"].copy()

    # Near-month per symbol = contract with highest OI
    if not futures.empty:
        near = (
            futures.sort_values("OpnIntrst", ascending=False)
            .drop_duplicates(subset=["TckrSymb"], keep="first")
            .copy()
        )
    else:
        near = pd.DataFrame()

    # ── Previous session close for price-change calculation ────────────────────
    prev_close_map: dict[str, float] = {}
    if len(files) >= 2:
        try:
            df_prev = pd.read_csv(files[-2], low_memory=False)
            prev_fut = df_prev[df_prev["FinInstrmTp"] == "STF"].copy()
            if not prev_fut.empty:
                prev_near = prev_fut.sort_values("OpnIntrst", ascending=False).drop_duplicates(subset=["TckrSymb"], keep="first")
                prev_close_map = dict(zip(prev_near["TckrSymb"].astype(str), prev_near["ClsPric"].astype(float)))
        except Exception as exc:
            logger.warning("[FNO] Could not read previous file: %s", exc)

    # ── 5D cumulative OI change ────────────────────────────────────────────────
    oi_5d_map: dict[str, float] = {}
    for f in files:
        try:
            df_f = pd.read_csv(f, low_memory=False, usecols=["FinInstrmTp", "TckrSymb", "OpnIntrst", "ChngInOpnIntrst"])
            fut_f = df_f[df_f["FinInstrmTp"] == "STF"]
            if not fut_f.empty:
                near_f = fut_f.sort_values("OpnIntrst", ascending=False).drop_duplicates(subset=["TckrSymb"], keep="first")
                for _, row in near_f.iterrows():
                    sym = str(row["TckrSymb"])
                    oi_5d_map[sym] = oi_5d_map.get(sym, 0.0) + float(row.get("ChngInOpnIntrst", 0) or 0)
        except Exception as exc:
            logger.warning("[FNO] 5D map failed for %s: %s", f.name, exc)

    # ── Build per-stock records ────────────────────────────────────────────────
    records = []
    if not near.empty:
        for _, row in near.iterrows():
            sym       = str(row["TckrSymb"])
            oi_now    = float(row.get("OpnIntrst", 0) or 0)
            oi_1d     = float(row.get("ChngInOpnIntrst", 0) or 0)
            oi_5d     = float(oi_5d_map.get(sym, 0))
            close_fut = float(row.get("ClsPric", 0) or 0)
            prev_cl   = prev_close_map.get(sym, close_fut)
            price_chg = close_fut - prev_cl if prev_cl else 0.0

            records.append({
                "symbol":      sym,
                "futures_oi":  round(oi_now, 0),
                "oi_1d":       round(oi_1d,  0),
                "oi_5d":       round(oi_5d,  0),
                "oi_signal":   _oi_signal(oi_1d, price_chg),
                "fut_close":   round(close_fut, 2),
                "expiry":      str(row.get("XpryDt", "")),
                "as_of_date":  trade_date,
            })

    # ── Save F&O intelligence CSV ──────────────────────────────────────────────
    cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    if records:
        fno_df = pd.DataFrame(records)
        tmp = FNO_OUTPUT.with_suffix(".tmp.csv")
        fno_df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(FNO_OUTPUT))
        logger.info("[FNO] Saved %d stock OI records", len(fno_df))

    # ── Save market context JSON ───────────────────────────────────────────────
    ctx = {
        "trade_date": trade_date,
        "pcr":        pcr,
        "pcr_signal": _pcr_signal(pcr),
        "calls_oi":   calls_oi,
        "puts_oi":    puts_oi,
    }
    tmp_ctx = CTX_OUTPUT.with_suffix(".tmp.json")
    with open(tmp_ctx, "w", encoding="utf-8") as fh:
        json.dump(ctx, fh, indent=2)
    shutil.move(str(tmp_ctx), str(CTX_OUTPUT))
    logger.info("[FNO] Context saved: PCR=%.3f (%s)", pcr or 0, ctx["pcr_signal"])

    return {"status": "DONE", "symbols": len(records), "pcr": pcr, "trade_date": trade_date}


if __name__ == "__main__":
    r = run()
    print(f"Status:  {r['status']}")
    print(f"Symbols: {r.get('symbols', 0)}")
    print(f"PCR:     {r.get('pcr')}")
    print(f"Date:    {r.get('trade_date', '')}")
    if r.get("error"):
        print(f"Error:   {r['error']}")
