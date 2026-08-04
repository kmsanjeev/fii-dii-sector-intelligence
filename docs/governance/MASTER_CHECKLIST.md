# MASTER CHECKLIST
## Capital Flow Intelligence Platform | Updated 2026-07-19

Legend:  [x] Completed  [-] In Progress  [ ] Not Started

---

# SECTION 1 — Governance

[x] PROJECT_SCOPE.md
[x] MASTER_ROADMAP.md (updated 2026-06-30)
[x] MODULE_REGISTRY.md (updated 2026-06-30)
[x] MASTER_CHECKLIST.md (this file)
[x] DEVELOPMENT_GOVERNANCE.md
[x] CHANGELOG.md (v4.25, 2026-07-09)
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
[x] ADR-021 Alert System Architecture (created with Phase 9, 2026-06-30)
[ ] ADR-022 ML Model Governance (create before Phase 12 expansion)

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

## Data Acquired (Phase 15-16)
[x] Quarterly financial results (4181 rows, 2084 symbols, NSE XBRL, Q2FY25+Q3FY25)
[x] Shareholding patterns (76170 rows, Q1FY24-Q1FY26 8 quarters, fraction-scale fixed — Phase SH)
[x] NSE board announcements (527 records, 471 symbols, Phase 16)

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

# SECTION 9 — Alert System [COMPLETE]

[x] ADR-021 Alert System Architecture (docs/decisions/ADR-021-Alert-System-Architecture.md)
[x] alerts/alert_engine.py (7 alert types, priority-ordered evaluation, 118 alerts on first run)
[x] alerts/alert_store.py (cooldown tracking, dedup, JSON state)
[x] alerts/telegram_bot.py (send + format, HTML formatting)
[x] alerts/daily_digest.py (18:30 IST daily summary, 690-char HTML digest)
[x] alerts/alert_scheduler.py (APScheduler: digest + post-market checks)
[x] TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env (live and tested)

---

# SECTION 10 — FastAPI Backend [COMPLETE]

[x] backend/main.py (FastAPI app, CORS, lifespan, port 8001)
[x] backend/routers/market.py (/api/market/regime + freshness)
[x] backend/routers/sectors.py (/api/sectors + history + detail)
[x] backend/routers/stocks.py (/api/stocks + watchlist + detail + momentum)
[x] backend/routers/participant.py (/api/participant/latest + history)
[x] backend/routers/corporate.py (/api/corporate/deals + catalysts + confidence)
[x] backend/routers/chat.py (POST /api/chat, in-memory sessions)
[x] backend/routers/charts.py (GET /api/charts/{symbol}/ohlcv + intraday)
[x] backend/routers/data_ops.py (engine trigger endpoints + acquisition pipeline)
[x] backend/services/data_loader.py (CSV cache, 60min background reload)
[x] backend/ws/live_ticker.py (WebSocket /ws/live, regime + sectors every 30s)

---

# SECTION 11 — React GUI [COMPLETE]

[x] frontend/ project scaffold (Vite + React 18 + TypeScript + inline styles via C.* tokens)
[x] GUI AppShell (dark terminal layout, sidebar, regime badge)
[x] GUI Design system (ScoreGauge, FlowCard, CapFlowBadge, SectorTile)
[x] GUI Dashboard (regime, top sectors, top stocks, participant conviction)
[x] GUI Sector Intelligence (rotation table, sector scores)
[x] GUI Stock Watchlist (sortable/filterable table, 2441 symbols)
[x] GUI Stock Detail (4-factor gauges, price performance, deal signals)
[x] GUI Participant Intelligence (FII/DII/PRO/CLIENT cards + 90D area chart)
[x] GUI Corporate Intelligence (deals table, event calendar)
[x] GUI AI Chat (/chat page, Phase 14 endpoint)
[x] GUI Settings (freshness, alert config)
[x] GUI Charts Page (KLineChart Pro v0.1.1 klinecharts v9.8.12 OHLCV, IST timestamps, 5M/15M/1H/1D/1W/3M/1Y/3Y/5Y)
[x] GUI custom indicators (VOLMain, VWAP, Supertrend, HMA — frontend/src/indicators/customIndicators.ts)
[x] GUI Portfolio, Backtest, Broker, Research, Execution, Admin pages (Phase 17-25)
[x] start.ps1 / stop.ps1 (persistent server management)

---

# SECTION 12 — ML Intelligence Layer [COMPLETE]

