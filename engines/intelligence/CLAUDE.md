# ENGINES/INTELLIGENCE — CLAUDE CONTEXT

## PURPOSE
Output intelligence engines that sit above raw data and fetchers.
Consume processed/cached data and produce ranked, scored intelligence datasets.

## ACTIVE ENGINES

| File | Phase | Status | Output |
|------|-------|--------|--------|
| price_momentum_engine.py | 8A | COMPLETE | price_momentum.csv (2441 symbols) |
| bull_run_probability_engine.py | 8B | COMPLETE | bull_run_probability.csv + watchlist |

## STUB FILES — DO NOT EXTEND, DO NOT USE

| File | Lines | Issue |
|------|-------|-------|
| index_intelligence_engine_v2.py | 80 | V2 stub — no implementation |
| leadership_persistence_engine_v2.py | 30 | V2 stub — no implementation |

Production equivalents live at the ENGINE ROOT level:
- engines/index_intelligence_engine.py (221 lines) — USE THIS
- engines/sector_leadership_persistence_engine.py (316 lines) — USE THIS

## PHASE 8A — price_momentum_engine.py

Inputs: 7813 bhavcopy files (data/NSE/bhavcopy/equity/ + data/bhavcopy/equity/)
Output: data/intelligence/price_momentum.csv

Key design:
- Dual bhavcopy schema: pre-2020 (CLOSE/TOTTRDQTY) vs post-2020 (CLOSE_PRICE/TTL_TRD_QNTY)
  Handled via _load_bhav() which auto-detects schema
- vol_ratio capped at 50x to prevent outlier distortion
- sector_rel_30d = symbol 30D return minus sector median (same sector symbols)
- All metrics percentile-ranked 0-100 via _pct_rank() preserving NaN

Composite price_score:
  ret_30d_pct x 0.35 + ret_90d_pct x 0.25 + ret_365d_pct x 0.20
  + sector_rel_pct x 0.15 + vol_ratio_pct x 0.05

Results (2026-06-30):
- 2441 symbols, as_of_date 2026-06-10
- Price score range: 3 to 98
- Top: INOXINDIA 98, JNKINDIA 98

## PHASE 8B — bull_run_probability_engine.py

Inputs:
- data/intelligence/price_momentum.csv (8A)
- data/intelligence/sector_rotation_intelligence.csv (6C)
- data/intelligence/institutional_deal_signals.csv (7A)
- data/intelligence/corporate_confidence_scores.csv (7C)
- data/intelligence/participant_intelligence.csv (5C) -- regime source (preferred)
- data/historical/institutional/institutional_positioning_history.csv -- fallback regime

Outputs:
- data/intelligence/bull_run_probability.csv (2441 symbols)
- data/intelligence/bull_run_watchlist.csv (225 EMERGING symbols)

Factor weights:
  price_score: 30%
  sector_flow_score: 25%  (FII_flow_score rescaled: (score + 100) / 2)
  deal_score: 25%         (inst_net_value_cr percentile-ranked; 50=neutral)
  corporate_score: 20%    (confidence_score_12m clipped [-3,6] rescaled 0-100; 50=neutral)

Regime multipliers (from participant_intelligence.csv preferred):
  STRONG_ACCUMULATION: 1.20 | ACCUMULATION: 1.10 | NEUTRAL: 0.90
  DISTRIBUTION: 0.80 | STRONG_DISTRIBUTION: 0.70

Labels:
  >= 65 STRONG_CANDIDATE | >= 45 EMERGING | >= 30 WATCHLIST | >= 15 NEUTRAL | < 15 AVOID

Results (2026-06-30):
- Regime: NEUTRAL (x0.90), 2441 symbols, score range 14-62
- EMERGING: 225 | WATCHLIST: 1804 | NEUTRAL: 411 | AVOID: 1
- Top: ADANIENSOL 62, ADANIENT 57, GMRAIRPORT 56

## PLANNED ENGINES (Phases 12-16)

Phase 12 (ML Layer):
- engines/ml/feature_engineering.py
- engines/ml/accumulation_model.py (XGBoost binary)
- engines/ml/bull_run_model.py (LightGBM + XGBoost ensemble)
- engines/ml/sector_rotation_model.py (LightGBM multi-class)
- engines/ml/anomaly_detector.py (Isolation Forest)
- engines/ml/ml_scorer.py (daily inference)

Phase 13 (RAG):
- engines/ai/knowledge/ (FAISS + BM25 hybrid retrieval)

Phase 14 (Chatbot):
- engines/ai/chatbot/ (Claude API agents + tool registry)

Phase 15 (Financial Results):
- engines/fundamentals/financial_results_engine.py

Phase 16 (Management Intelligence):
- engines/management/ (promoter holding trends, announcement sentiment)
