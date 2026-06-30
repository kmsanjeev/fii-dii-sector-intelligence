"""
ML Scorer — Phase 12D
Daily inference: loads saved models and scores current feature matrix.
Run this daily after intelligence CSVs are refreshed (post 16:00 IST).

Usage:
    py -3.11 engines/ml/ml_scorer.py
"""

import sys
from pathlib import Path
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

ML_DIR = cfg.INTELLIGENCE_DIR / "ml_features"
MODEL_DIR = ML_DIR / "models"
FEATURE_MATRIX = ML_DIR / "feature_matrix.parquet"
ML_SCORES_OUT = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"

import shutil


def run_daily_scoring():
    logger.info("[MLScorer] Starting daily scoring")

    # Step 1: Rebuild feature matrix
    from engines.ml.feature_engineering import FeatureEngineeringEngine
    fe = FeatureEngineeringEngine()
    if not fe.run():
        logger.error("[MLScorer] Feature engineering failed")
        return False

    df = pd.read_parquet(FEATURE_MATRIX)

    # Step 2: Accumulation model scores
    acc_scores = pd.DataFrame()
    acc_model_path = MODEL_DIR / "accumulation_xgb.json"
    if acc_model_path.exists():
        try:
            from engines.ml.accumulation_model import AccumulationModel
            acc_model = AccumulationModel()
            scores = acc_model.load_and_score(df)
            acc_scores = pd.DataFrame({
                "symbol": df["symbol"],
                "accumulation_score": scores.values,
            })
            logger.info(f"[MLScorer] Accumulation scores: {len(acc_scores)} symbols")
        except Exception as e:
            logger.warning(f"[MLScorer] Accumulation scoring failed: {e}")

    # Step 3: Bull run ML scores
    br_scores = pd.DataFrame()
    lgbm_path = MODEL_DIR / "bull_run_lgbm.txt"
    xgb_path  = MODEL_DIR / "bull_run_xgb.json"
    if lgbm_path.exists() and xgb_path.exists():
        try:
            import lightgbm as lgb, xgboost as xgb_lib, numpy as np
            from engines.ml.bull_run_model import FEATURE_COLS, LABEL_WEIGHTS

            lgbm_model = lgb.Booster(model_file=str(lgbm_path))
            xgb_model  = xgb_lib.XGBClassifier()
            xgb_model.load_model(str(xgb_path))

            available = [c for c in FEATURE_COLS if c in df.columns]
            X = df[available].copy()
            for col in X.columns:
                X[col] = X[col].fillna(X[col].median())

            lgbm_p = lgbm_model.predict(X, num_iteration=lgbm_model.best_iteration)
            xgb_p  = xgb_model.predict_proba(X)

            n_cls = min(lgbm_p.shape[1], xgb_p.shape[1])
            weights = LABEL_WEIGHTS[:n_cls]
            ens = 0.6 * lgbm_p[:, :n_cls] + 0.4 * xgb_p[:, :n_cls]
            ml_score = (ens * weights).sum(axis=1)

            br_scores = pd.DataFrame({
                "symbol": df["symbol"],
                "ml_bull_run_score": np.round(ml_score, 2),
            })
            logger.info(f"[MLScorer] Bull run scores: {len(br_scores)} symbols")
        except Exception as e:
            logger.warning(f"[MLScorer] Bull run scoring failed: {e}")

    # Step 4: Merge and save
    combined = df[["symbol", "sector", "bull_run_score", "label"]].copy()
    if not acc_scores.empty:
        combined = combined.merge(acc_scores, on="symbol", how="left")
    if not br_scores.empty:
        combined = combined.merge(br_scores, on="symbol", how="left")

    tmp = ML_SCORES_OUT.with_suffix(".tmp.csv")
    combined.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(ML_SCORES_OUT))
    logger.info(f"[MLScorer] Combined scores saved: {ML_SCORES_OUT} ({len(combined)} symbols)")
    return True


if __name__ == "__main__":
    success = run_daily_scoring()
    if success:
        df = pd.read_csv(ML_SCORES_OUT)
        print(f"Scored {len(df)} symbols")
        top_cols = [c for c in ["symbol", "ml_bull_run_score", "accumulation_score", "label"] if c in df.columns]
        print(df.nlargest(10, top_cols[1] if len(top_cols) > 1 else "bull_run_score")[top_cols])
    else:
        sys.exit(1)
