# CHANGELOG

## Project

Capital Flow Intelligence Platform

---

# Version 3.8.1

Phase 16B Fix -- AnnouncementFetcher bulk API rewrite

Date: 2026-06-30

Status: Completed

---

## Summary

Fixed `announcement_fetcher.py` to use nselib bulk `corporate_actions_for_equity(period='6M')`
instead of the non-existent `shareholding_patterns()` method. Added `_fetch_bulk()` and
`_parse_bulk()` methods. Fixed date normalization bug (premature truncation before regex).

## Results

- `board_announcements.csv`: 527 records, 471 symbols (DIVIDEND 446, BONUS 24, BUYBACK 19)
- `management_sentiment.csv`: 471 symbols scored (POSITIVE 435, NEUTRAL 36)
- Note: HoldingTrendEngine still defaults to STABLE (no nselib shareholding API available)

## Commit

`da5623f` -- Fix announcement_fetcher.py: add _fetch_bulk() using nselib bulk corporate_actions

---

# Version 3.8

Phase 16 -- Management Intelligence Layer

Date: 2026-06-30

Status: Completed

---

## Summary

Built the Management Intelligence Layer (Phase 16) in `engines/management/` -- 3 engines:
holding trend, announcement fetcher, and management sentiment scorer with optional Claude AI tone.

## Engines Built

| File | Purpose |
|------|---------|
| engines/management/holding_trend_engine.py | QoQ promoter/FII/DII delta + 7 conviction signals |
| engines/management/announcement_fetcher.py | Board meeting fetch + 8-type keyword classification |
| engines/management/management_sentiment_engine.py | Rule-based + Claude AI tone score (0-100) |

## Output Files

data/NSE/shareholding/holding_trends.csv -- promoter/FII/DII QoQ deltas, conviction_signal
data/NSE/shareholding/board_announcements.csv -- classified board announcements
data/NSE/shareholding/management_sentiment.csv -- management_score, management_label

---

# Version 3.7

Phase 15 -- Financial Results + Valuation Engine

Date: 2026-06-30

Status: Completed

---

## Summary

Built two financial fundamentals engines (Phase 15): quarterly results fetcher and
valuation scorer with P/E + ROE + growth composite.

## Engines Built

| File | Purpose |
|------|---------|
| engines/fundamentals/financial_results_engine.py | Quarterly P&L via nselib bulk + yfinance fallback |
| engines/fundamentals/valuation_engine.py | P/E, ROE, growth scoring -> valuation_label |

## Notes

NSE XBRL archive endpoint returns 404 intermittently. Engine handles gracefully.
Valuation scores compute from available data and skip missing symbols.

---

# Version 3.6

Phase 13-14 -- RAG Knowledge Base + AI Chatbot

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete AI intelligence layer: RAG knowledge base (Phase 13) with hybrid
BM25 + FAISS retrieval, and the AI chatbot (Phase 14) with Claude tool use + RAG context.

## Phase 13 -- RAG Knowledge Base

| File | Purpose |
|------|---------|
| engines/ai/knowledge/document_builder.py | 1091 text documents from 6 intelligence CSVs |
| engines/ai/knowledge/bm25_indexer.py | BM25Okapi sparse keyword index |
| engines/ai/knowledge/faiss_indexer.py | sentence-transformers dense index, 6 domain indexes |
| engines/ai/knowledge/retriever.py | RRF hybrid fusion, domain auto-detection |
| engines/ai/knowledge/index_updater.py | Daily rebuild pipeline |

## Phase 14 -- AI Chatbot

| File | Purpose |
|------|---------|
| engines/ai/chatbot/intent_router.py | Keyword intent detection (MARKET/SECTOR/STOCK/CORPORATE) |
| engines/ai/chatbot/tools/data_tools.py | 11 data access functions over intelligence CSVs |
| engines/ai/chatbot/tools/tool_registry.py | Anthropic API tool schemas + dispatch |
| engines/ai/chatbot/chat_engine.py | Multi-turn agentic loop with RAG injection |
| backend/routers/chat.py | POST /api/chat, in-memory session management |

## Packages Installed

sentence-transformers==5.6.0, faiss-cpu==1.14.3, rank-bm25==0.2.2, anthropic==0.113.0

---

# Version 3.5

Phase 12 -- ML Intelligence Layer

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete ML Intelligence Layer (Phase 12) in `engines/ml/` -- 4 engines:
feature engineering, accumulation model (XGBoost), bull run ensemble (LightGBM+XGBoost),
and daily inference scorer. Produces 2 new intelligence CSVs and saves trained model files.

---

## Engines Built

| File | Purpose |
|------|---------|
| engines/ml/feature_engineering.py | Builds 24-feature snapshot matrix from 6 intelligence CSVs |
| engines/ml/accumulation_model.py | XGBoost binary classifier, target: label_enc >= 3 |
| engines/ml/bull_run_model.py | LightGBM (0.6) + XGBoost (0.4) ensemble, multi-class |
| engines/ml/ml_scorer.py | Daily orchestrator: rebuild features + load models + score all |

## Output Files

| Output | Description |
|--------|-------------|
| data/intelligence/ml_features/feature_matrix.parquet | 2441 symbols x 24 features |
| data/intelligence/ml_accumulation_scores.csv | XGBoost binary scores (0-100) |
| data/intelligence/ml_bull_run_scores.csv | Ensemble scores + per-class probabilities |
| data/intelligence/ml_shap_values.csv | SHAP feature importance for top 100 symbols |
| data/intelligence/ml_scores_combined.csv | Daily combined output |
| data/intelligence/ml_features/models/ | Saved model files (XGBoost .json, LightGBM .txt) |

## Feature Groups (24 features)

Phase 8B scores: bull_run_score, price_score, sector_flow_score, deal_score,
                 corporate_score, regime_multiplier
