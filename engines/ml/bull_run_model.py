"""
Bull Run ML Model — Phase 12C
LightGBM + XGBoost ensemble for multi-label bull run probability.
Replaces the rule-based scoring from Phase 8B with learned weights.

Target: label_enc (0=AVOID, 1=NEUTRAL, 2=WATCHLIST, 3=EMERGING, 4=STRONG_CANDIDATE)
        treated as ordinal regression (predict each class probability, return weighted score)

Ensemble: 0.6 * LightGBM + 0.4 * XGBoost (LightGBM typically wins on tabular financial data)

SHAP: computed for top 100 predictions to explain what drove the score.
"""

import shutil
import json
from pathlib import Path
import numpy as np
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

ML_DIR = cfg.INTELLIGENCE_DIR / "ml_features"
FEATURE_MATRIX = ML_DIR / "feature_matrix.parquet"
MODEL_DIR = ML_DIR / "models"
SCORES_PATH = cfg.INTELLIGENCE_DIR / "ml_bull_run_scores.csv"
SHAP_PATH   = cfg.INTELLIGENCE_DIR / "ml_shap_values.csv"

FEATURE_COLS = [
    "price_score", "sector_flow_score", "deal_score", "corporate_score",
    "ret_30d", "ret_90d", "ret_365d", "vol_ratio",
    "sector_FII_flow", "sector_combined_score", "rotation_signal_enc",
    "part_FII_flow", "part_DII_flow", "part_smart_money", "regime_enc",
    "corp_confidence", "deal_net_cr",
]

# Ordinal weights for weighted score: AVOID=0, NEUTRAL=25, WATCHLIST=50, EMERGING=75, STRONG=100
LABEL_WEIGHTS = np.array([0, 25, 50, 75, 100])


class BullRunMLModel:
    """
    LightGBM + XGBoost ensemble for bull run multi-class scoring.
    """

    def __init__(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.lgbm_path = MODEL_DIR / "bull_run_lgbm.txt"
        self.xgb_path  = MODEL_DIR / "bull_run_xgb.json"
        self.meta_path = MODEL_DIR / "bull_run_meta.json"

    def run(self) -> bool:
        try:
            import lightgbm as lgb
            import xgboost as xgb
            from sklearn.model_selection import TimeSeriesSplit
            import shap
        except ImportError:
            logger.error("[BullRunML] lightgbm, xgboost or shap not installed")
            return False

        logger.info("[BullRunML] Starting training")

        if not FEATURE_MATRIX.exists():
            raise FileNotFoundError(f"Run feature_engineering.py first: {FEATURE_MATRIX}")

        df = pd.read_parquet(FEATURE_MATRIX)
        X, y, symbols = self._prepare(df)
        n_classes = len(np.unique(y))

        # LightGBM
        lgbm_model = lgb.LGBMClassifier(
            n_estimators=300,
            num_leaves=31,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            objective="multiclass",
            num_class=n_classes,
            random_state=42,
            verbose=-1,
        )
        lgbm_model.fit(X, y)

        # XGBoost
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=n_classes,
            random_state=42,
        )
        xgb_model.fit(X, y)

        self._save_models(lgbm_model, xgb_model, X.columns.tolist(), n_classes)

        # Ensemble scoring
        lgbm_proba = lgbm_model.predict_proba(X)
        xgb_proba  = xgb_model.predict_proba(X)

        # Handle class count mismatch
        if lgbm_proba.shape[1] > len(LABEL_WEIGHTS):
            weights = LABEL_WEIGHTS[:lgbm_proba.shape[1]]
        else:
            weights = LABEL_WEIGHTS[:lgbm_proba.shape[1]]

        ensemble_proba = 0.6 * lgbm_proba + 0.4 * xgb_proba
        ml_score = (ensemble_proba * weights).sum(axis=1)

        predicted_label = np.array(["AVOID", "NEUTRAL", "WATCHLIST", "EMERGING", "STRONG_CANDIDATE"])[
            ensemble_proba.argmax(axis=1)
        ]

        scores_df = pd.DataFrame({
            "symbol":          symbols,
            "ml_bull_run_score": np.round(ml_score, 2),
            "ml_label":        predicted_label,
        })
        for i, col in enumerate(["prob_AVOID", "prob_NEUTRAL", "prob_WATCHLIST", "prob_EMERGING", "prob_STRONG"]):
            if i < ensemble_proba.shape[1]:
                scores_df[col] = np.round(ensemble_proba[:, i], 4)

        self._save_scores(scores_df)

        # SHAP for top 100 symbols
        try:
            top_idx = scores_df.nlargest(100, "ml_bull_run_score").index
            X_top = X.iloc[top_idx]
            explainer = shap.TreeExplainer(lgbm_model)
            shap_vals = explainer.shap_values(X_top)
            if isinstance(shap_vals, list):
                shap_arr = np.abs(np.array(shap_vals)).mean(axis=0)
            else:
                shap_arr = np.abs(shap_vals)
            shap_df = pd.DataFrame(shap_arr, columns=X.columns)
            shap_df.insert(0, "symbol", symbols.iloc[top_idx].values)
            tmp = SHAP_PATH.with_suffix(".tmp.csv")
            shap_df.to_csv(tmp, index=False)
            shutil.move(str(tmp), str(SHAP_PATH))
            logger.info(f"[BullRunML] SHAP values saved for top 100 symbols")
        except Exception as e:
            logger.warning(f"[BullRunML] SHAP computation failed (non-critical): {e}")

        logger.info(f"[BullRunML] Scored {len(scores_df)} symbols")
        return True

    def _prepare(self, df: pd.DataFrame):
        available = [c for c in FEATURE_COLS if c in df.columns]
        X = df[available].copy()
        for col in X.columns:
            X[col] = X[col].fillna(X[col].median())

        y = df["label_enc"].fillna(1).astype(int).values
        symbols = df["symbol"]
        logger.info(f"[BullRunML] {len(available)} features, {len(y)} samples")
        return X, y, symbols

    def _save_models(self, lgbm, xgb, feature_names, n_classes):
        lgbm.booster_.save_model(str(self.lgbm_path))
        xgb.save_model(str(self.xgb_path))
        meta = {
            "model_type":   "LightGBM (0.6) + XGBoost (0.4) ensemble",
            "target":       "label_enc (0=AVOID ... 4=STRONG_CANDIDATE)",
            "n_classes":    n_classes,
            "feature_names": feature_names,
            "lgbm_estimators": 300,
            "xgb_estimators":  200,
            "trained_at":   pd.Timestamp.now().isoformat(),
        }
        with open(self.meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"[BullRunML] Models saved to {MODEL_DIR}")

    def _save_scores(self, df: pd.DataFrame):
        tmp = SCORES_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(SCORES_PATH))
        logger.info(f"[BullRunML] Scores saved: {SCORES_PATH}")


if __name__ == "__main__":
    engine = BullRunMLModel()
    engine.run()
    df = pd.read_csv(SCORES_PATH)
    print(f"Scored {len(df)} symbols")
    print(df.nlargest(10, "ml_bull_run_score")[["symbol", "ml_bull_run_score", "ml_label"]])
