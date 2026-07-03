"""
Forward Return Model -- Phase 12C
XGBoost binary classifier trained on REALIZED forward returns (not rule-based labels).

Target: is_up_15_45d  (stock rises 15%+ in 45 trading sessions ~2 months)
Features: rsi_14, macd_hist, bb_pct_b, adx_14, vs_dma_200, vol_ratio
          (same 6 features used in label_generator.py training data)

Training data: engines/ml/label_generator.py -> ml_forward_labels.csv
  ~53 bi-weekly reference dates x ~2300 symbols = ~120K rows (2024-2026)

Current scoring: pulls today's feature values from:
  - data/intelligence/technical_pattern_features.csv  (rsi_14, macd_hist, bb_pct_b, adx_14)
  - data/intelligence/technical_indicators.csv        (vs_dma_200)
  - data/intelligence/price_momentum.csv              (vol_ratio)

Output: data/intelligence/ml_forward_return_scores.csv

Run: py -3.11 -m engines.ml.forward_return_model
"""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ML_DIR        = cfg.INTELLIGENCE_DIR / "ml_features"
MODEL_DIR     = ML_DIR / "models"
LABELS_CSV    = cfg.INTELLIGENCE_DIR / "ml_forward_labels.csv"
SCORES_PATH   = cfg.INTELLIGENCE_DIR / "ml_forward_return_scores.csv"
MODEL_PATH    = MODEL_DIR / "forward_return_xgb.json"
META_PATH     = MODEL_DIR / "forward_return_meta.json"

# Inference sources (current values)
TECH_PATTERNS = cfg.INTELLIGENCE_DIR / "technical_pattern_features.csv"
TECH_IND      = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"
PRICE_MOM     = cfg.INTELLIGENCE_DIR / "price_momentum.csv"

