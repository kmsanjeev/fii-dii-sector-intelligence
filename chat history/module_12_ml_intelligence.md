# Module 12 — ML Intelligence Layer
## Phase 12 Complete | 2026-06-30

---

## What Was Built

### engines/ml/ directory

engines/ml/
  __init__.py
  feature_engineering.py     <- Phase 12A: 24-feature snapshot matrix
  accumulation_model.py      <- Phase 12B: XGBoost binary classifier
  bull_run_model.py          <- Phase 12C: LightGBM + XGBoost ensemble
  ml_scorer.py               <- Phase 12D: daily inference orchestrator

### Phase 12A — feature_engineering.py

Builds 24-feature snapshot matrix from all 6 intelligence layers.
Output: data/intelligence/ml_features/feature_matrix.parquet + .csv

Feature groups:
  Phase 8B scores: bull_run_score, price_score, sector_flow_score, deal_score, corporate_score, regime_multiplier
  Price:           ret_30d, ret_90d, ret_365d, vol_ratio
  Sector:          sector_FII_flow, sector_combined_score, rotation_signal_enc (ordinal 0-5)
  Participant:     part_FII_flow, part_DII_flow, part_smart_money, regime_enc (ordinal 0-4)
  Corporate:       corp_confidence, deal_net_cr
  Encoded:         label_enc (0=AVOID to 4=STRONG_CANDIDATE)

Result: 2441 symbols x 24 features | Top: ADANIENSOL 61.79 price_score=92.69

### Phase 12B — accumulation_model.py

XGBoost binary classifier. Target: label_enc >= 3 (EMERGING or STRONG_CANDIDATE).
TimeSeriesSplit 5-fold CV. Saves model to data/intelligence/ml_features/models/accumulation_xgb.json.
Output: data/intelligence/ml_accumulation_scores.csv

Notes:
  - Current target is a score proxy (not actual forward price return)
  - CV AUC warnings expected for small fold sizes (snapshot not time-series data)
  - True look-ahead-safe training requires bhavcopy time-series target (Phase 12D future work)

Result: 2441 symbols scored | Top: ADANIENSOL 100.0

### Phase 12C — bull_run_model.py

LightGBM (0.6) + XGBoost (0.4) ensemble. Multi-class (0-4 label_enc).
Ordinal weighted score: AVOID=0, NEUTRAL=25, WATCHLIST=50, EMERGING=75, STRONG=100.
SHAP values computed for top 100 symbols.
Output: data/intelligence/ml_bull_run_scores.csv + ml_shap_values.csv

Saved models:
  data/intelligence/ml_features/models/bull_run_lgbm.txt
  data/intelligence/ml_features/models/bull_run_xgb.json

Result: 2441 symbols scored | Top: ADANIENSOL 75.00

### Phase 12D — ml_scorer.py

Daily orchestrator: rebuilds feature matrix -> loads saved models -> scores all symbols.
Output: data/intelligence/ml_scores_combined.csv (symbol, sector, bull_run_score, label,
        ml_bull_run_score, accumulation_score)

Usage: py -3.11 -m engines.ml.ml_scorer

Result: 2441 symbols | ADANIENSOL ml_score=75.0 accumulation=99.95

---

## Packages Installed

xgboost==3.2.0
lightgbm==4.6.0
scikit-learn==1.9.0
shap==0.51.0
pyarrow==24.0.0 (upgraded from 15.0.0 for numpy 2.x compatibility)
pandas==3.0.3 (upgraded from 2.2.0 by sklearn dependency)

---

## Known Limitations (by design)

1. Target is score-based proxy, not actual forward price return.
   True target (price_up_10pct_in_20d) requires bhavcopy time-series — future work.

2. CV on snapshot data is artificial (TimeSeriesSplit requires true time dimension).
   Full time-series training will be possible after Phase 15 (financial results) adds
   enough historical diversity.

3. ML scores currently close to rule-based scores because the model is trained on
   the same features that generate the rule-based scores. Divergence will appear
   when true forward targets are used.

---

## Next Steps

Phase 13 -- RAG Knowledge Base:
  py -3.11 -m pip install sentence-transformers rank-bm25 faiss-cpu
  engines/ai/knowledge/ (FAISS + BM25 hybrid retrieval)