[x] engines/ml/feature_engineering.py (24-feature snapshot matrix, 2441 symbols)
[x] engines/ml/accumulation_model.py (XGBoost binary, score-proxy target)
[x] engines/ml/bull_run_model.py (LightGBM 0.6 + XGBoost 0.4 ensemble)
[x] engines/ml/ml_scorer.py (daily orchestrator: features + models + score)
[x] data/intelligence/ml_features/feature_matrix.parquet (2441 x 24 features)
[x] data/intelligence/ml_accumulation_scores.csv
[x] data/intelligence/ml_bull_run_scores.csv
[x] data/intelligence/ml_scores_combined.csv
[x] data/intelligence/ml_shap_values.csv (top 100 symbols)

---

# SECTION 13 — RAG Knowledge Base [COMPLETE]

[x] engines/ai/knowledge/document_builder.py (1091 text docs from 6 intelligence CSVs)
[x] engines/ai/knowledge/faiss_indexer.py (6 domain FAISS indexes, sentence-transformers)
[x] engines/ai/knowledge/bm25_indexer.py (BM25Okapi sparse keyword index)
[x] engines/ai/knowledge/retriever.py (hybrid RRF fusion, domain auto-detection)
[x] engines/ai/knowledge/index_updater.py (daily rebuild pipeline)

---

# SECTION 14 — Chatbot (Groq multi-provider) [COMPLETE]

[x] engines/ai/chatbot/intent_router.py (keyword intent: MARKET/SECTOR/STOCK/CORPORATE)
[x] engines/ai/chatbot/chat_engine.py (multi-turn agentic loop, RAG injection, Groq llama-3.3-70b-versatile)
[x] engines/ai/chatbot/tools/data_tools.py (11 data access functions)
[x] engines/ai/chatbot/tools/tool_registry.py (Groq/OpenAI function-calling format schemas + dispatch)
[x] engines/common/llm_client.py (multi-provider fallback: Groq -> Cerebras -> Gemini -> OpenRouter)
[x] backend/routers/chat.py (POST /api/chat, in-memory session management)
[x] GROQ_API_KEY in .env (chatbot primary); ANTHROPIC_API_KEY retained for Phase 16 sentiment only

---

# SECTION 15 — Financial Results [COMPLETE]

[x] engines/fundamentals/financial_results_engine.py (NSE XBRL + FILING_WINDOWS, 4181 rows)
[x] engines/fundamentals/valuation_engine.py (P/E, ROE, valuation_label, 2084 symbols)
[x] engines/fundamentals/shareholding_engine.py (quarterly FII/DII/promoter%, backfill)
[x] data/NSE/results/ (quarterly_results.csv: 4181 rows, Q2FY25+Q3FY25, 99% EQ universe)
[x] data/NSE/shareholding/quarterly_shp.csv (76170 rows, Q1FY24-Q1FY26 8 quarters, fraction-scale fixed)

---

# SECTION 16 — Management Intelligence [COMPLETE]

[x] engines/management/holding_trend_engine.py (QoQ promoter/FII/DII deltas, 7 signals)
[x] engines/management/announcement_fetcher.py (nselib bulk, 527 records, 8-type classification)
[x] engines/management/management_sentiment_engine.py (rule-based + Claude API tone score)
[x] data/NSE/shareholding/holding_trends.csv (conviction_signal per symbol)
[x] data/NSE/shareholding/board_announcements.csv (527 records, DIVIDEND/BONUS/BUYBACK)
[x] data/NSE/shareholding/management_sentiment.csv (471 symbols, POSITIVE 435, NEUTRAL 36)

---

# SECTION 17 — Symbol Change History [COMPLETE]

[x] engines/foundation/symbol_change_engine.py (1038 NSE symbol renames)
[x] data/NSE/equity_master/symbol_change_history.csv (company_name, old_symbol, new_symbol, change_date)
[x] Known renames verified: IIFLWAM->360ONE, BIRLA3M->3MINDIA

---

# SECTION 18 — Corporate Announcements Intelligence [COMPLETE]

[x] engines/corporate/ (announcement fetcher + corporate announcements engine — NSE XBRL)
[x] engines/corporate/announcement_fetcher.py (incremental download, 12 announcement types)
[x] data/intelligence/company_announcements.csv
[x] data/intelligence/announcement_signals.csv

---

# SECTION 19 — Daily Intelligence Refresh [COMPLETE]