Price:           ret_30d, ret_90d, ret_365d, vol_ratio
Sector:          sector_FII_flow, sector_combined_score, rotation_signal_enc (ordinal 0-5)
Participant:     part_FII_flow, part_DII_flow, part_smart_money, regime_enc (ordinal 0-4)
Corporate:       corp_confidence, deal_net_cr

## Packages Installed

xgboost==3.2.0, lightgbm==4.6.0, scikit-learn==1.9.0, shap==0.51.0
pyarrow upgraded 15.0.0 -> 24.0.0 (numpy 2.x compatibility)
pandas upgraded 2.2.0 -> 3.0.3 (sklearn dependency)

## Known Limitations (by design)

- Target is score-based proxy (not actual forward price return) until bhavcopy
  time-series target generation is available in a future phase
- TimeSeriesSplit CV on snapshot data is artificial; true CV requires time-series features
- ML scores are correlated with rule-based scores (same underlying features)

---

# Version 3.4

Phase 11 — React GUI

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete React GUI (Phase 11) in `frontend/` — 10 pages, 5 platform components,
TypeScript build clean, Vite proxy to FastAPI backend.

---

## Pages Built

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | / | Regime, flows, top sectors, EMERGING watchlist |
| Sectors | /sectors | All 29 sectors grouped by rotation_signal |
| Sector Detail | /sectors/:sector | Sector scores + top 10 stocks |
| Watchlist | /watchlist | Paginated 2441 symbols table with label filter |
| Stock Detail | /stocks/:symbol | 4-factor gauges, price performance, deal signals |
| Participant | /participant | FII/DII/PRO/CLIENT cards + 90D area chart |
| Corporate | /corporate | Deals table + upcoming catalysts |
| AI Chat | /chat | Phase 14 placeholder |
| Settings | /settings | Freshness, alert config, platform info |

## Platform Components

ScoreGauge, CapFlowBadge, FlowCard, RegimeBanner, SectorTile, AppShell

## Tech Stack

React 18 + TypeScript + Vite + Tailwind CSS + Zustand + TanStack Query + Recharts

---

# Version 3.3

Phase 10 — FastAPI Backend

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete FastAPI Backend (Phase 10) in `backend/` — REST API serving all 11
intelligence CSVs via 16 endpoints, in-memory data loader with 60min auto-reload,
and WebSocket live ticker.

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app entry point, CORS, startup, /health |
| `backend/services/data_loader.py` | Thread-safe CSV cache, 60min background reload |
| `backend/routers/market.py` | /api/market/regime + freshness |
| `backend/routers/participant.py` | /api/participant/latest + history |
| `backend/routers/sectors.py` | /api/sectors (all 29) + history + detail |
| `backend/routers/stocks.py` | /api/stocks (2441) + watchlist + detail + momentum |
| `backend/routers/corporate.py` | /api/corporate/deals + catalysts + confidence + events |
| `backend/ws/live_ticker.py` | WebSocket /ws/live (regime + sectors every 30s) |

---

## Test Results (2026-06-30)

16/16 endpoints PASS. Key data:
- NEUTRAL regime | FII +10.91 | DII -4.52
- 29 sectors | 2441 symbols | 225 EMERGING
- 12 upcoming catalysts | 1111 corporate confidence scores

---

## Packages Added

- fastapi==0.138.2
- uvicorn[standard] (watchfiles, httptools)

---

# Version 3.2

Phase 9 — Alert System

Date: 2026-06-30

Status: Completed

---

## Summary

Built the complete Alert System (Phase 9) in `alerts/` — five files covering signal
evaluation, cooldown tracking, Telegram delivery, daily digest, and APScheduler orchestration.

---

## Files Created

| File | Phase | Purpose |
|------|-------|---------|
| `alerts/alert_engine.py` | 9A | Evaluates 6 intelligence CSVs, emits 7 alert types |
| `alerts/alert_store.py` | 9B | Cooldown tracking, dedup, atomic JSON state |
| `alerts/telegram_bot.py` | 9C | Telegram Bot API delivery, HTML formatting |
| `alerts/daily_digest.py` | 9D | 18:30 IST daily intelligence summary |
| `alerts/alert_scheduler.py` | 9E | APScheduler: digest + post-market checks |
| `docs/decisions/ADR-021-Alert-System-Architecture.md` | — | Architecture decision record |

---

## Alert Types (Priority Order)

| Priority | Type | Cooldown | Source |
|----------|------|---------|--------|
| P1 | REGIME_CHANGE | None | participant_intelligence.csv |
| P2 | STRONG_CANDIDATE | 72h | bull_run_probability.csv |
| P3 | SECTOR_ROTATION | 48h | sector_rotation_intelligence.csv |
| P4 | INSTITUTIONAL_DEAL | 48h | institutional_deal_signals.csv |
| P5 | CORPORATE_CONFIDENCE | 48h | corporate_confidence_scores.csv |
| P6 | PARTICIPANT_DIVERGENCE | 48h | participant_intelligence.csv |
| P7 | DAILY_DIGEST | 24h | all layers |

---

## Test Results (2026-06-30)

- alert_engine: 118 alerts on first run (P1 regime change + P3/P4/P5/P6)
- alert_store: cooldown filter verified
- daily_digest: 690-char HTML digest with 5 sections
- alert_scheduler: APScheduler imports and jobs verified

---

## Packages Added

- APScheduler==3.11.3
- python-telegram-bot==21.11.1

---

# Version 3.1

Phase 8 — Bull Run Probability Engine (8A / 8B)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the Bull Run Probability Engine in `engines/intelligence/` — two engines that combine
all previously built intelligence layers into a per-stock bull run probability score.

---

## Engines Created

