"""
Score Snapshot Engine
Phase SA-1 D2 -- Daily point-in-time retention of every key stock score.

Every intelligence CSV on this platform is OVERWRITTEN daily, which made it
impossible to ever measure whether the scores predict anything. This engine
appends today's scores to an append-only parquet so the Signal Efficacy
engine can grade the platform's own live signals (deals, sector flow, ML,
conviction) after enough history accumulates -- the honest path to
'highest accuracy': measure, then weight.

Reads (read-only, G-D-01):
  data/intelligence/bull_run_probability.csv     bull_run_score, sector/deal/corp scores
  data/intelligence/ml_scores_combined.csv       ml_bull_run_score, accumulation_score
  data/intelligence/trade_conviction_scores.csv  conviction_score
  data/intelligence/technical_indicators.csv     trend_signal, rsi_14, prox_52w_high

Writes (append-only with per-date dedupe, G-D-02/G-D-05):
  data/intelligence/history/scores_history.parquet

Run:  py -3.11 -m engines.research.score_snapshot_engine
"""

import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

HISTORY_DIR = cfg.INTELLIGENCE_DIR / "history"
OUTPUT_PQ   = HISTORY_DIR / "scores_history.parquet"

SOURCES = {
    "bull_run": {
        "path": cfg.INTELLIGENCE_DIR / "bull_run_probability.csv",
        "cols": {"bull_run_score": "bull_run_score", "price_score": "price_score",
                 "sector_flow_score": "sector_flow_score", "deal_score": "deal_score",
                 "corporate_score": "corporate_score", "label": "bull_label"},
    },
    "ml": {
        "path": cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv",
        "cols": {"ml_bull_run_score": "ml_bull_run_score",
                 "accumulation_score": "ml_accum_score"},
    },
    "conviction": {
        "path": cfg.INTELLIGENCE_DIR / "trade_conviction_scores.csv",
        "cols": {"score": "conviction_score", "action": "conviction_action"},
    },
    "technical": {
        "path": cfg.INTELLIGENCE_DIR / "technical_indicators.csv",
        "cols": {"trend_signal": "trend_signal", "rsi": "rsi_14",
                 "prox_52w_high": "prox_52w_high", "vol_20d_avg": "vol_20d_avg",
                 "adx": "adx"},
    },
}


class ScoreSnapshotEngine:
    """Appends today's cross-sectional scores to the point-in-time archive."""

    def __init__(self):
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        self.snap_date = date.today().isoformat()

    def run(self) -> bool:
        logger.info("[ScoreSnapshot] Starting for %s", self.snap_date)
        merged: pd.DataFrame | None = None

        for name, spec in SOURCES.items():
            if not spec["path"].exists():
                logger.warning("[ScoreSnapshot] Missing source %s -- skipped", name)
                continue
            try:
                usecols = ["symbol"] + list(spec["cols"].keys())
                df = pd.read_csv(spec["path"], usecols=lambda c: c in usecols)
            except Exception as e:
                logger.warning("[ScoreSnapshot] Failed reading %s: %s", name, e)
                continue
            if "symbol" not in df.columns or df.empty:
                continue
            df["symbol"] = df["symbol"].str.strip().str.upper()
            df = df.rename(columns=spec["cols"])
            keep = ["symbol"] + [v for v in spec["cols"].values() if v in df.columns]
            df = df[keep].drop_duplicates(subset=["symbol"], keep="last")
            merged = df if merged is None else merged.merge(df, on="symbol", how="outer")

        if merged is None or merged.empty:                      # G-D-03
            logger.warning("[ScoreSnapshot] No sources available -- nothing to snapshot")
            return True   # valid state on a fresh install

        merged.insert(0, "snap_date", self.snap_date)

        # Append with same-date dedupe (G-D-05): re-running today replaces today
        if OUTPUT_PQ.exists():
            hist = pd.read_parquet(OUTPUT_PQ)
            hist = hist[hist["snap_date"] != self.snap_date]
            merged = pd.concat([hist, merged], ignore_index=True)

        tmp = OUTPUT_PQ.with_suffix(".tmp.parquet")             # G-D-02
        merged.to_parquet(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PQ))

        n_today = int((merged["snap_date"] == self.snap_date).sum())
        n_dates = merged["snap_date"].nunique()
        logger.info("[ScoreSnapshot] Complete -- %d symbols today, %d dates in archive",
                    n_today, n_dates)
        return True


if __name__ == "__main__":
    ok = ScoreSnapshotEngine().run()
    sys.exit(0 if ok else 1)
