"""
Holding Trend Engine -- Phase 16A (rev2)
Computes quarterly holding pattern trends (promoter / FII / DII) with QoQ deltas.

Data source: data/NSE/shareholding/quarterly_shp.csv  (populated by shareholding_engine.py)
Output:      data/NSE/shareholding/holding_trends.csv

Replaces the original nselib-based fetcher; nselib.capital_market.shareholding_patterns
does not exist in the installed nselib version.  Reading from quarterly_shp.csv is both
faster and uses the same authoritative NSE XBRL data.

Columns produced:
  symbol, period, quarter_end_date, promoter_pct, fii_pct, dii_pct, public_pct,
  promoter_delta, fii_delta, dii_delta, conviction_signal, as_of_date, source, submission_date

Signals:
  STRONG_PROMOTER_FII_BUY  promoter_delta >= +1% AND fii_delta >= +0.5%
  STRONG_PROMOTER_BUY      promoter_delta >= +1%
  FII_DII_ACCUMULATION     fii_delta >= +0.5% AND dii_delta >= +0.5%
  FII_ACCUMULATION         fii_delta >= +0.5%
  DII_ACCUMULATION         dii_delta >= +0.5%
  PROMOTER_SELLING         promoter_delta <= -1%
  FII_DII_DIVERGENCE       FII buying while DII selling (or vice versa) >= 0.5%
  STABLE                   all deltas within +/-0.5%

Delta computation:
  Only computed between CONSECUTIVE quarters (FY quarter index differs by exactly 1).
  Non-consecutive windows (e.g. Q2FY23 -> Q2FY25) get NaN deltas and STABLE signal.

Guardrails:
  G-D-02: atomic writes   G-D-03: no empty DF
"""

import re
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

SHAREHOLDING_DIR = cfg.NSE_DIR / "shareholding"
SHP_CSV          = SHAREHOLDING_DIR / "quarterly_shp.csv"
OUTPUT_PATH      = SHAREHOLDING_DIR / "holding_trends.csv"
EQUITY_MASTER    = cfg.EQUITY_MASTER_DIR / "equity_master.csv"

STRONG_PROMOTER_BUY  = 1.0
FII_ACCUM_THRESHOLD  = 0.5
DII_ACCUM_THRESHOLD  = 0.5
PROMOTER_SELL_THRESH = -1.0

MAX_QUARTERS_PER_SYMBOL = 8   # show up to 8 quarters in UI


def _fy_quarter_index(label: str) -> int:
    """Convert e.g. 'Q2FY25' -> 101 for sorting.  Unknown -> -1."""
    m = re.match(r"Q(\d)FY(\d+)$", label)
    if not m:
        return -1
    q, fy = int(m.group(1)), int(m.group(2))
    return fy * 4 + q


def _is_consecutive(idx_a: int, idx_b: int) -> bool:
    return abs(idx_b - idx_a) == 1


def _safe_float(v) -> float | None:
    try:
        f = float(v)
        return f if pd.notna(f) else None
    except (TypeError, ValueError):
        return None


def _assign_signal(promoter_delta, fii_delta, dii_delta) -> str:
    p = _safe_float(promoter_delta)
    f = _safe_float(fii_delta)
    d = _safe_float(dii_delta)

    if p is not None and p >= STRONG_PROMOTER_BUY:
        if f is not None and f >= FII_ACCUM_THRESHOLD:
            return "STRONG_PROMOTER_FII_BUY"
        return "STRONG_PROMOTER_BUY"
    if f is not None and d is not None:
        if f >= FII_ACCUM_THRESHOLD and d >= DII_ACCUM_THRESHOLD:
            return "FII_DII_ACCUMULATION"
        if f >= FII_ACCUM_THRESHOLD and d <= -DII_ACCUM_THRESHOLD:
            return "FII_DII_DIVERGENCE"
        if f <= -FII_ACCUM_THRESHOLD and d >= DII_ACCUM_THRESHOLD:
            return "FII_DII_DIVERGENCE"
    if f is not None and f >= FII_ACCUM_THRESHOLD:
        return "FII_ACCUMULATION"
    if d is not None and d >= DII_ACCUM_THRESHOLD:
        return "DII_ACCUMULATION"
    if p is not None and p <= PROMOTER_SELL_THRESH:
        return "PROMOTER_SELLING"
    return "STABLE"