| File | Phase | Output |
|------|-------|--------|
| `engines/intelligence/price_momentum_engine.py` | 8A | `data/intelligence/price_momentum.csv` |
| `engines/intelligence/bull_run_probability_engine.py` | 8B | `data/intelligence/bull_run_probability.csv` + watchlist |

---

## Intelligence Architecture

### Price Momentum Score (Phase 8A)
- Reads 5 reference bhavcopy dates: latest, 30D, 60D, 90D, 365D ago
- Reads 22 bhavcopy files for 20D volume average
- Per-symbol: ret_30d, ret_60d, ret_90d, ret_365d, vol_ratio, sector_rel_30d
- All metrics percentile-ranked (0-100) across 2441-symbol universe
- Composite price_score: ret_30d (35%) + ret_90d (25%) + ret_365d (20%) + sector_rel (15%) + vol (5%)
- Handles dual bhavcopy schema (pre/post-2020 column names)
- 2441 symbols scored, as_of_date: 2026-06-10

### Bull Run Probability Score (Phase 8B)
- 4-factor weighted combination:
  - Price Momentum Score: 30% (from 8A, already 0-100)
  - Sector Capital Flow Score: 25% (FII_flow_score from sector_rotation_intelligence.csv rescaled 0-100)
  - Institutional Deal Score: 25% (inst_net_value_cr percentile-ranked; neutral 50 if no deal data)
  - Corporate Confidence Score: 20% (confidence_score_12m clipped [-3,6] rescaled 0-100)
- Market Regime Multiplier from institutional_positioning_history.csv:
  - ACCUMULATION: ×1.10  DISTRIBUTION: ×0.80  others: ×0.90
- Final score clipped to [0, 100]

### 2026-06-30 Results
- 2441 symbols scored
- Regime: DISTRIBUTION (×0.80 multiplier)
- Score range: 12.3 to 54.9 (DISTRIBUTION caps ceiling below 65)
- EMERGING: 16 symbols (max possible in DISTRIBUTION regime)
- WATCHLIST: 1599 symbols
- NEUTRAL: 824 symbols
- AVOID: 2 symbols
- Top candidates: ADANIENSOL (55), ADANIENT (51), GMRAIRPORT (50), CRAFTSMAN (48), EMCURE (48)

---

# Version 3.0

Phase 7 — Corporate Intelligence Layer (7A / 7B / 7C)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the Corporate Intelligence Layer (`engines/corporate/`) per ADR-020 Domain 3+4.
Three engines provide stock-level intelligence that feeds into the Bull Run Probability
engine (Phase 8): institutional deal signals, upcoming catalysts, and corporate confidence scores.

---

## Deliverables

### Engines (engines/corporate/)
- `block_bulk_deal_engine.py` (7A) — incremental downloader for NSE block/bulk deals.
  Classifies each client as FII/MF/INSURANCE/PROMOTER/RETAIL via keyword matching.
  Computes 30D net institutional buying per symbol → deal_signal.
- `corporate_event_calendar_engine.py` (7B) — downloads event calendar (board meetings,
  results dates) from 2023-01-01 to present. Identifies upcoming catalysts in next 60D,
  prioritized by event type × sector_rotation_intelligence combined score.
- `corporate_action_intelligence_engine.py` (7C) — processes all 40,517 existing corporate
  actions (1999-2026). Classifies DIVIDEND/BONUS/SPLIT/BUYBACK/RIGHTS/MERGER/AGM_EGM.
  Extracts amounts/ratios. Computes rolling 12M corporate confidence score per symbol.

### New Data Files
- `data/intelligence/block_bulk_deals.csv` — 12,467 rows (6M block/bulk deal history)
- `data/intelligence/institutional_deal_signals.csv` — 361 symbols, 30D net signals
- `data/intelligence/event_calendar.csv` — 33,839 rows (2023-2026)
- `data/intelligence/upcoming_catalysts.csv` — next 60D events, priority scored
- `data/intelligence/corporate_action_signals.csv` — 40,517 classified actions (1999-2026)
- `data/intelligence/corporate_confidence_scores.csv` — 1,111 symbols, 12M rolling score

---

## Design Decisions

- Financial results via nselib XBRL endpoint returns 404 — skipped for this phase
- Management Intelligence (NLP, transcripts) — deferred to Phase 8+ (requires AI pipeline)
- Shareholding patterns — deferred (data not yet acquired)
- Participant classification: keyword matching on client name (heuristic, good enough for FII/MF detection)
- Corporate confidence weights: BUYBACK +3 > BONUS +2 > SPLIT +1 > DIVIDEND +0.5 > RIGHTS -0.5
- Catalyst score = purpose_priority × 10 + sector_combined_score / 10 (blends event type + sector flow)

---

# Version 2.9

Phase 6 — Sector Rotation + Capital Flow Engines (6A / 6B / 6C)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built three sector-level capital flow engines that weight-allocate total participant F&O flows
to each of the 29 platform sectors using daily bhavcopy turnover weights, then derive rolling
flow scores, z-score normalisation, rotation signals, and a combined price + flow intelligence snapshot.

---

## Deliverables

### Engines (engines/participant/)
- `sector_capital_flow_engine.py` (6A) — reads 7813 bhavcopy files (2016-2026, dual schema support
  for pre-2020 and post-2020 column formats), weight-allocates FII/DII/PRO/CLIENT OI and Volume flows
  to 29 platform sectors by daily turnover weight. Incremental.
- `sector_flow_score_engine.py` (6B) — OI delta, rolling 5D/20D/60D sums, z-score flow scores
  (-100..+100) per sector per participant. Full rebuild.
- `sector_rotation_intelligence_engine.py` (6C) — combines flow scores + NSE index price momentum
  (from Phase 3 index_strength.csv) into rotation signal, capital flow alignment, and combined rank.
  Outputs both a latest snapshot and a full time-series.

