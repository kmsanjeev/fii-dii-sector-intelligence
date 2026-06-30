"""
Feature Engineering Engine — Phase 12A
Builds the historical feature matrix from all intelligence layers.
Output: data/intelligence/ml_features/feature_matrix.parquet

Features per symbol per date:
  Price:       ret_30d, ret_90d, ret_365d, vol_ratio, price_score
  Sector:      sector_FII_flow_score, sector_combined_score, rotation_signal_encoded
  Participant: FII_flow_score, DII_flow_score, Smart_Money_Score, Market_Regime_encoded
  Corporate:   deal_score (neutral=50), corporate_score (confidence, neutral=50)
  Derived:     bull_run_score (phase 8B), label_encoded

Target (for accumulation model):
  is_up_10pct_in_20d — computed from bhavcopy price 20 trading days forward
  is_up_5pct_in_10d  — shorter-term variant

Look-ahead bias prevention:
  Features at date T, target from price at T+20 (or T+60 for bull run).
  TimeSeriesSplit CV only — no random shuffle.
"""

import os
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

ML_DIR = cfg.INTELLIGENCE_DIR / "ml_features"
OUTPUT_PATH = ML_DIR / "feature_matrix.parquet"
OUTPUT_CSV   = ML_DIR / "feature_matrix.csv"  # also write CSV for inspection

BULL_RUN   = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
PRICE_MOM  = cfg.INTELLIGENCE_DIR / "price_momentum.csv"
SECTOR_ROT = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
PART_INTEL = cfg.INTELLIGENCE_DIR / "participant_intelligence.csv"
DEAL_SIG   = cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv"
CORP_CONF  = cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv"

LABEL_MAP = {
    "STRONG_CANDIDATE": 4,
    "EMERGING":         3,
    "WATCHLIST":        2,
    "NEUTRAL":          1,
    "AVOID":            0,
}
ROTATION_MAP = {
    "EARLY_ROTATION": 5,
    "LEADING":        4,
    "MOMENTUM":       3,
    "EMERGING":       2,
    "LAGGING":        1,
    "DECLINING":      0,
}
REGIME_MAP = {
    "STRONG_ACCUMULATION": 4,
    "ACCUMULATION":        3,
    "NEUTRAL":             2,
    "DISTRIBUTION":        1,
    "STRONG_DISTRIBUTION": 0,
}