FEATURE_COLS  = ["rsi_14", "macd_hist", "bb_pct_b", "adx_14", "vs_dma_200", "vol_ratio"]
TARGET_COL    = "is_up_15_45d"


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
class ForwardReturnModel:
    """
    XGBoost binary classifier for 15%-in-45-sessions forward return prediction.
    Trained on realized bhavcopy returns, not rule-based Phase 8B labels.
    TimeSeriesSplit CV respects temporal ordering (no look-ahead leakage).
    """

    def __init__(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> bool:
        try:
            import xgboost as xgb
            from sklearn.model_selection import TimeSeriesSplit, cross_val_score
        except ImportError:
            logger.error("[FwdReturnModel] xgboost / sklearn not installed")
            return False

        if not LABELS_CSV.exists():
            raise FileNotFoundError(f"Run label_generator.py first: {LABELS_CSV}")

        logger.info("[FwdReturnModel] Loading training data from %s", LABELS_CSV.name)
        labels = pd.read_csv(LABELS_CSV)
        labels["ref_date"] = pd.to_datetime(labels["ref_date"])

        X_train, y_train = self._prepare_training(labels)
        model, cv_scores = self._train(xgb, X_train, y_train)

        self._save_model(model, cv_scores)

        # Score current universe
        current_features = self._load_current_features()
        if current_features.empty:
            logger.error("[FwdReturnModel] No current features -- cannot score")
            return False

        self._score_and_save(model, current_features)
        return True

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def _prepare_training(self, labels: pd.DataFrame):
        # Keep only rows where all 6 features AND the primary label are present
        cols = FEATURE_COLS + [TARGET_COL]
        clean = labels[cols].dropna()

        # Sort by date (already in temporal order from generator) to respect TimeSeriesSplit
        # ref_date not in clean, so we rely on row order which is date-sorted from the generator
        X = clean[FEATURE_COLS]
        y = clean[TARGET_COL].astype(int)

        n_pos = int(y.sum())
        n_neg = len(y) - n_pos
        logger.info(
            "[FwdReturnModel] Training: %d rows | positive: %d (%.1f%%) | negative: %d",
            len(y), n_pos, n_pos / len(y) * 100, n_neg,
        )
        return X, y

    def _train(self, xgb, X, y):
        from sklearn.model_selection import TimeSeriesSplit, cross_val_score

        n_pos = int(y.sum())
        n_neg = len(y) - n_pos
        scale_pos = n_neg / n_pos if n_pos > 0 else 1.0

        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.04,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=round(scale_pos, 2),
            eval_metric="auc",
            random_state=42,
            verbosity=0,
        )

        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(model, X, y, cv=tscv, scoring="roc_auc")
        logger.info(
            "[FwdReturnModel] CV AUC: %.3f (+/- %.3f) | scale_pos_weight=%.2f",
            cv_scores.mean(), cv_scores.std(), scale_pos,
        )

        model.fit(X, y)
        return model, cv_scores

    def _save_model(self, model, cv_scores):
        model.save_model(str(MODEL_PATH))
        meta = {
            "model_type":    "XGBoost binary classifier",
            "target":        "is_up_15_45d (15% gain in 45 trading sessions)",
            "features":      FEATURE_COLS,
            "cv_auc_mean":   float(np.mean(cv_scores)),
            "cv_auc_std":    float(np.std(cv_scores)),
            "trained_at":    pd.Timestamp.now().isoformat(),
        }
        with open(META_PATH, "w") as f:
            json.dump(meta, f, indent=2)
        logger.info("[FwdReturnModel] Model saved -> %s", MODEL_PATH.name)

    # ------------------------------------------------------------------
    # Current scoring
    # ------------------------------------------------------------------
    def _load_current_features(self) -> pd.DataFrame:
        """Join today's feature values from existing Phase 12B/A outputs."""
        missing = [p for p in [TECH_PATTERNS, TECH_IND, PRICE_MOM] if not p.exists()]
        if missing:
            logger.warning("[FwdReturnModel] Missing sources: %s", [p.name for p in missing])

        frames = []

        if TECH_PATTERNS.exists():
            tp = pd.read_csv(
                TECH_PATTERNS,
                usecols=["symbol", "rsi_14", "macd_hist", "bb_pct_b", "adx_14"],
            )
            tp["symbol"] = tp["symbol"].str.strip().str.upper()
            frames.append(tp.set_index("symbol"))

        if TECH_IND.exists():
            ti = pd.read_csv(TECH_IND, usecols=["symbol", "vs_dma_200"])
            ti["symbol"] = ti["symbol"].str.strip().str.upper()
            frames.append(ti.set_index("symbol"))

        if PRICE_MOM.exists():
            pm = pd.read_csv(PRICE_MOM, usecols=["symbol", "vol_ratio"])
            pm["symbol"] = pm["symbol"].str.strip().str.upper()
            frames.append(pm.set_index("symbol"))

        if not frames:
            return pd.DataFrame()

        # Outer join on symbol index, then reset
        df = frames[0]
        for f in frames[1:]:
            df = df.join(f, how="outer")

        df = df.reset_index().rename(columns={"index": "symbol"})
        present = [c for c in FEATURE_COLS if c in df.columns]
        missing_feat = [c for c in FEATURE_COLS if c not in df.columns]
        if missing_feat:
            logger.warning("[FwdReturnModel] Feature columns missing from current data: %s", missing_feat)
            for c in missing_feat:
                df[c] = np.nan

        logger.info("[FwdReturnModel] Current features loaded: %d symbols", len(df))
        return df

    def _score_and_save(self, model, current: pd.DataFrame):
        import xgboost as xgb

        X_cur = current[FEATURE_COLS].copy()
        proba = model.predict_proba(X_cur)[:, 1]

        out = pd.DataFrame({
            "symbol":             current["symbol"],
            "forward_return_prob": np.round(proba, 4),
            "forward_return_score": np.round(proba * 100, 1),
        })

        tmp = SCORES_PATH.with_suffix(".tmp.csv")
        out.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(SCORES_PATH))

        scored = out.nlargest(10, "forward_return_score")[["symbol", "forward_return_score"]]
        logger.info("[FwdReturnModel] Scored %d symbols | Top 10:\n%s", len(out), scored.to_string(index=False))

    def load_and_score(self, df_features: pd.DataFrame) -> pd.Series:
        """Load saved model and score arbitrary feature DataFrame."""
        import xgboost as xgb
        m = xgb.XGBClassifier()
        m.load_model(str(MODEL_PATH))
        X = df_features[[c for c in FEATURE_COLS if c in df_features.columns]].copy()
        return pd.Series(m.predict_proba(X)[:, 1] * 100, name="forward_return_score")


if __name__ == "__main__":
    engine = ForwardReturnModel()
    ok = engine.run()
    if ok and SCORES_PATH.exists():
        df = pd.read_csv(SCORES_PATH)
        print(f"\nScored {len(df)} symbols")
        print(df.nlargest(10, "forward_return_score")[["symbol", "forward_return_score"]])