### New Data Files
- `data/intelligence/sector_capital_flows.csv` — 74,269 rows, 29 sectors x 2561 dates (2016-2026)
- `data/intelligence/sector_flow_scores.csv` — 74,269 rows, 35 cols per sector per date
- `data/intelligence/sector_rotation_intelligence.csv` — 29-row snapshot (latest date)
- `data/intelligence/sector_rotation_history.csv` — full time-series for GUI charting

---

## Design Decisions

- Turnover weight allocation: `sector_weight = sector_turnover / total_market_turnover` (close x qty / 1e7 crores)
- Dual bhavcopy schema: pre-2020 uses CLOSE/TOTTRDQTY columns; post-2020 uses CLOSE_PRICE/TTL_TRD_QNTY
- Z-score: 252-day rolling window, clipped to +/-3, scaled to +/-100 (consistent with Phase 5B)
- Combined score: 60% participant flow score (leading) + 40% price momentum (confirming)
- Rotation quadrants: STRONG_ACCUMULATION (flow+, price+), EARLY_ROTATION (flow+, price-),
  PRICE_LED (flow-, price+), DISTRIBUTION (flow-, price-)
- NSE index -> platform sector: static mapping covering 32 NSE indices to 29 platform sectors

---

# Version 2.8

Phase 5 — Participant Intelligence Layer (5A / 5B / 5C)

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the Participant Intelligence Layer (`engines/participant/`) per ADR-016.
Three engines track capital flow by participant category (FII, DII, PRO, CLIENT)
across F&O and cash market channels.

---

## Deliverables

### Engines (engines/participant/)
- `participant_acquisition_engine.py` (5A) — incremental downloader for F&O OI/Volume +
  new cash market flows history; fills gap 2026-06-03 to today; extends cash history from 2024-01-01
- `participant_flow_engine.py` (5B) — OI delta, rolling sums (5D/20D/60D), normalized
  z-score flow scores (−100..+100) per participant; full rebuild on run
- `participant_intelligence_engine.py` (5C) — conviction (% positive days in 20D window),
  Smart Money Score, Retail Score, divergence signals, Market Opportunity, ensemble Market Regime

### New Data Files
- `data/historical/institutional/cash_market_flows_history.csv` — cash flows by FPI/MF/Insurance/Retail (2024+)
- `data/intelligence/participant_flow_scores.csv` — rolling metrics + normalized scores
- `data/intelligence/participant_intelligence.csv` — conviction, divergence, smart money, regime

### Module Context
- `engines/participant/CLAUDE.md` — data sources, schemas, F&O net formula, column quirks
- `engines/participant/__init__.py` — package init

---

## Design Decisions

- F&O net position = futures only (Index + Stock Long − Short); options excluded for cleaner signal
- Score normalisation: rolling z-score over 252-day window, clipped ±3, scaled to ±100
- Market Regime ensemble: Smart Money 50%, DII 25%, Cash Institutional 25%
- Market Opportunity = max(0, Smart) × max(0, −Retail) / 100 — fires when smart money accumulates AND retail sells
- Backward compatible with Phase 7 institutional_positioning_history.csv (21-column schema preserved)

---

---

# Purpose

This document records all major project milestones, architecture decisions, strategic changes, documentation updates, and development achievements.

The changelog serves as the historical record of the platform's evolution.

---

# Versioning Philosophy

The platform follows milestone-based versioning.

Major versions are created when:

* Architecture changes significantly
* New intelligence layers are introduced
* Strategic direction changes
* Major modules are completed

---

# Version 2.7

Phase 4D — NSE Constituents Engine V1

Date:

2026-06-30

Status:

Completed

---

## Summary

Built the NSE index constituent downloader using `nsearchives.nseindia.com/content/indices/`
(open endpoint, no auth required). Downloads 30 NSE indices in one run — 12 broad-market
cap-tier indices + 18 sector/theme/strategy indices. Produces one constituent CSV per index
plus a master `index_membership.csv` mapping each symbol to all its indices with sector hints.

---

## Deliverables

### Engine
- `engines/foundation/nse_constituents_engine_v1.py` — complete rewrite (class-based, all guardrails)

### Outputs (data/NSE/indices/)
- `nifty_50_constituents.csv` through `nifty_smallcap_250_constituents.csv` — 30 files, one per index
- `index_membership.csv` — 506 unique symbols; columns: symbol, index_names, sector_hints, dominant_sector_hint
- `reports/download_registry.csv` — status per index (30 SUCCESS, 0 FAILED)
- `reports/constituents_recovery_queue.csv` — empty (all succeeded)

### Index Coverage (30 indices, 2519 constituent rows total)
Broad market (12): NIFTY 50, NEXT 50, 100, 200, 500, MIDCAP 50/100/150, SMALLCAP 100/250, LARGEMIDCAP 250, MIDSMALLCAP 400
Sector (14): AUTO, PHARMA, IT, METAL, FMCG, MEDIA, REALTY, BANK, PSU BANK, HEALTHCARE, OIL & GAS, ENERGY, FINANCIAL SERVICES 25/50, CONSUMER DURABLES
Strategy/PSU (4): COMMODITIES, MNC, CPSE, PSE

### Key Verifications
- TCS → dominant_sector_hint=IT ✅
- HDFCBANK → dominant_sector_hint=BANKING ✅
- MARUTI → dominant_sector_hint=AUTO ✅
- ONGC → dominant_sector_hint=ENERGY ✅
- SUNPHARMA → sector_hints=HEALTHCARE|PHARMA ✅
- All 30 downloads: HTTP 200, schema valid, EQ series filter applied

