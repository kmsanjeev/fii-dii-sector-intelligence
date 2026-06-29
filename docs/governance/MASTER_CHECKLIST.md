# MASTER CHECKLIST
## Capital Flow Intelligence Platform | Updated 2026-06-30

Legend:  [x] Completed  [-] In Progress  [ ] Not Started

---

# SECTION 1 — Governance

[x] PROJECT_SCOPE.md
[x] MASTER_ROADMAP.md (updated 2026-06-30)
[x] MODULE_REGISTRY.md (updated 2026-06-30)
[x] MASTER_CHECKLIST.md (this file)
[x] DEVELOPMENT_GOVERNANCE.md
[x] CHANGELOG.md (v3.1, 2026-06-30)
[x] GUARDRAILS.md (55 rules, 12 sections)

---

# SECTION 2 — Architecture

[x] MASTER_ARCHITECTURE.md
[x] DATA_ARCHITECTURE.md
[x] AI_ARCHITECTURE.md
[x] GUI_ARCHITECTURE.md
[x] ML_AI_CHATBOT_ARCHITECTURE.md
[x] GUI_IMPLEMENTATION_PLAN.md

---

# SECTION 3 — Architecture Decisions (ADRs)

[x] ADR-001 Raw Data Never Modified
[x] ADR-002 NSE Data Structure
[x] ADR-003 On Demand Cache
[x] ADR-004 Listing Date Aware Processing
[x] ADR-005 Nselib First Policy
[x] ADR-006 Gross Flow Preservation
[x] ADR-007 Sector Theme Stock Capital Flow Model
[x] ADR-008 Cache Maintenance Strategy
[x] ADR-009 Intelligence Layer Separation
[x] ADR-010 AI First User Experience
[x] ADR-011 Infographic First Visualization
[x] ADR-012 Research Before Development
[x] ADR-013 Broker Independence Architecture
[x] ADR-014 Module Driven Development
[x] ADR-015 Documentation Mandatory Before Release
[x] ADR-016 Participant Intelligence Framework
[x] ADR-018 Market Data Reliability Framework
[x] ADR-019 Data Integrity Recovery & Backup Framework
[x] ADR-020 Corporate Intelligence Layer
[ ] ADR-021 Alert System Architecture (create before Phase 9)
[ ] ADR-022 ML Model Governance (create before Phase 12)

---

# SECTION 4 — Data Foundation

## Phase 1 — Foundation [COMPLETE]
[x] Bhavcopy import engine (7813 files, 1995-2026)
[x] Equity master engine (equity_master.csv)
[x] Cache manager
[x] Bhavcopy structure (data/bhavcopy/equity/)

## Phase 2 — Classification [COMPLETE]
[x] Classification engine v4 (99.5% coverage, 2123 symbols)
[x] Industry master engine (183 industries)
[x] Theme master engine (18 themes)
[x] company_fundamentals_master.csv (Phase 4A)
[x] company_classification_v4.csv

## Phase 3 — Index Intelligence [COMPLETE]
[x] Index intelligence engine (139 indices)
[x] Index snapshot engine
[x] Index taxonomy engine
[x] Sector leadership persistence engine
[x] index_membership.csv (30 indices, 506 symbols, Phase 4D)

## Phase 3B — Guardrails + Tests [COMPLETE]
[x] engines/common/guardrails.py (55 rules)
[x] tests/guardrails/ (12 test files)
[x] tests/edge_cases/ (4 test files)
[x] pytest.ini + conftest.py

## Phase 4 — Fundamentals [COMPLETE]
[x] company_fundamentals_master_engine.py
[x] industry_master_engine.py
[x] classification_engine_v4.py (final)
[x] nse_constituents_engine_v1.py

## Data Still Needed
[ ] Quarterly financial results (Phase 15 — yfinance workaround)
[ ] Shareholding patterns (Phase 15)
[ ] NSE announcements text (Phase 16)

---

# SECTION 5 — Participant Intelligence [COMPLETE]

[x] participant_acquisition_engine.py (5A)
    Output: institutional_positioning_history.csv (2581 rows, through 2026-06-29)
    Output: cash_market_flows_history.csv (609 rows, through 2026-06-24)