class FeatureEngineeringEngine:
    """
    Assembles a static snapshot feature matrix from the current intelligence outputs.
    This is a point-in-time snapshot (not time-series) suitable for initial model training.
    The full time-series version will be built in Phase 12B.
    """

    def run(self) -> bool:
        logger.info("[FeatureEng] Starting feature engineering")
        ML_DIR.mkdir(parents=True, exist_ok=True)

        try:
            df = self._build_matrix()
            if df.empty:
                logger.error("[FeatureEng] Empty feature matrix — aborting")
                return False

            self._validate(df)
            self._save(df)
            logger.info(f"[FeatureEng] Complete: {len(df)} symbols, {len(df.columns)} features")
            return True

        except Exception as e:
            logger.error(f"[FeatureEng] Failed: {e}", exc_info=True)
            raise

    def _build_matrix(self) -> pd.DataFrame:
        # Base: bull run probability (has all 4 component scores)
        if not BULL_RUN.exists():
            raise FileNotFoundError(f"Required: {BULL_RUN}")

        bull = pd.read_csv(BULL_RUN)
        bull = bull.rename(columns={"market_regime": "regime_raw"})

        # Price momentum (sector_rel and raw returns)
        price_cols = ["symbol", "ret_30d", "ret_90d", "ret_365d", "vol_ratio",
                      "price_score", "sector_rel_30d"]
        if PRICE_MOM.exists():
            price = pd.read_csv(PRICE_MOM, usecols=[c for c in price_cols if c in
                                                     pd.read_csv(PRICE_MOM, nrows=0).columns])
            bull = bull.merge(price, on="symbol", how="left", suffixes=("", "_pm"))

        # Sector features
        if SECTOR_ROT.exists():
            sec = pd.read_csv(SECTOR_ROT, usecols=[
                "sector", "FII_flow_score", "combined_score", "rotation_signal"
            ]).rename(columns={
                "FII_flow_score": "sector_FII_flow",
                "combined_score": "sector_combined_score",
            })
            bull = bull.merge(sec, on="sector", how="left")
            bull["rotation_signal_enc"] = bull["rotation_signal"].map(ROTATION_MAP).fillna(2)

        # Participant regime (latest snapshot, same for all symbols)
        if PART_INTEL.exists():
            part = pd.read_csv(PART_INTEL, usecols=[
                "date", "FII_flow_score", "DII_flow_score",
                "Smart_Money_Score", "Market_Regime"
            ]).sort_values("date").iloc[-1]
            bull["part_FII_flow"] = float(part.get("FII_flow_score", 0) or 0)
            bull["part_DII_flow"] = float(part.get("DII_flow_score", 0) or 0)
            bull["part_smart_money"] = float(part.get("Smart_Money_Score", 0) or 0)
            bull["regime_enc"] = REGIME_MAP.get(str(part.get("Market_Regime", "NEUTRAL")), 2)

        # Corporate confidence
        if CORP_CONF.exists():
            corp = pd.read_csv(CORP_CONF, usecols=["symbol", "confidence_score_12m"])
            corp = corp.rename(columns={"confidence_score_12m": "corp_confidence"})
            bull = bull.merge(corp, on="symbol", how="left")

        # Deal signals
        if DEAL_SIG.exists():
            deals = pd.read_csv(DEAL_SIG, usecols=["symbol", "inst_net_value_cr"])
            deals = deals.rename(columns={"inst_net_value_cr": "deal_net_cr"})
            bull = bull.merge(deals, on="symbol", how="left")

        # Encode label
        bull["label_enc"] = bull["label"].map(LABEL_MAP).fillna(1)

        # Select final feature columns
        feature_cols = [
            "symbol", "sector", "as_of_date",
            # Scores from 8B
            "bull_run_score", "label", "label_enc",
            "price_score", "sector_flow_score", "deal_score", "corporate_score",
            "regime_multiplier",
            # Price
            "ret_30d", "ret_90d", "ret_365d", "vol_ratio",
            # Sector
            "sector_FII_flow", "sector_combined_score", "rotation_signal_enc",
            # Participant
            "part_FII_flow", "part_DII_flow", "part_smart_money", "regime_enc",
            # Corporate
            "corp_confidence", "deal_net_cr",
        ]
        available = [c for c in feature_cols if c in bull.columns]
        return bull[available].copy()

    def _validate(self, df: pd.DataFrame):
        assert not df.empty, "Feature matrix is empty"
        assert "symbol" in df.columns, "Missing symbol column"
        assert "bull_run_score" in df.columns, "Missing target column"
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        inf_count = np.isinf(df[numeric_cols]).sum().sum()
        if inf_count > 0:
            logger.warning(f"[FeatureEng] {inf_count} Inf values — replacing with NaN")
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
        logger.info(f"[FeatureEng] Validated: {len(df)} rows, {df.isnull().sum().sum()} nulls")

    def _save(self, df: pd.DataFrame):
        tmp = OUTPUT_PATH.with_suffix(".tmp.parquet")
        df.to_parquet(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))

        tmp_csv = OUTPUT_CSV.with_suffix(".tmp.csv")
        df.to_csv(tmp_csv, index=False)
        shutil.move(str(tmp_csv), str(OUTPUT_CSV))

        logger.info(f"[FeatureEng] Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    engine = FeatureEngineeringEngine()
    engine.run()
    import pandas as pd
    df = pd.read_parquet(OUTPUT_PATH)
    print(f"Feature matrix: {len(df)} symbols x {len(df.columns)} features")
    print(f"Columns: {list(df.columns)}")
    print(df[["symbol", "bull_run_score", "label", "price_score"]].head(10))