### Not Available on nsearchives (for future work)
NIFTY FINANCIAL SERVICES (main), NIFTY PRIVATE BANK, NIFTY CHEMICALS, NIFTY CEMENT,
NIFTY INFRASTRUCTURE, NIFTY TOTAL MARKET, NIFTY INDIA DEFENCE, NIFTY EV,
NIFTY INDIA DIGITAL, NIFTY INDIA MANUFACTURING, NIFTY TRANSPORTATION & LOGISTICS

---

# Version 2.6

Phase 4C — Classification Engine V4 Completion

Date:

2026-06-30

Status:

Completed

---

## Summary

Rewrote `classification_engine_v4.py` as a proper 5-level hierarchical classifier using
industry_master as primary lookup. Applied symbol-level corrections for all 71 previously
OTHER symbols, reducing OTHER from 71 to 10 (genuinely miscellaneous businesses).
Coverage improved from 96.7% → 99.53% non-OTHER. Also writes `company_classification_v4.csv`
with source tracking (INDUSTRY_MASTER / SYMBOL_CORRECTION / KEYWORD_MATCH / MANUAL_OVERRIDE).

---

## Deliverables

### Engine
- `engines/fundamentals/classification_engine_v4.py` — complete rewrite (hierarchical, 5 levels, all guardrails)

### Outputs
- `data/reference/company_classification_v4.csv` — 2123 rows, 7 cols (with SOURCE tracking)
- `data/NSE/equity_master/company_fundamentals_master.csv` — UPDATED (99.53% coverage)
- `data/NSE/equity_master/classification_coverage_report.csv` — metrics snapshot
- `data/NSE/equity_master/classification_review_queue.csv` — 10 symbols needing manual review
- `data/NSE/equity_master/classification_sector_counts.csv` — per-sector counts

### Key Corrections in SYMBOL_CORRECTIONS Dict (60 symbols reclassified from OTHER)
- ICICIAMC / NAM-INDIA / UTIAMC → AMC / FINANCIALISATION
- SUPRAJIT / MAJESAUT / PTL → AUTO / EV_TRANSITION
- HARSHA / INTLCONV / SANGHVIMOV / DYNAMATECH / OMNI / TEXINFRA → CAPITAL_GOODS
- INDIQUBE / NESCO / NIRLON / SMARTWORKS / EFCIL / HEMIPROP / WEWORK / MERCANTILE → REALTY
- CYBERTECH / GENESYS / SASKEN / DSSL / REDINGTON → IT / DIGITAL_INDIA
- SPCENET → TELECOM / DIGITAL_INDIA
- DEVYANI / ADVENTHTL → HOSPITALITY / PREMIUMISATION
- GICL / TARACHAND / TVSSCS → LOGISTICS / LOGISTICS_MODERNISATION
- DBSTOCKBRO / ALANKIT / CMSINFO / RADIANTCMS / PRUDENT / ICDSLTD → FINANCIAL_SERVICES
- SOUTHWEST / KOTYARK → ENERGY; SHIVAUM / GOYALALUM / MSTCLTD → METAL
- RUCHINFRA / ELITECON → INFRASTRUCTURE; VIKASLIFE / FLEXITUFF / RUBFILA / SICAGEN / IWP → CHEMICALS
- KOTHARIPRO / VINCOFE / GOLDIAM → FMCG; UMAEXPORTS → AGRICULTURE; LAHOTIOV → TEXTILES
- TOUCHWOOD → MEDIA; ACEINTEG → DEFENCE; CNL → RETAIL; BLUSPRING → POWER
- STCINDIA / MMTC → DIVERSIFIED / PSU_REVIVAL

### Remaining OTHER (10 — genuinely miscellaneous, no dominant sector)
AARVI, AKG, DEVX, KAPSTON, KRYSTAL, LANDSMILL, METROGLOBL, QUESS, SIS, UDS
(staffing / facility management / export trading / startup incubator)

### Final State after Phase 4C
- Total symbols: 2,123
- Classified (non-OTHER): 2,113 (99.53%)
- OTHER: 10 (0.47%)
- UNCLASSIFIED: 0

---

# Version 2.5

Phase 4B — Industry Master Engine

Date:

2026-06-29

Status:

Completed

---

## Summary

Built the authoritative industry_nse → sector_platform + theme_platform lookup table covering
all 183 unique NSE industry classifications across 2123 symbols. Immediately applied the master
back to improve company_fundamentals_master.csv to 96.7% sector coverage and 100% theme coverage.

---

## Deliverables

### Engine
- `engines/fundamentals/industry_master_engine.py` — complete rewrite (class-based, all guardrails)

### Outputs
- `data/reference/mapping/industry_master.csv` — 183 rows, 10 columns (authoritative lookup table)
- `data/NSE/equity_master/company_fundamentals_master.csv` — UPDATED (96.7% sector, 100% theme)

### Bug Fixes (in engine development)
- `_manual_theme` column NaN propagation — fixed by initializing to "" before loop
- `float('nan')` is truthy in Python — fixed with `pd.notna()` guard

### Industry Groups (10 groups across 183 industries)
- MANUFACTURING: 59 industries
- CONSUMER: 31 industries
- INFRASTRUCTURE_ENERGY: 30 industries
- FINANCIAL_SERVICES: 20 industries
- TECHNOLOGY: 19 industries
- HEALTHCARE: 10 industries
- REAL_ESTATE: 6 industries
- OTHER: 5 industries (DISTRIBUTORS, DIVERSIFIED COMMERCIAL SERVICES, etc.)
- AGRICULTURE: 2 industries
- DIVERSIFIED: 1 industry