[x] participant_flow_engine.py (5B)
    Output: participant_flow_scores.csv (2581 rows, 62 cols)
    FII_flow_score latest: +10.9 | DII: -4.5 | PRO: -20.2 | CLIENT: +9.4

[x] participant_intelligence_engine.py (5C)
    Output: participant_intelligence.csv (2581 rows, 21 cols)
    Latest regime: NEUTRAL | Smart Money: -4.7 | FII conviction: 40%

---

# SECTION 6 — Sector Intelligence [COMPLETE]

[x] sector_capital_flow_engine.py (6A)
    Output: sector_capital_flows.csv (74269 rows, 29 sectors, 2016-2026)

[x] sector_flow_score_engine.py (6B)
    Output: sector_flow_scores.csv (74269 rows, 35 cols)

[x] sector_rotation_intelligence_engine.py (6C)
    Output: sector_rotation_intelligence.csv (29 sectors snapshot)
    Output: sector_rotation_history.csv (74269 rows time series)

---

# SECTION 7 — Corporate Intelligence [COMPLETE]

[x] block_bulk_deal_engine.py (7A)
    Output: block_bulk_deals.csv (12467 rows)
    Output: institutional_deal_signals.csv (361 symbols)

[x] corporate_event_calendar_engine.py (7B)
    Output: event_calendar.csv (33839 rows, 2023-2026)
    Output: upcoming_catalysts.csv (12 events in next 60D)

[x] corporate_action_intelligence_engine.py (7C)
    Output: corporate_action_signals.csv (40517 rows, 1999-2026)
    Output: corporate_confidence_scores.csv (1111 symbols)

---

# SECTION 8 — Stock Intelligence / Bull Run [COMPLETE]

[x] price_momentum_engine.py (8A)
    Output: price_momentum.csv (2441 symbols, ret_30d/60d/90d/365d, price_score)

[x] bull_run_probability_engine.py (8B)
    Output: bull_run_probability.csv (2441 symbols, 4-factor score, label)
    Output: bull_run_watchlist.csv (225 EMERGING symbols)
    Regime: NEUTRAL (x0.90) | Top: ADANIENSOL 62, ADANIENT 57, GMRAIRPORT 56

---

# SECTION 9 — Alert System [NOT STARTED]

[ ] ADR-021 Alert System Architecture
[ ] alerts/alert_engine.py (7 alert types, priority-ordered evaluation)
[ ] alerts/alert_store.py (cooldown tracking, dedup, JSON state)
[ ] alerts/telegram_bot.py (send + format, /commands)
[ ] alerts/daily_digest.py (18:30 IST daily summary)
[ ] alerts/alert_scheduler.py (APScheduler: digest + checks)
[ ] TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env

---

# SECTION 10 — FastAPI Backend [NOT STARTED]

[ ] backend/main.py (FastAPI app, CORS, lifespan)
[ ] backend/routers/market.py
[ ] backend/routers/sectors.py
[ ] backend/routers/stocks.py
[ ] backend/routers/participant.py
[ ] backend/routers/corporate.py
[ ] backend/routers/chat.py
[ ] backend/services/data_loader.py (CSV cache, 60min reload)
[ ] backend/ws/live_ticker.py (WebSocket)

---

# SECTION 11 — React GUI [NOT STARTED]

[ ] frontend/ project scaffold (Vite + React 18 + TypeScript)
[ ] GUI-1: AppShell (dark layout, sidebar, regime badge)
[ ] GUI-2: Design system (ScoreGauge, FlowCard, CapFlowBadge, SectorTile)
[ ] GUI-3: Dashboard (regime, top sectors, top stocks, participant conviction)
[ ] GUI-4: Sector Intelligence (heatmap, rotation table)
[ ] GUI-5: Stock Watchlist (sortable/filterable table)
[ ] GUI-6: Stock Detail (OHLCV + participant flow + corporate events)
[ ] GUI-7: Participant Intelligence (FII/DII timeline, conviction bars)
[ ] GUI-8: Corporate Intelligence (deals table, event calendar)
[ ] GUI-9: AI Chat (WebSocket chat interface)
[ ] GUI-10: Settings (alert preferences, data freshness)