[x] engines/orchestration/daily_refresh.py (ordered pipeline, per-stage error isolation)
[x] engines/orchestration/refresh_scheduler.py (APScheduler: 18:00 IST weekdays trigger)
[x] engines/orchestration/refresh_monitor.py (staleness checker)
[x] data/intelligence/refresh_log.csv
[x] Pipeline: 5A -> 6A/B/C -> 7A -> 18 -> 8A -> 8B -> 12 -> 13 -> 9

---

# SECTION 20 — Portfolio Engine [COMPLETE]

[x] engines/portfolio/portfolio_engine.py (transactions.csv, P&L, sector allocation)
[x] engines/portfolio/transaction_loader.py
[x] backend/routers/portfolio.py (/api/portfolio/positions + /exposure + /pnl)
[x] Frontend Portfolio page (holdings table, exposure bar, signal alignment gauge)

---

# SECTION 21 — Backtesting Framework [COMPLETE]

[x] engines/backtest/backtest_engine.py (3 strategies, 5 horizons)
[x] engines/backtest/metrics.py (Sharpe, max drawdown, win rate)
[x] data/intelligence/backtest_results.csv
[x] data/intelligence/strategy_performance.csv
[x] Frontend Backtest page (equity curve, performance table, signal accuracy)

---

# SECTION 22 — Broker Adapter (Read-Only) [COMPLETE]

[x] engines/broker/base.py (abstract BrokerAdapter interface)
[x] engines/broker/dhan_adapter.py (Dhan broker adapter)
[x] engines/broker/csv_adapter.py (CSV positions fallback)
[x] engines/broker/sync_engine.py (broker sync pipeline)
[x] backend/routers/broker.py + Frontend Broker page

---

# SECTION 23 — Research Platform [COMPLETE]

[x] engines/research/screener_engine.py (2406-symbol screener, 15 filters)
[x] engines/research/notes_engine.py (investment notes per symbol)
[x] backend/routers/research.py
[x] Frontend Research page (screener, comparator, notes)

---

# SECTION 24 — Execution Platform [COMPLETE]

[x] engines/execution/risk_engine.py (position limits, concentration cap, drawdown stop)
[x] engines/execution/order_manager.py (state machine: PENDING/PLACED/FILLED/FAILED)
[x] engines/execution/signal_recommender.py (signal-based trade recommendations)
[x] engines/execution/dhan_order_adapter.py (Dhan order placement)
[x] Frontend Execution page (order blotter, risk dashboard, paper vs live toggle)

---

# SECTION 25 — Commercial Platform [COMPLETE]

[x] backend/auth/store.py (SQLite sessions + API keys)
[x] backend/auth/middleware.py (auth enforcement middleware)
[x] backend/auth/router.py (POST /api/auth/setup, login, API key management)
[x] Auth disabled by default; enable via POST /api/auth/setup or Admin -> Auth Config
[x] Frontend Admin page (auth config panel)

---

# CURRENT PLATFORM COMPLETION (2026-07-09)

```
Foundation + Data         100%  (Phases 1-4)
Participant Intelligence  100%  (Phase 5 -- 2581 rows)
Sector Intelligence       100%  (Phase 6 -- 74269 rows)
Corporate Intelligence    100%  (Phase 7)
Stock Scoring             100%  (Phase 8 -- 2441 symbols)
Alert System              100%  (Phase 9 -- 10 alert types P1-P10)
FastAPI Backend           100%  (Phase 10 -- 20 endpoints + WebSocket)
React GUI + Charts        100%  (Phase 11 -- 15 pages, KLineChart Pro)
ML Layer                  100%  (Phase 12 -- 4 models, 2441 symbols)
RAG Knowledge Base        100%  (Phase 13 -- FAISS+BM25, 6 domain indexes)
Chatbot                   100%  (Phase 14 -- Groq primary, 11 tools)
Financial Results + SHP   100%  (Phase 15 -- 4181 XBRL rows, 76170 SHP rows)
Management Intelligence   100%  (Phase 16 -- 471 symbols sentiment)
Symbol Change History     100%  (Phase 17 -- 1038 renames)
Corporate Announcements   100%  (Phase 18)
Daily Intelligence Refresh 100% (Phase 19 -- APScheduler 18:00 IST)
Portfolio Engine          100%  (Phase 20)
Backtesting Framework     100%  (Phase 21 -- 3 strategies, 5 horizons)
Broker Adapter            100%  (Phase 22 -- Dhan + CSV)
Research Platform         100%  (Phase 23 -- 2406-symbol screener)
Execution Platform        100%  (Phase 24 -- paper + live orders)
Commercial Platform       100%  (Phase 25 -- SQLite sessions + API keys)
Technical + F&O Intel     100%  (Phase A -- 2718 symbols, 211 F&O stocks)
Trade Intelligence Card   100%  (Phase B -- 7-factor synthesis)
Trade Conviction Alerts   100%  (Phase C -- 2406 symbols, P9/P10 alerts)
Chat UI                   100%  (Phase D -- ChatPage.tsx)
Sector FPI Fortnightly    100%  (Phase FPI -- 8690 rows)
Kundli + Gann             100%  (Phase KU)
AstroFinance              100%  (Phase AF -- 209 rows planetary intelligence)
KLineChart Pro            100%  (Phase CH -- custom indicators)
Technical Indicators      100%  (Phase TI -- RSI/MACD/ATR/BB/OBV/ADX)
Shareholding XBRL Fix     100%  (Phase SH -- 8-score panel, fraction-scale fixed)
Sectors + Social Pulse UI 100%  (Phase UI-S)
Veda Hands-Free Follow-up 100%  (Phase V4 -- mic reopens after reply, no repeat wake word)
Veda Customer-Support Persona 100% (Phase V5 -- confirm-before-detail, warm greetings)
Portfolio CSV Import     100%  (Phase PF-1 -- bulk import + template)

Overall: 100% of full vision complete (Investment Operating System LIVE)
```