### Key Corrections Applied
- DIVERSIFIED COMMERCIAL SERVICES (37 cos): IT → OTHER (staffing/facility mgmt ≠ IT)
- COAL (3 cos): POWER → ENERGY with PSU_REVIVAL theme
- PACKAGING (31 cos): OTHER → CHEMICALS with CHINA_PLUS_ONE theme
- PAPER AND PAPER PRODUCTS (21 cos): OTHER → CHEMICALS
- FURNITURE HOME FURNISHING (10 cos): OTHER → REALTY
- HOUSEWARE (4 cos): OTHER → FMCG
- AMUSEMENT PARKS (3 cos): OTHER → HOSPITALITY

### Final State after Phase 4B
- ISIN: 100%
- Sector classified (non-OTHER): 96.7%
- Theme populated: 96.3% (strings only; 3.7% = OTHER sector → no theme, by design)
- No industries in review queue (all 183 at high confidence)

---

# Version 2.4

Phase 4A — Company Fundamentals Master Engine

Date:

2026-06-29

Status:

Completed

---

## Summary

Built the authoritative company master for all 2123 EQ active symbols.
Passes all 4 spec success criteria. Resolves the ADANIPORTS→LOGISTICS classification bug.
Output at `data/NSE/equity_master/company_fundamentals_master.csv`.

---

## Deliverables

### Engine
- `engines/fundamentals/company_fundamentals_master_engine.py` — complete rewrite (class-based, all guardrails)

### Outputs
- `data/NSE/equity_master/company_fundamentals_master.csv` — 2123 rows, 15 columns
- `data/NSE/equity_master/fundamentals_review_queue.csv` — 103 symbols for manual review
- `data/NSE/equity_master/fundamentals_coverage_report.csv` — coverage metrics

### Supporting Data
- `data/reference/mapping/manual_override.csv` — created with 8 known misclassification corrections

### Success Criteria (all PASS)
- industry_nse populated: 100% (spec: 95%+)
- ISIN null count: 0 (spec: ZERO)
- listing_date null count: 0 (spec: ZERO)
- ADANIPORTS sector: LOGISTICS (spec: LOGISTICS/PORTS not AEROSPACE)

### Coverage
- ISIN: 100%
- Sector classified (non-OTHER): 95.1%
- Theme classified: 94.8%
- Market cap known: 100%

### Key Fixes Applied
- ADANIPORTS: CHEMICALS (Screener error) → LOGISTICS via manual_override.csv
- ONGC: AGRI (Screener error) → ENERGY via manual_override.csv
- TCS + consulting firms: PROFESSIONAL_SERVICES → IT via SECTOR_NORMALIZE fix
- Packaging companies: mapped to CHEMICALS (packaging materials)
- Education companies: mapped to HEALTHCARE (theme alignment)

### Architecture
- SECTOR_NORMALIZE dict: 44 mappings (28 canonical + 16 legacy/alternate names)
- SECTOR_TO_THEME dict: 25 sector → theme mappings (basic; Phase 4B refines via industry_master)
- manual_override.csv applied last — immutable (G-C-02)
- All guardrails: atomic write, schema validation, empty df guard, universe size check

---

# Version 2.3

ML / AI / Chatbot Architecture — Modules 14, 15, 16 Added

Date:

2026-06-29

Status:

Completed

---

## Summary

Designed and documented ML Intelligence, AI Knowledge Base (RAG), and Chatbot Platform layers.
Added 3 new modules (14, 15, 16) to MODULE_REGISTRY. Platform now has a clear roadmap from raw
NSE data through ML scoring → RAG retrieval → conversational AI interface. Claude API
(claude-sonnet-4-6) selected as the LLM backbone. Chat history restructured to module-wise append files.

---

## Deliverables

### Architecture Document
- `docs/architecture/ML_AI_CHATBOT_ARCHITECTURE.md` — full ML/AI/Chatbot spec (8 sections)

### New Modules
- Module 14: ML Intelligence Layer (0%, Planned) — XGBoost/LightGBM accumulation, sector rotation, bull run, anomaly, NLP classification
- Module 15: AI Knowledge Base / RAG (0%, Planned) — FAISS + BM25 hybrid retrieval over all intelligence outputs
- Module 16: Chatbot Platform (0%, Planned) — 7 agents, tool registry, WebSocket, React chat UI

### Module Updates
- Module 07 (AI Platform): Architecture expanded with full Claude API integration spec

### Process Changes
- Chat history restructured to module-wise append files (`chat history/module_NN_<name>.md`)
- Old session-based files deprecated — all new entries append to module files

### ADR References
- ADR-021: ML Intelligence Layer
- ADR-022: RAG Knowledge Base
- ADR-023: Chatbot / Conversational AI

---

## Build Dependencies (ML/AI/Chatbot cannot start until)

1. Phase 4A (Company Fundamentals Master Engine) — unblocks ML-1 Feature Engineering
2. Phase 3B outputs (intelligence CSVs) — unblocks RAG-1 (available now for partial indexing)
3. Phase 6 (Sector Rotation Engines) — unblocks ML-4 Sector Rotation Model

---

# Version 2.2

GUI Architecture Planning — React + FastAPI Implementation Plan

Date:

2026-06-29

Status:

Completed

---

## Summary

Designed and documented the full React-based GUI for the Capital Flow Intelligence Platform.
Created `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` covering technology stack, design system,
13 pages, 13 build phases, FastAPI backend contract, state management, and IST-aware utilities.
Module 08 (GUI Platform) advances from 10% to 25%.

---

## Deliverables

### Architecture Document
- `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` — 15-section complete build specification

### Technology Decisions (Locked)
- Frontend: React 18 + TypeScript + Vite
- Styling: Tailwind CSS + CSS Variables (dark terminal theme)
- Charts: Recharts (heatmaps/flows) + TradingView Lightweight Charts (OHLCV)
- Server State: TanStack Query v5
- Client State: Zustand
- Routing: React Router v6
- Backend: FastAPI + Uvicorn (already in requirements.txt)
- Real-time: WebSocket — live flow ticker during market hours only