---

# SECTION 12 — ML Intelligence Layer [NOT STARTED]

[ ] ADR-022 ML Model Governance
[ ] engines/ml/feature_engineering.py (historical feature matrix, parquet)
[ ] engines/ml/accumulation_model.py (XGBoost binary, is_up_10pct_in_20d)
[ ] engines/ml/bull_run_model.py (LightGBM + XGBoost ensemble)
[ ] engines/ml/sector_rotation_model.py (LightGBM multi-class, 29 sectors)
[ ] engines/ml/anomaly_detector.py (Isolation Forest)
[ ] engines/ml/ml_scorer.py (daily scoring without retraining)
[ ] engines/ml/model_evaluator.py (precision/recall, Sharpe on signals)
[ ] data/intelligence/ml_features/ (feature matrix parquet + saved models)

---

# SECTION 13 — RAG Knowledge Base [NOT STARTED]

[ ] engines/ai/knowledge/document_builder.py (text from intelligence CSVs)
[ ] engines/ai/knowledge/faiss_indexer.py (6 domain FAISS indexes)
[ ] engines/ai/knowledge/bm25_indexer.py
[ ] engines/ai/knowledge/retriever.py (hybrid RRF)
[ ] engines/ai/knowledge/index_updater.py (daily incremental)
[ ] data/intelligence/rag/ (FAISS .index files + metadata)

---

# SECTION 14 — Chatbot (Claude API) [NOT STARTED]

[ ] engines/ai/chatbot/intent_router.py
[ ] engines/ai/chatbot/chat_engine.py
[ ] engines/ai/chatbot/agents/market_agent.py
[ ] engines/ai/chatbot/agents/sector_agent.py
[ ] engines/ai/chatbot/agents/stock_agent.py
[ ] engines/ai/chatbot/agents/corporate_agent.py
[ ] engines/ai/chatbot/agents/research_agent.py
[ ] engines/ai/chatbot/tools/tool_registry.py
[ ] engines/ai/chatbot/tools/data_tools.py
[ ] engines/ai/chatbot/memory/short_term.py
[ ] ANTHROPIC_API_KEY in .env

---

# SECTION 15 — Financial Results [NOT STARTED]

[ ] engines/fundamentals/financial_results_engine.py (yfinance quarterly)
[ ] engines/fundamentals/valuation_engine.py (P/E, P/B, ROE scoring)
[ ] data/NSE/results/ (quarterly CSVs per symbol)

---

# SECTION 16 — Management Intelligence [NOT STARTED]

[ ] engines/management/holding_trend_engine.py (promoter/FII/DII quarterly delta)
[ ] engines/management/announcement_fetcher.py (nselib board meeting outcomes)
[ ] engines/management/management_sentiment_engine.py (Claude API tone scoring)
[ ] data/intelligence/management_intelligence.csv

---

# SECTION 17 — Execution Platform [FUTURE]

[ ] Portfolio engine
[ ] Risk engine
[ ] Order management
[ ] Trade journal
[ ] Broker adapter framework (Zerodha, Dhan, Upstox, Angel One)

---

# CURRENT PLATFORM COMPLETION

```
Foundation + Data         100%  (Phases 1-4)
Participant Intelligence  100%  (Phase 5)
Sector Intelligence       100%  (Phase 6)
Corporate Intelligence    100%  (Phase 7)
Stock Scoring             100%  (Phase 8)
Alert System                0%  (Phase 9  <- NEXT)
FastAPI Backend             0%  (Phase 10)
React GUI                   0%  (Phase 11)
ML Layer                    0%  (Phase 12)
RAG Knowledge Base          0%  (Phase 13)
Chatbot                     0%  (Phase 14)
Financial Results           0%  (Phase 15)
Management Intelligence     0%  (Phase 16)
Execution Platform          0%  (Future)

Overall: ~45% of full vision complete
Intelligence cascade: 100% complete and producing live outputs
```
