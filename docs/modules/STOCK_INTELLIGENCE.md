# STOCK INTELLIGENCE
## Capital Flow Intelligence Platform | Updated 2026-06-30

---

# Module Overview

Stock Intelligence is the final intelligence layer of the Capital Flow cascade.
Identifies individual stocks benefiting from participant flows, sector rotation,
corporate signals, and price momentum.

---

# Capital Flow Hierarchy

  Market -> Participant -> Sector -> Theme -> Stock -> Portfolio

---

# Completion Status: 40% (Phase 8 complete 2026-06-30)

---

# Completed Engines (Phase 8)

## Phase 8A — price_momentum_engine.py (COMPLETE)

File: engines/intelligence/price_momentum_engine.py
Output: data/intelligence/price_momentum.csv

Per-symbol price returns across 5 lookback windows from 7813 bhavcopy files.
Dual bhavcopy schema (pre/post-2020 column names handled via _load_bhav()).

Metrics per symbol:
- ret_30d, ret_60d, ret_90d, ret_365d (price returns in %)
- vol_ratio (latest volume / 20D average)
- sector_rel_30d (return minus sector median)
- ret_30d_pct, ret_90d_pct, ret_365d_pct, vol_ratio_pct, sector_rel_pct (0-100 percentile rank)
- price_score (composite: 30D 35% + 90D 25% + 365D 20% + sector_rel 15% + vol 5%)
- as_of_date (latest bhavcopy date)

Results (2026-06-30):
- 2441 symbols, as_of_date 2026-06-10
- 30D return range: -94.3% to +98.0%
- 1872 symbols with 365D data
- Price score range: 3 to 98
- Top: INOXINDIA 98, JNKINDIA 98 (CAPITAL_GOODS)

## Phase 8B — bull_run_probability_engine.py (COMPLETE)

File: engines/intelligence/bull_run_probability_engine.py
Outputs: data/intelligence/bull_run_probability.csv (2441 symbols)
         data/intelligence/bull_run_watchlist.csv (225 EMERGING symbols)

Multi-factor bull run probability score combining four intelligence layers.

Factor weights:
- price_score: 30% (from 8A, already 0-100)
- sector_flow_score: 25% (FII_flow_score from sector_rotation_intelligence.csv rescaled 0-100)
- deal_score: 25% (inst_net_value_cr percentile-ranked; 50=neutral for no-deal symbols)
- corporate_score: 20% (confidence_score_12m clipped [-3,6] rescaled 0-100; 50=neutral)

Market regime from participant_intelligence.csv (Phase 5C preferred):
- ACCUMULATION: x1.10 | NEUTRAL: x0.90 | DISTRIBUTION: x0.80

Labels:
- STRONG_CANDIDATE (>= 65)
- EMERGING (>= 45)
- WATCHLIST (>= 30)
- NEUTRAL (>= 15)
- AVOID (< 15)

Results (2026-06-30):
- 2441 symbols, regime NEUTRAL (x0.90)
- Score range: 14 to 62 (no STRONG_CANDIDATE in NEUTRAL regime)
- EMERGING: 225 | WATCHLIST: 1804 | NEUTRAL: 411 | AVOID: 1
- Top: ADANIENSOL 62, ADANIENT 57, GMRAIRPORT 56, CRAFTSMAN 54, EMCURE 54

---

# Remaining Engines (Phase 12 — ML Layer)

- Accumulation Detection Model (XGBoost binary, target: price_up_10pct_in_20d)
- Bull Run ML Model (LightGBM + XGBoost ensemble, replaces rule-based 8B)
- Relative Strength Engine (within-sector rank)
- Delivery Intelligence Engine (delivery volume analysis)
- F&O Intelligence Engine (put/call ratio, OI buildup per symbol)
- Anomaly Detector (Isolation Forest on flows)

---

# Intelligence Cascade Inputs (all LIVE)

| Source | File | Key field | Status |
|--------|------|-----------|--------|
| Price History | bhavcopy/equity/ (7813 files) | OHLCV | LIVE |
| Participant flows | participant_flow_scores.csv | FII_flow_score | LIVE 2026-06-29 |
| Sector attribution | sector_rotation_intelligence.csv | combined_score | LIVE 2026-06-02 |
| Institutional deals | institutional_deal_signals.csv | inst_net_value_cr | LIVE 2026-06-29 |
| Corporate confidence | corporate_confidence_scores.csv | confidence_score_12m | LIVE 2026-06-29 |
| Market regime | participant_intelligence.csv | Market_Regime | LIVE 2026-06-29 |