### Design System (Defined)
- Dark terminal palette (#0A0D14 background)
- Participant colors: FII=Blue, DII=Indigo, PRO=Amber, CLIENT=Pink
- Score gradient: Red (0-30) → Amber (30-60) → Green (60-80) → Emerald (80-100)
- 3-Second Rule: market regime + FII net + top sector visible on landing

### Pages Designed (13 total)
Dashboard, Market, Sectors, SectorDetail, Themes, ThemeDetail,
Stocks (screener), StockDetail, Portfolio, Research, AI Assistant, Reports, Settings

### Build Phases Defined (GUI-1 through GUI-13)
GUI-1: AppShell → GUI-4: FastAPI data wiring (needs Phase 4A) → GUI-9: AI Assistant → GUI-13: Auth

### Key Components Specified
- `CapitalFlowCascade` — Sankey: Market → Sector → Theme → Stock
- `SectorHeatmap` — Recharts Treemap (size=market cap, color=flow score)
- `FlowCard` — FII/DII/PRO/CLIENT buy/sell/net with 7-day sparkline
- `OhlcvChart` — TradingView LC with delivery % + FII flow overlay panes

### FastAPI Contract
- 14 REST endpoints + 1 WebSocket (`/ws/live-flow`)
- Standard envelope: `{ status, data, meta: { generated_at, data_as_of, cache_hit } }`

### Session Protocol
- `chat history/session_2026_06_29_gui_plan.md` saved
- Memory updated in `memory/project_fii_dii.md`

---

# Version 2.1

Phase 3B: Guardrail Utility Library + Complete Test Suite

Date:

2026-06-29

Status:

Completed

---

## Summary

Implemented the complete guardrail utility library (`engines/common/guardrails.py`) with 55
functions covering all 12 guardrail sections, paired with a full pytest test suite across 16 test
files (~400 test cases). Introduced phased development protocol: every phase ends with a session
log saved to `chat history/`, memory update, and CHANGELOG entry.

---

## Deliverables

### Guardrail Library
- `engines/common/guardrails.py` — 55 utility functions, all logging at DEBUG level
- All 12 guardrail sections covered (Data, API, Symbol, Price, Classification, Corporate Actions,
  Intelligence, Financial Results, Trading Calendar, Institutional, System, Performance)

### Test Infrastructure
- `pytest.ini` — DEBUG logging to `tests/logs/pytest_debug.log`
- `tests/conftest.py` — 10 shared fixtures + autouse `log_test_boundaries`
- `requirements.txt` — added pytest>=8.0.0 and pytest-mock>=3.0.0

### Guardrail Test Files (tests/guardrails/)
12 files covering G-D-01 through G-PERF-04 (all 55 rules)

### Edge Case Test Files (tests/edge_cases/)
4 files covering India-specific edge cases: mergers/IPOs, circuit breakers,
PSU/holding co classification, institutional T+1 lag, Budget Day, F&O expiry

### Supporting Files
- `tests/CLAUDE.md` — test directory context for future sessions
- `chat history/session_2026_06_29_phase3b_guardrails_and_tests.md` — session log
- `memory/project_fii_dii.md` — updated with Phase 3B completion + phased dev protocol

### Process Improvements
- Phased development protocol established (session log + memory update + changelog after every phase)

---

# Version 2.0

Claude AI Development Infrastructure Release

Date:

2026-06-29

Status:

Completed

---

## Summary

Established complete AI-assisted development infrastructure: master Claude guide,
directory-level skill files (CLAUDE.md), platform guardrails, and edge case registry.
This release makes Claude a self-sufficient platform architect without re-reading project
docs on every session.

---

## Deliverables

### Claude Skill Files (CLAUDE.md)
- `CLAUDE.md` (root) — master project rules, critical path, guardrail summary
- `engines/CLAUDE.md` — engine directory map, template, compliance checklist
- `engines/common/CLAUDE.md` — shared utility reference card
- `engines/fundamentals/CLAUDE.md` — Phase 4 spec, classification edge cases
- `engines/acquisition/CLAUDE.md` — data download rules, recovery patterns
- `engines/intelligence/CLAUDE.md` — planned intelligence engine specs
- `engines/foundation/CLAUDE.md` — index/constituent management
- `data/CLAUDE.md` — canonical data paths, lifecycle, edge cases
- `fetchers/CLAUDE.md` — legacy context, migration roadmap
- `docs/CLAUDE.md` — documentation governance, ADR creation rules
- `alerts/CLAUDE.md` — Telegram delivery rules
- `sheets/CLAUDE.md` — Google Sheets integration rules
- `storage/CLAUDE.md` — atomic write patterns, storage managers

### Governance Documents
- `docs/CLAUDE_MASTER_DEV_GUIDE.md` — 16-section master reference
- `docs/governance/GUARDRAILS.md` — 12-section, 55 rules, full edge case registry

### Technical Debt Catalogued
- 5 files marked for removal (legacy/backup/stubs)
- Data path discrepancy documented (`data/NSE Data/` → `data/NSE/`)
- 8 known issues catalogued with root causes

---

# Version 1.0

Documentation Foundation Release

Date:

2026-06-03

Status:

Completed

---

## Summary

Established complete project governance and documentation framework.

The project evolved from an informal FII/DII analytics initiative into a formally documented Capital Flow Intelligence Platform.

---

## Deliverables

### Governance Layer

Completed:

PROJECT_SCOPE.md

MASTER_ROADMAP.md

MODULE_REGISTRY.md

MASTER_CHECKLIST.md

DEVELOPMENT_GOVERNANCE.md

RESEARCH_PIPELINE.md

CHANGELOG.md

---

### Architecture Layer

Completed:

MASTER_ARCHITECTURE.md

DATA_ARCHITECTURE.md

AI_ARCHITECTURE.md

GUI_ARCHITECTURE.md

BROKER_ARCHITECTURE.md

---

### Module Documentation

Completed:

INSTITUTIONAL_INTELLIGENCE.md

SECTOR_INTELLIGENCE.md

THEME_INTELLIGENCE.md

STOCK_INTELLIGENCE.md

FUNDAMENTAL_INTELLIGENCE.md

AI_PLATFORM.md

GUI_PLATFORM.md

EXECUTION_PLATFORM.md

---

### Architecture Decision Records

Completed:

ADR-001 Raw Data Never Modified

ADR-002 NSE Data Structure

ADR-003 On Demand Cache

ADR-004 Listing Date Aware Processing

ADR-005 Nselib First Policy

ADR-006 Gross Flow Preservation

ADR-007 Sector Theme Stock Capital Flow Model

ADR-008 Cache Maintenance Strategy

ADR-009 Intelligence Layer Separation

ADR-010 AI First User Experience

ADR-011 Infographic First Visualization

ADR-012 Research Before Development

ADR-013 Broker Independence Architecture

ADR-014 Module Driven Development

ADR-015 Documentation Mandatory Before Release

---

# Strategic Architecture Update

Date:

2026-06-03

Status:

Completed

---

## Change

Project positioning updated from:

```text
FII/DII Intelligence Platform
```

to:

```text
Capital Flow Intelligence Platform
```

---

## Reason

The platform is no longer focused solely on institutional activity.

The platform now tracks market participation across:

FII

DII

PRO

CLIENT

and analyzes how capital moves through the broader market ecosystem.

---

## New Strategic Framework

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
    ↓
Fundamental Validation
    ↓
Portfolio
    ↓
Execution
```

This framework now serves as the primary architectural model for all future development.

---

# Participant Intelligence Initiative

Date:

2026-06-03

Status:

Approved

---

## Objective

Expand Institutional Intelligence into Participant Intelligence.

---

## Participants

FII

DII

PRO

CLIENT

---

## Planned Outputs

Participation Scores

Conviction Scores

Divergence Scores

Smart Money Scores

Retail Sentiment Scores

Participant Reports

Participant Dashboards

Participant Infographics

---

## Planned Engines

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

## Planned AI Capability

AI Participant Analyst

---

# Institutional Intelligence Milestone

Date:

2026-06-01

Status:

Completed

---

## Achievement

Institutional historical dataset integrity reached:

100%

---

## Results

Coverage:

100%

Integrity:

100%

Missing Dates:

0

---

## Deliverables

Historical Engine

Backfill Engine

Integrity Engine

Regime Engine

Trend Engine Foundation

---

# Data Architecture Milestone

Date:

2026-06-02

Status:

Completed

---

## Achievement

Long-term data architecture finalized.

---

## Decisions

Year-wise Bhavcopy Storage

On-Demand Cache Generation

Listing Date Aware Processing

Raw Data Preservation

Cache Maintenance Strategy

---

## Final Structure

```text
data/

NSE Data/

    bhavcopy/

        equity/

            <YEAR>/

                bhavcopy_YYYYMMDD.csv

        f&o/

            <YEAR>/

                fo_YYYYMMDD.csv

    equity_master/

    corporate_actions/

    shareholding/

    results/

    announcements/

cache/

    stock_history/
```

---

# Research Governance Milestone

Date:

2026-06-03

Status:

Completed

---

## Achievement

Research-first development process adopted.

---

## Framework

```text
Idea
    ↓
Research
    ↓
Validation
    ↓
Architecture
    ↓
Development
    ↓
Testing
    ↓
Documentation
    ↓
Release
```

---

## Result

All future major development initiatives must follow the research pipeline.

---

# User Experience Milestone

Date:

2026-06-03

Status:

Completed

---

## Achievement

AI-first and infographic-first platform philosophy adopted.

---

## Principles

AI First User Experience

Infographic First Visualization

Three Second Understanding Rule

Progressive Disclosure

Broker Independence

Human Approval Required

---

# Current Development State

Date:

2026-06-03

---

## Completed

Governance Framework

Architecture Framework

Documentation Framework

Institutional Intelligence Foundation

Data Architecture

Research Framework

---

## Active Development

Sector Intelligence Expansion

Theme Intelligence Expansion

Participant Intelligence Planning

---

## Planned

Stock Intelligence

Fundamental Intelligence

AI Platform Expansion

GUI Platform

Execution Platform

Research Platform

Commercial Platform

---

# Next Milestone

Version 1.1

Participant Intelligence Foundation

---

## Planned Deliverables

ADR-016 Participant Intelligence Framework

PARTICIPANT_INTELLIGENCE.md

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

## Expected Outcome

Transition from:

Institutional Intelligence

to

Participant Intelligence

as the primary capital flow analysis layer.

---

# Long-Term Vision

Build the world's most comprehensive Capital Flow Intelligence Platform capable of:

Tracking Participant Behavior

↓

Detecting Capital Flow

↓

Identifying Opportunities

↓

Explaining Opportunities

↓

Managing Portfolios

↓

Executing Trades

↓

Monitoring Outcomes

through a unified AI-powered investment operating system.

---

# Current Project Status

Overall Estimated Completion:

25%

---

## Strategic Focus

Current Priority:

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

capital flow discovery and opportunity identification.

This remains the central objective of the platform.

## Version 1.3

### Architecture

- Added ADR-018 Market Data Reliability Framework

### Key Decisions

- Runtime data integrity validation
- Self-healing data architecture
- Automated incremental backup strategy
- Weekly recovery point framework
- Secondary backup repository requirement
- Disaster recovery hierarchy
- Metadata-only registry architecture
