"""
Participant Intelligence Engine
Phase 5C — Conviction, divergence, smart money, and market opportunity signals

Reads:
  data/intelligence/participant_flow_scores.csv  (from Phase 5B)

Outputs:
  data/intelligence/participant_intelligence.csv

Columns:
  date
  FII_flow_score, DII_flow_score, PRO_flow_score, CLIENT_flow_score
  FPI_flow_score, MF_flow_score

  FII_conviction   — % of last 20D with positive OI delta (0–100)
  DII_conviction
  PRO_conviction
  CLIENT_conviction

  Smart_Money_Score  = avg(FII_flow_score, PRO_flow_score)
  Retail_Score       = CLIENT_flow_score (contrarian indicator)
  FII_DII_Divergence = FII_flow_score - DII_flow_score
  Smart_Retail_Divergence = Smart_Money_Score - CLIENT_flow_score
  Market_Opportunity = max(0, Smart_Money) × max(0, −CLIENT) / 100

  Cash_Institutional_Score = avg(FPI_flow_score, MF_flow_score)

  Market_Regime — ensemble: STRONG_ACCUMULATION / ACCUMULATION / NEUTRAL /
                             DISTRIBUTION / STRONG_DISTRIBUTION
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

logger = get_logger("participant_intelligence")

INTELLIGENCE_DIR = ROOT / "data" / "intelligence"
FLOW_SCORES_FILE = INTELLIGENCE_DIR / "participant_flow_scores.csv"
OUTPUT_FILE      = INTELLIGENCE_DIR / "participant_intelligence.csv"

PARTICIPANTS = ["FII", "DII", "PRO", "CLIENT"]
CONVICTION_WINDOW = 20


def _classify_regime(score: float) -> str:
    if score >= 40:
        return "STRONG_ACCUMULATION"
    if score >= 15:
        return "ACCUMULATION"
    if score <= -40:
        return "STRONG_DISTRIBUTION"
    if score <= -15:
        return "DISTRIBUTION"
    return "NEUTRAL"


class ParticipantIntelligenceEngine:
    """
    Phase 5C — derives actionable participant intelligence from flow scores.

    Input:  participant_flow_scores.csv (produced by Phase 5B)
    Output: participant_intelligence.csv (full rebuild on each run)
    """

    def run(self) -> bool:
        logger.info("[ParticipantIntelligence] Starting Phase 5C")
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

        df = self._load_scores()
        if df.empty:
            logger.error("[5C] participant_flow_scores.csv is empty — run Phase 5B first")
            return False

        result = self._compute(df)
        self._save(result)
        self._print_summary(result)
        return True

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def _load_scores(self) -> pd.DataFrame:
        if not FLOW_SCORES_FILE.exists():
            logger.warning("[5C] %s not found — run participant_flow_engine.py first",
                           FLOW_SCORES_FILE)
            return pd.DataFrame()
        df = pd.read_csv(FLOW_SCORES_FILE)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date").reset_index(drop=True)
        logger.info("[5C] Flow scores: %d rows, %s → %s",
                    len(df), df["date"].min(), df["date"].max())
        return df

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def _compute(self, df: pd.DataFrame) -> pd.DataFrame:
        result = pd.DataFrame({"date": df["date"]})

        # ---- Flow scores (passthrough for reference) ----------------
        for p in PARTICIPANTS:
            col = f"{p}_flow_score"
            result[col] = pd.to_numeric(df.get(col, np.nan), errors="coerce")

        for p in ["FPI", "MF", "INSURANCE", "RETAIL"]:
            col = f"{p}_flow_score"
            result[col] = pd.to_numeric(df.get(col, np.nan), errors="coerce")

        # ---- Conviction score (% of last 20D with positive OI delta) --
        for p in PARTICIPANTS:
            delta_col = f"{p}_OI_Delta"
            if delta_col in df.columns:
                deltas = pd.to_numeric(df[delta_col], errors="coerce")
                positive = (deltas > 0).astype(float)
                result[f"{p}_conviction"] = (
                    positive.rolling(CONVICTION_WINDOW, min_periods=5).mean() * 100
                ).round(1)
            else:
                result[f"{p}_conviction"] = np.nan

        # ---- Smart Money and Retail signals ---------------------------
        fii_score    = result["FII_flow_score"]
        dii_score    = result["DII_flow_score"]
        pro_score    = result["PRO_flow_score"]
        client_score = result["CLIENT_flow_score"]

        result["Smart_Money_Score"] = ((fii_score + pro_score) / 2).round(2)
        result["Retail_Score"]      = client_score.round(2)

        # ---- Divergence signals ---------------------------------------
        result["FII_DII_Divergence"]      = (fii_score - dii_score).round(2)
        result["Smart_Retail_Divergence"] = (result["Smart_Money_Score"] - client_score).round(2)

        # ---- Market Opportunity: aligned smart + opposite retail ------
        smart = result["Smart_Money_Score"].clip(lower=0)
        anti_retail = (-client_score).clip(lower=0)
        result["Market_Opportunity"] = (smart * anti_retail / 100).round(2)

        # ---- Cash institutional composite ----------------------------
        fpi_score = result.get("FPI_flow_score", pd.Series(np.nan, index=result.index))
        mf_score  = result.get("MF_flow_score",  pd.Series(np.nan, index=result.index))
        result["Cash_Institutional_Score"] = ((fpi_score + mf_score) / 2).round(2)

        # ---- Ensemble Market Regime ----------------------------------
        # Weighted: Smart Money 50%, DII 25%, Cash Institutional 25%
        smart_w = result["Smart_Money_Score"] * 0.50
        dii_w   = dii_score * 0.25
        cash_w  = result["Cash_Institutional_Score"].fillna(0) * 0.25
        ensemble = (smart_w + dii_w + cash_w).round(2)
        result["Ensemble_Score"] = ensemble
        result["Market_Regime"]  = ensemble.apply(_classify_regime)

        return result

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("G-D-03: refusing to write empty participant_intelligence.csv")
        tmp = OUTPUT_FILE.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_FILE))
        logger.info("[5C] Saved: %s (%d rows, %d cols)",
                    OUTPUT_FILE.name, len(df), len(df.columns))

    def _print_summary(self, df: pd.DataFrame):
        last = df.iloc[-1]
        print()
        print("=" * 65)
        print("PARTICIPANT INTELLIGENCE ENGINE — PHASE 5C COMPLETE")
        print("=" * 65)
        print(f"Date range        : {df['date'].min()} → {df['date'].max()}")
        print(f"Total rows        : {len(df)}")
        print()
        print(f"Latest date       : {last['date']}")
        print(f"Market Regime     : {last.get('Market_Regime', 'N/A')}")
        print(f"Smart Money Score : {last.get('Smart_Money_Score', 0):+.1f}")
        print(f"Retail Score      : {last.get('Retail_Score', 0):+.1f}")
        print(f"Smart/Retail Div  : {last.get('Smart_Retail_Divergence', 0):+.1f}")
        print(f"Market Opportunity: {last.get('Market_Opportunity', 0):.1f}")
        print()
        print("Conviction (% of last 20D positive):")
        for p in ["FII", "DII", "PRO", "CLIENT"]:
            v = last.get(f"{p}_conviction", float("nan"))
            bar = int(v / 5) if not pd.isna(v) else 0
            print(f"  {p:8s}: {'█' * bar}{'░' * (20 - bar)} {v:.0f}%")
        print("=" * 65)


if __name__ == "__main__":
    engine = ParticipantIntelligenceEngine()
    engine.run()
