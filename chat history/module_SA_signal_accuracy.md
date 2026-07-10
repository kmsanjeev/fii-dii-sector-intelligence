# MODULE SA — SIGNAL ACCURACY PLATFORM

Module-wise session log. Append-only per phased development protocol.

---

## Session 2026-07-10 — Phase SA-1 (COMPLETE)

Mandate: institutional-trader gap review focused on PREDICTION QUALITY +
a conviction investment screener + a bull-cycle alert.

### Gap review verdict (grounded in repo)
1. No signal efficacy measurement (no IC/decile/hit-rate anywhere)  << biggest
2. No score history retention (all intelligence CSVs overwritten daily)
3. Static hand-picked factor weights (8B: 30/25/25/20, never validated)
4. No liquidity gate in stock selection (screener_engine has zero ADV filters)
5. Weak CV in accumulation model (bull_run_score as time proxy) + label
   circularity (12B labels from 8B rules; 12C forward_return_model is the fix)

### D1 signal_efficacy_engine.py
- Point-in-time monthly snapshots, 36 months, NIFTY 500 from parquet cache
- Factors: ret_30d, ret_90d, prox_52w_high, dma_trend, vol_surge
- Forward 30/60/90d returns -> Spearman IC, decile spread, top-decile hit rate
- KEY FINDING: raw momentum IC NEGATIVE over this window (reversal regime);
  prox_52w_high the only consistently positive factor (IC +0.022 @90d, 62.5%
  positive months); dma_trend best decile spread @90d (+2.31%)
- Unmeasurable signals (deals/flows/ML) listed UNMEASURED honestly

### D2 score_snapshot_engine.py
- Daily append to history/scores_history.parquet: 17 cols x 2,735 symbols
- Same-date dedupe; makes ALL platform signals measurable after ~6 months
- GOTCHA: trade_conviction col is `score` not conviction_score; technical
  rsi col is `rsi` not rsi_14

### D3 conviction_screener_engine.py
- Weights from efficacy file: max(IC,0)*10 + max(spread,0)/100*4, floor 0.03;
  capped priors (ML .15, deals .10, sector flow .10) until measured
- HARD GATES: ADV >= 1cr/day, price >= 20, coverage, label != AVOID
  (2,441 -> 1,572 investable)
- Evidence (top 3 supports) + primary risk per stock; HIGH >= 70 (163),
  MEDIUM >= 58 (327)
- GOTCHA: prox_52w_high in technical_indicators.csv is PERCENT not fraction;
  bull_run + technical share close_now/trend_signal cols (merge collision)

### D4 P12_BULL_CYCLE alert
- HIGH tier + UPTREND/STRONG_UPTREND + prox in [-12,0]% + ML >= 60
- Top 5 by conviction, 72h cooldown; message carries evidence/risk/liquidity
- First run detected 5 setups

### API/GUI/Pipeline
- GET /api/research/conviction (+refresh), GET /api/research/efficacy
- ResearchPage: Conviction tab (tier filter, evidence + risk columns)
- Pipeline: SA1_score_snapshot + SA1_conviction_screener after R4_tca

### Verification
- Efficacy: 15 measured cells, 34 snapshots, sane ICs
- Screener: top picks 77-483 cr/day ADV, within 1-7% of 52w high, 0 HIGH-tier
  picks >50% below high; API 200s; tsc+build clean; suite 267/267
