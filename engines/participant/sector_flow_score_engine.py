"""
Sector Flow Score Engine
Phase 6B — Rolling metrics and normalized z-score flow scores per platform sector

Reads:
  data/intelligence/sector_capital_flows.csv  (from Phase 6A)

Outputs:
  data/intelligence/sector_flow_scores.csv

One row per (date × sector). Columns:
  date, sector
  FII_OI_attr, DII_OI_attr, PRO_OI_attr, CLIENT_OI_attr     (raw daily attributed OI)
  FII_Vol_attr, DII_Vol_attr, PRO_Vol_attr, CLIENT_Vol_attr  (raw daily attributed volume)
  sector_weight, sector_weight_5D, sector_weight_20D         (rolling weight averages)
  FII_OI_Delta, DII_OI_Delta, PRO_OI_Delta, CLIENT_OI_Delta  (day-over-day OI change)
  FII_OI_5D, FII_OI_20D, FII_OI_60D                          (rolling OI sums per participant)
  DII_OI_5D, DII_OI_20D, DII_OI_60D
  PRO_OI_5D, PRO_OI_20D, PRO_OI_60D
  CLIENT_OI_5D, CLIENT_OI_20D, CLIENT_OI_60D
  FII_flow_score, DII_flow_score, PRO_flow_score, CLIENT_flow_score  (z-score → -100..+100)
  Smart_Money_Score  (per sector)
  Retail_Score       (per sector)
"""

import shutil
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("sector_flow_score")

INTELLIGENCE_DIR = cfg.INTELLIGENCE_DIR
INPUT_FILE  = INTELLIGENCE_DIR / "sector_capital_flows.csv"
OUTPUT_FILE = INTELLIGENCE_DIR / "sector_flow_scores.csv"

PARTICIPANTS = ["FII", "DII", "PRO", "CLIENT"]
WINDOWS      = [5, 20, 60]
Z_WINDOW     = 252
SCORE_SCALE  = 100


def _zscore_norm(series: pd.Series, window: int) -> pd.Series:
    """Rolling z-score clipped to [-3, +3] → scaled to [-SCORE_SCALE, +SCORE_SCALE]."""
    roll = series.rolling(window, min_periods=max(window // 2, 20))
    mu    = roll.mean()
    sigma = roll.std().replace(0, np.nan)
    z     = ((series - mu) / sigma).clip(-3, 3)
    return (z / 3 * SCORE_SCALE).round(2)


class SectorFlowScoreEngine:
    """
    Phase 6B — produces per-sector rolling flow scores.
    Full rebuild on each run (deterministic given same inputs).
    """

    def run(self) -> bool:
        logger.info("[SectorFlowScore] Starting Phase 6B")
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

        df = self._load_capital_flows()
        if df.empty:
            logger.error("[6B] sector_capital_flows.csv is empty — run Phase 6A first")
            return False

        result = self._compute(df)
        self._save(result)
        self._print_summary(result)
        return True

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def _load_capital_flows(self) -> pd.DataFrame:
        if not INPUT_FILE.exists():
            logger.warning("[6B] %s not found — run sector_capital_flow_engine.py first", INPUT_FILE)
            return pd.DataFrame()
        df = pd.read_csv(INPUT_FILE)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values(["date", "sector"]).reset_index(drop=True)
        logger.info("[6B] Capital flows: %d rows, %s → %s",
                    len(df), df["date"].min(), df["date"].max())
        return df

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def _compute(self, raw: pd.DataFrame) -> pd.DataFrame:
        all_sectors = sorted(raw["sector"].unique())
        sector_dfs = []

        for sector in all_sectors:
            sdf = raw[raw["sector"] == sector].copy().sort_values("date").reset_index(drop=True)
            result = pd.DataFrame({"date": sdf["date"], "sector": sector})

            # Raw attributed values
            for p in PARTICIPANTS:
                oi_col  = f"{p}_OI_Net_attr"
                vol_col = f"{p}_Volume_Net_attr"
                result[f"{p}_OI_attr"]  = pd.to_numeric(sdf.get(oi_col, np.nan), errors="coerce")
                result[f"{p}_Vol_attr"] = pd.to_numeric(sdf.get(vol_col, np.nan), errors="coerce")

            # Sector weight rolling averages
            result["sector_weight"] = pd.to_numeric(sdf.get("sector_weight", np.nan), errors="coerce")
            for w in [5, 20]:
                result[f"sector_weight_{w}D"] = (
                    result["sector_weight"].rolling(w, min_periods=1).mean().round(6)
                )

            # OI delta (day-over-day change in attributed OI)
            for p in PARTICIPANTS:
                result[f"{p}_OI_Delta"] = result[f"{p}_OI_attr"].diff().round(2)

            # Rolling OI sums per window
            for p in PARTICIPANTS:
                for w in WINDOWS:
                    result[f"{p}_OI_{w}D"] = (
                        result[f"{p}_OI_attr"].rolling(w, min_periods=1).sum().round(2)
                    )

            # Flow scores: z-normalise the 20D OI rolling sum (medium-term signal)
            for p in PARTICIPANTS:
                base = result[f"{p}_OI_{WINDOWS[1]}D"]  # 20D
                result[f"{p}_flow_score"] = _zscore_norm(base, Z_WINDOW)

            # Smart Money and Retail per sector
            result["Smart_Money_Score"] = (
                (result["FII_flow_score"] + result["PRO_flow_score"]) / 2
            ).round(2)
            result["Retail_Score"] = result["CLIENT_flow_score"].round(2)

            sector_dfs.append(result)

        combined = pd.concat(sector_dfs, ignore_index=True)
        combined = combined.sort_values(["date", "sector"]).reset_index(drop=True)
        return combined

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("G-D-03: refusing to write empty sector_flow_scores.csv")
        tmp = OUTPUT_FILE.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_FILE))
        logger.info("[6B] Saved: %s (%d rows, %d cols)", OUTPUT_FILE.name, len(df), len(df.columns))

    def _print_summary(self, df: pd.DataFrame):
        latest_date = df["date"].max()
        latest = df[df["date"] == latest_date].sort_values("FII_flow_score", ascending=False)
        print()
        print("=" * 65)
        print("SECTOR FLOW SCORE ENGINE — PHASE 6B COMPLETE")
        print("=" * 65)
        print(f"Date range   : {df['date'].min()} to {latest_date}")
        print(f"Total rows   : {len(df)}")
        print(f"Sectors      : {df['sector'].nunique()}")
        print()
        print(f"FII flow scores on {latest_date} (top & bottom 5):")
        for _, r in latest.head(5).iterrows():
            print(f"  {r['sector']:22s}: FII={r['FII_flow_score']:+6.1f}  "
                  f"DII={r['DII_flow_score']:+6.1f}  "
                  f"Smart={r['Smart_Money_Score']:+6.1f}")
        print("  " + "-" * 55)
        for _, r in latest.tail(5).iterrows():
            print(f"  {r['sector']:22s}: FII={r['FII_flow_score']:+6.1f}  "
                  f"DII={r['DII_flow_score']:+6.1f}  "
                  f"Smart={r['Smart_Money_Score']:+6.1f}")
        print("=" * 65)


if __name__ == "__main__":
    engine = SectorFlowScoreEngine()
    engine.run()