class HoldingTrendEngine:
    """
    Reads quarterly_shp.csv and produces holding_trends.csv with QoQ delta signals.
    Only rows with valid fii_pct are included (XBRL-sourced institutional data).
    Up to MAX_QUARTERS_PER_SYMBOL most-recent quarters are retained per symbol.
    """

    def run(self) -> bool:
        logger.info("[HoldingTrend] Starting from quarterly_shp.csv")

        if not SHP_CSV.exists():
            logger.error(f"[HoldingTrend] {SHP_CSV} not found — run shareholding_engine.py first")
            return False

        shp = pd.read_csv(SHP_CSV, low_memory=False)

        # Only rows with FII/DII data (XBRL-sourced)
        shp = shp[shp["fii_pct"].notna()].copy()
        if shp.empty:
            logger.error("[HoldingTrend] No rows with fii_pct in quarterly_shp.csv")
            return False
        logger.info(f"[HoldingTrend] {len(shp)} rows with FII data across {shp['window_label'].nunique()} quarters")

        # Rename window_label -> period for output schema
        shp["period"] = shp["window_label"]
        shp["fy_idx"] = shp["period"].apply(_fy_quarter_index)
        shp = shp[shp["fy_idx"] >= 0]  # drop malformed labels

        # Sort by symbol then FY quarter index
        shp = shp.sort_values(["symbol", "fy_idx"]).reset_index(drop=True)

        # Keep only the most-recent MAX_QUARTERS_PER_SYMBOL quarters per symbol
        shp = shp.groupby("symbol", group_keys=False).tail(MAX_QUARTERS_PER_SYMBOL).reset_index(drop=True)

        # Compute QoQ deltas — only for truly consecutive quarters
        out_rows = []
        for sym, grp in shp.groupby("symbol"):
            rows = grp.reset_index(drop=True)
            for i, row in rows.iterrows():
                curr_idx = row["fy_idx"]
                promoter_delta = fii_delta = dii_delta = None

                if i > 0:
                    prev = rows.iloc[i - 1]
                    if _is_consecutive(prev["fy_idx"], curr_idx):
                        curr_p, prev_p = _safe_float(row["promoter_pct"]), _safe_float(prev["promoter_pct"])
                        curr_f, prev_f = _safe_float(row["fii_pct"]),      _safe_float(prev["fii_pct"])
                        curr_d, prev_d = _safe_float(row["dii_pct"]),      _safe_float(prev["dii_pct"])
                        if curr_p is not None and prev_p is not None:
                            promoter_delta = round(curr_p - prev_p, 2)
                        if curr_f is not None and prev_f is not None:
                            fii_delta = round(curr_f - prev_f, 2)
                        if curr_d is not None and prev_d is not None:
                            dii_delta = round(curr_d - prev_d, 2)

                signal = _assign_signal(promoter_delta, fii_delta, dii_delta)

                out_rows.append({
                    "symbol":           sym,
                    "period":           row["period"],
                    "quarter_end_date": str(row.get("quarter_end_date", "")),
                    "promoter_pct":     _safe_float(row.get("promoter_pct")),
                    "fii_pct":          _safe_float(row.get("fii_pct")),
                    "dii_pct":          _safe_float(row.get("dii_pct")),
                    "public_pct":       _safe_float(row.get("public_pct")),
                    "promoter_delta":   promoter_delta,
                    "fii_delta":        fii_delta,
                    "dii_delta":        dii_delta,
                    "conviction_signal": signal,
                    "as_of_date":       str(date.today()),
                    "source":           str(row.get("source", "nse_xbrl")),
                    "submission_date":  str(row.get("submission_date", "")),
                })

        df = pd.DataFrame(out_rows)
        if df.empty:
            logger.error("[HoldingTrend] No output rows produced")
            return False

        # G-D-02: atomic write
        tmp = OUTPUT_PATH.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))

        logger.info(
            f"[HoldingTrend] Done: {len(df)} rows, "
            f"{df['symbol'].nunique()} symbols, "
            f"{sorted(df['period'].unique())} quarters"
        )
        return True


if __name__ == "__main__":
    HoldingTrendEngine().run()
