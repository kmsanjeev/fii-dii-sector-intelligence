# PARTICIPANT INTELLIGENCE
## Capital Flow Intelligence Platform | Updated 2026-06-30

---

# Module Overview

Participant Intelligence is the foundational intelligence layer of the Capital Flow cascade.
Tracks capital flow by participant category (FII, DII, PRO, CLIENT) via F&O and cash market data.
Provides market regime detection, smart money signals, and conviction scoring for all downstream engines.

---

# Status: 100% COMPLETE (Phase 5, completed 2026-06-30)

---

# Capital Flow Framework

  Participant -> Sector -> Theme -> Stock -> Portfolio -> Execution

Participant Intelligence is the entry point of the entire cascade.

---

# Objective

Answer these questions from live data:
1. Who is buying? Who is selling?
2. Who has conviction?
3. Who is changing positioning?
4. Where is smart money flowing?
5. What is the current market regime?

---

# Participants Covered

| Label | Type | Signal |
|-------|------|--------|
| FII | Foreign Institutional Investors | Global capital allocation |
| DII | Domestic Institutional Investors | MF + Insurance deployment |
| PRO | Proprietary/Professional traders | Tactical positioning |
| CLIENT | Retail / non-institutional | Crowd behavior, sentiment |

---

# Completed Engines

## Phase 5A — participant_acquisition_engine.py (COMPLETE)

File: engines/participant/participant_acquisition_engine.py
Outputs:
- data/historical/institutional/institutional_positioning_history.csv (F&O OI + volume, 2016-present)
- data/historical/institutional/cash_market_flows_history.csv (cash flows, 2024-present)
- data/NSE/participant_recovery_queue.csv (failed dates for retry)

Data sources (nselib):
- derivatives.participant_wise_open_interest(date) — F&O OI by participant
- derivatives.participant_wise_trading_volume(date) — F&O volume by participant
- derivatives.fii_derivatives_statistics(date) — FII futures contracts
- capital_market.category_turnover_cash(date) — cash market by category

Results (2026-06-30):
- institutional_positioning_history.csv: 2581 rows, 2016-01-01 through 2026-06-29
- cash_market_flows_history.csv: 609 rows, through 2026-06-24
- 1 recovery entry (2026-02-19 cash market TZ error — non-critical)

## Phase 5B — participant_flow_engine.py (COMPLETE)

File: engines/participant/participant_flow_engine.py
Output: data/intelligence/participant_flow_scores.csv (2581 rows, 62 cols)

Computes rolling z-scores and normalized flow scores per participant category.
Key metrics: {P}_net_futs, {P}_flow_score, {P}_net_oi, {P}_flow_strength, {P}_flow_direction

Latest scores (2026-06-29):
- FII_flow_score: +10.9
- DII_flow_score: -4.5
- PRO_flow_score: -20.2
- CLIENT_flow_score: +9.4

## Phase 5C — participant_intelligence_engine.py (COMPLETE)

File: engines/participant/participant_intelligence_engine.py
Output: data/intelligence/participant_intelligence.csv (2581 rows, 21 cols)

Produces ensemble regime classification, conviction scores, smart money signals,
FII/DII divergence, and retail sentiment.

Latest results (2026-06-29):
- Market_Regime: NEUTRAL
- Smart_Money_Score: -4.7
- FII_conviction: 40%
- Regime source used by bull_run_probability_engine.py (Phase 8B)

---

# Key Formulas

F&O net position:
  Net = Future_Index_Long + Future_Stock_Long - Future_Index_Short - Future_Stock_Short
  (Options excluded — futures give cleaner directional signal)

Flow score (rolling z-score, clipped to [-3, +3]):
  z = (net_position - rolling_mean) / rolling_std

Market regime thresholds:
  STRONG_ACCUMULATION: FII z > 1.5 + DII z > 0.5
  ACCUMULATION: FII z > 0.5
  NEUTRAL: -0.5 < FII z < 0.5
  DISTRIBUTION: FII z < -0.5
  STRONG_DISTRIBUTION: FII z < -1.5

---

# Known Issues

- Cash market 2026-02-19: "Cannot mix tz-aware with tz-naive values" from NSE API
  Status: 1 entry in recovery_queue.csv, non-critical, fix in next incremental run

---

# Data Files

| File | Path | Status |
|------|------|--------|
| institutional_positioning_history.csv | data/historical/institutional/ | LIVE 2026-06-29 |
| cash_market_flows_history.csv | data/historical/institutional/ | LIVE 2026-06-24 |
| participant_flow_scores.csv | data/intelligence/ | LIVE 2026-06-29 |
| participant_intelligence.csv | data/intelligence/ | LIVE 2026-06-29 |

---

# Downstream Consumers

- sector_capital_flow_engine.py (6A) — uses participant flow scores
- bull_run_probability_engine.py (8B) — reads Market_Regime for regime multiplier
- alert_engine.py (Phase 9) — monitors regime changes for alerts
- MarketAgent (Phase 14) — get_market_regime() tool
