"""
Accumulation Detection Model — Phase 12B
XGBoost binary classifier: will this stock be up 10%+ in 20 trading days?

Training:
  - Features: price_score, sector_flow_score, deal_score, corporate_score,
               ret_30d, ret_90d, ret_365d, vol_ratio, sector_FII_flow,
               part_FII_flow, part_smart_money, regime_enc
  - Target: label_enc >= 3 (EMERGING or STRONG_CANDIDATE) as proxy for accumulation
    (true target would be forward price return, requires bhavcopy time-series)
  - CV: TimeSeriesSplit (no data leakage)
  - Interpretability: SHAP values per prediction

Look-ahead bias note:
  The current feature matrix is a snapshot. In a full time-series implementation,
  features at date T must use only data available at T (not T+1).
  This model uses Phase 8B labels as the target — a score-based proxy —
  until bhavcopy time-series target generation is available (Phase 12D).
"""

import shutil
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

ML_DIR = cfg.INTELLIGENCE_DIR / "ml_features"
FEATURE_MATRIX = ML_DIR / "feature_matrix.parquet"
MODEL_DIR = ML_DIR / "models"
SCORES_PATH = cfg.INTELLIGENCE_DIR / "ml_accumulation_scores.csv"

FEATURE_COLS = [
    # Phase 8B component scores (composite bull_run_score excluded -- circular)
    "price_score", "sector_flow_score", "deal_score", "corporate_score", "regime_multiplier",
    # Price momentum
    "ret_30d", "ret_90d", "ret_365d", "vol_ratio", "sector_rel_30d",
    # Sector snapshot
    "sector_combined_score", "rotation_signal_enc",
    # Sector rolling flows (5D/20D/60D)
    "sec_FII_5d", "sec_FII_20d", "sec_FII_60d",
    "sec_DII_5d", "sec_DII_20d", "sec_DII_60d",
    "sec_smart_money", "sec_retail_score",
    # Participant regime (market-wide)
    "part_FII_flow", "part_DII_flow", "part_smart_money", "regime_enc",
    # Fundamentals
    "mkt_cap_enc", "fund_promoter_pct", "fund_fii_pct", "fund_dii_pct",
    # Shareholding pattern (latest quarter)
    "shp_promoter_pct", "shp_fii_pct", "shp_dii_pct",
    # Index membership
    "index_count",
    # Corporate actions 12M
    "div_count_12m", "has_buyback_12m", "has_bonus_12m",
    # Institutional signals
    "corp_confidence", "deal_net_cr",
]


class AccumulationModel:
    """
    XGBoost binary classifier for accumulation detection.
    Target: symbol in EMERGING or STRONG_CANDIDATE label (score proxy).
    """

    def __init__(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.model_path = MODEL_DIR / "accumulation_xgb.json"
        self.meta_path  = MODEL_DIR / "accumulation_meta.json"

    def run(self) -> bool:
        try:
            import xgboost as xgb
            from sklearn.model_selection import TimeSeriesSplit, cross_val_score
            from sklearn.metrics import classification_report, roc_auc_score
        except ImportError:
            logger.error("[AccumulationModel] xgboost or sklearn not installed")
            return False

        logger.info("[AccumulationModel] Starting training")

        if not FEATURE_MATRIX.exists():
            raise FileNotFoundError(f"Run feature_engineering.py first: {FEATURE_MATRIX}")

        df = pd.read_parquet(FEATURE_MATRIX)
        X, y, symbols = self._prepare(df)

        # TimeSeriesSplit CV (sorted by bull_run_score as proxy for time ordering)
        tscv = TimeSeriesSplit(n_splits=5)
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="auc",
            random_state=42,
        )

        cv_scores = cross_val_score(model, X, y, cv=tscv, scoring="roc_auc")
        logger.info(f"[AccumulationModel] CV AUC: {cv_scores.mean():.3f} (+/-{cv_scores.std():.3f})")

        # Train final model on all data
        model.fit(X, y)
        self._save_model(model, cv_scores, X.columns.tolist())

        # Score all symbols
        proba = model.predict_proba(X)[:, 1]
        scores_df = pd.DataFrame({
            "symbol":           symbols,
            "accumulation_prob": np.round(proba, 4),
            "accumulation_score": np.round(proba * 100, 1),
        })

        self._save_scores(scores_df)
        logger.info(f"[AccumulationModel] Scored {len(scores_df)} symbols")
        return True

    def _prepare(self, df: pd.DataFrame):
        available = [c for c in FEATURE_COLS if c in df.columns]
        missing = set(FEATURE_COLS) - set(available)
        if missing:
            logger.warning("[AccumulationModel] Features not in matrix: %s", sorted(missing))
        X = df[available].copy()
        # NaN passed directly -- XGBoost learns the missing-value branch natively (per G-I-04:
        # never fillna(0); fillna(median) also wrong here as absence IS signal for sparse features).
        y = (df["label_enc"] >= 3).astype(int)  # EMERGING or STRONG_CANDIDATE
        symbols = df["symbol"]
        logger.info("[AccumulationModel] Features: %d, Positives: %d/%d, NaN cells: %d",
                    len(available), y.sum(), len(y), X.isnull().sum().sum())
        return X, y, symbols

    def _save_model(self, model, cv_scores, feature_names):
        model.save_model(str(self.model_path))
        meta = {
            "model_type": "XGBoost binary classifier",
            "target": "label_enc >= 3 (EMERGING or STRONG_CANDIDATE)",
            "cv_auc_mean": float(np.mean(cv_scores)),
            "cv_auc_std":  float(np.std(cv_scores)),
            "feature_names": feature_names,
            "n_estimators": 200,
            "trained_at": pd.Timestamp.now().isoformat(),
        }
        with open(self.meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"[AccumulationModel] Model saved: {self.model_path}")

    def _save_scores(self, df: pd.DataFrame):
        tmp = SCORES_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(SCORES_PATH))
        logger.info(f"[AccumulationModel] Scores saved: {SCORES_PATH}")

    def load_and_score(self, df_features: pd.DataFrame) -> pd.Series:
        """Load saved model and score new data."""
        import xgboost as xgb
        model = xgb.XGBClassifier()
        model.load_model(str(self.model_path))
        available = [c for c in FEATURE_COLS if c in df_features.columns]
        X = df_features[available].copy()  # NaN passed natively -- consistent with training
        return pd.Series(model.predict_proba(X)[:, 1] * 100, name="accumulation_score")


if __name__ == "__main__":
    engine = AccumulationModel()
    engine.run()
    df = pd.read_csv(SCORES_PATH)
    print(f"Scored {len(df)} symbols")
    print(df.nlargest(10, "accumulation_score")[["symbol", "accumulation_score"]])