---

# SECTION 26 — Voice + Portfolio Ops (2026-07-15) [COMPLETE]

[x] Phase V4 -- vedaStore.ts hands-free follow-up (speak() resolves on true
    playback end; mic auto-reopens after Veda finishes talking; earcon chime
    instead of a spoken re-prompt)
[x] Phase V5 -- customer-support voice persona (chat_engine.py
    `_VOICE_ADDENDUM`, intent_router.py `_GREETING_PROMPT`, voice.py
    trailer rewritten as a genuine question, `already_asked` guard against
    double-asking)
[x] Phase PF-1 -- Portfolio CSV import (`import_transactions()`,
    `GET/POST /api/portfolio/import*`, PortfolioPage.tsx upload UI)

[-] Task #25 (session tracker) -- live browser/mic verification of the
    hands-free follow-up loop + voice persona pacing not yet done

---

# DOCUMENTATION HYGIENE (2026-07-19)

[x] CHANGELOG.md archived: entries before v4.43.0 moved to
    docs/governance/CHANGELOG_ARCHIVE.md (5681 -> 1442 lines in the active
    file) -- was being read in full most sessions, a major token cost
[x] MASTER_CHECKLIST.md + PROJECT_MASTER_STATE.md resynced to v4.56 (were
    stale since 2026-07-09 / f7f8af2, missing 4 shipped phases)

---

# SECTION 27 â€” Veda Research Foundation (2026-08-04) [PARTIAL]

# SECTION 27 - Veda Research Foundation (2026-08-04) [PARTIAL]

[x] Phase 0 -- foundation contracts added:
    `backend/routers/chat.py` request/response expansion,
    `GET /api/chat/capabilities`, `engines/common/config.py` feature flags,
    upload/cache directory paths, future attachment contract placeholders
[x] Phase 1 -- Python-first research base added:
    `engines/ai/research/` service layer, provider abstraction, `ddgs`
    provider, in-memory TTL cache, explicit `research_mode` wiring into
    `ChatEngine`
[x] Frontend contract readiness:
    `frontend/src/api/client.ts` now supports chat capability fetch,
    research metadata, and future attachment payload shape
[x] Unit test coverage added:
    `tests/test_veda_research_service.py`
[x] Phase 2 -- research mode orchestration UI/decision layer:
    `frontend/src/pages/ChatPage.tsx` and
    `frontend/src/components/veda/VedaWidget.tsx` now expose research-mode
    toggles and simple assistant research badges
[x] Phase 2 -- research audit visibility:
    `engines/ai/chatbot/chat_engine.py` now records local-first vs external
    research reasons, and `backend/routers/voice.py` logs
    request/use/provider/reason plus live `research_share`
[ ] Phase 3 -- file/document/image upload flow
[ ] Phase 4 -- source-aware answer rendering in chat UI
[ ] Phase 5 -- reviewed save-to-knowledge flow
[ ] Phase 6 -- MIT Git capability intake
[ ] Phase 7 -- MCP fallback connectors
[ ] Phase 8 -- live hardening and rollout verification
