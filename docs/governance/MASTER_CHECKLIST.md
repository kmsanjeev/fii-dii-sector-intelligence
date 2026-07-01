# MASTER CHECKLIST
## Capital Flow Intelligence Platform | Updated 2026-07-02

Legend:  [x] Completed  [-] In Progress  [ ] Not Started

---

# SECTION 1 — Governance

[x] PROJECT_SCOPE.md
[x] MASTER_ROADMAP.md (updated 2026-06-30)
[x] MODULE_REGISTRY.md (updated 2026-06-30)
[x] MASTER_CHECKLIST.md (this file)
[x] DEVELOPMENT_GOVERNANCE.md
[x] CHANGELOG.md (v3.12, 2026-07-02)
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
[x] Shareholding patterns (7228 rows, Q2FY25-Q1FY26, 98.9% FII coverage)
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

[x] frontend/ project scaffold (Vite + React 18 + TypeScript + Tailwind)
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
[x] GUI Charts Page (TradingView OHLCV, IST timestamps, 5M/15M/1H/1D/1W/3M/1Y/3Y/5Y)
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

# SECTION 14 — Chatbot (Claude API) [COMPLETE]

[x] engines/ai/chatbot/intent_router.py (keyword intent: MARKET/SECTOR/STOCK/CORPORATE)
[x] engines/ai/chatbot/chat_engine.py (multi-turn agentic loop, RAG injection)
[x] engines/ai/chatbot/tools/data_tools.py (11 data access functions)
[x] engines/ai/chatbot/tools/tool_registry.py (Anthropic API schemas + dispatch)
[x] backend/routers/chat.py (POST /api/chat, in-memory session management)
[x] ANTHROPIC_API_KEY in .env

---

# SECTION 15 — Financial Results [COMPLETE]

[x] engines/fundamentals/financial_results_engine.py (NSE XBRL + FILING_WINDOWS, 4181 rows)
[x] engines/fundamentals/valuation_engine.py (P/E, ROE, valuation_label, 2084 symbols)
[x] engines/fundamentals/shareholding_engine.py (quarterly FII/DII/promoter%, backfill)
[x] data/NSE/results/ (quarterly_results.csv: 4181 rows, Q2FY25+Q3FY25, 99% EQ universe)
[x] data/NSE/shareholding/quarterly_shp.csv (7228 rows, Q2FY25-Q1FY26, 98.9% FII coverage)

---

# SECTION 16 — Management Intelligence [COMPLETE]

[x] engines/management/holding_trend_engine.py (QoQ promoter/FII/DII deltas, 7 signals)
[x] engines/management/announcement_fetcher.py (nselib bulk, 527 records, 8-type classification)
[x] engines/management/management_sentiment_engine.py (rule-based + Claude API tone score)
[x] data/NSE/shareholding/holding_trends.csv (conviction_signal per symbol)
[x] data/NSE/shareholding/board_announcements.csv (527 records, DIVIDEND/BONUS/BUYBACK)
[x] data/NSE/shareholding/management_sentiment.csv (471 symbols, POSITIVE 435, NEUTRAL 36)

---

# SECTION 17 — Daily Intelligence Refresh [NOT STARTED] <- NEXT BUILD

[ ] engines/orchestration/daily_refresh.py (ordered engine pipeline, per-stage error isolation)
[ ] engines/orchestration/refresh_scheduler.py (APScheduler: 18:00 IST weekdays trigger)
[ ] engines/orchestration/refresh_monitor.py (staleness checker, refresh_log.csv output)
[ ] data/intelligence/refresh_log.csv (per-run: stage, status, duration, rows_updated)
[ ] Integration test: confirm full pipeline runs end-to-end without manual intervention
[ ] Verify: alert_engine fires on fresh data after each successful refresh

---

# SECTION 18 — Portfolio Engine [NOT STARTED] <- after Phase 17

[ ] engines/portfolio/position_engine.py (add/close/update positions, atomic CSV writes)
[ ] engines/portfolio/exposure_engine.py (sector/theme exposure %, vs rotation_signal)
[ ] engines/portfolio/pnl_engine.py (unrealised P&L from bhavcopy parquet cache prices)
[ ] backend/routers/portfolio.py (/api/portfolio/positions + /exposure + /pnl endpoints)
[ ] data/portfolio/positions.csv (symbol, qty, entry_price, entry_date, sector, status)
[ ] data/portfolio/portfolio_snapshot.csv (daily sector exposure + P&L snapshot)
[ ] Frontend Portfolio page (holdings table, exposure bar, signal alignment gauge)

---

# SECTION 19 — Backtesting Framework [NOT STARTED] <- after Phase 18

[ ] engines/backtest/signal_backtester.py (replay EMERGING signals, compute forward returns)
[ ] engines/backtest/strategy_engine.py (entry/exit rules: N-day hold, stop-loss, target)
[ ] engines/backtest/performance_engine.py (Sharpe, max drawdown, win rate, hit rate by sector)
[ ] data/intelligence/backtest_results.csv (per-signal: score, entry_date, fwd_ret_20d, outcome)
[ ] data/intelligence/strategy_performance.csv (aggregate: Sharpe, win%, avg_return, drawdown)
[ ] Frontend Backtest page (equity curve, performance table, signal accuracy by label)

---

# SECTION 20 — Broker Adapter (Read-Only) [NOT STARTED] <- after Phase 18

[ ] engines/broker/base_adapter.py (abstract BrokerAdapter interface, broker-independence)
[ ] engines/broker/zerodha_adapter.py (Kite Connect: holdings, positions, margins)
[ ] engines/broker/position_sync.py (map broker positions -> portfolio engine schema)
[ ] ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_ACCESS_TOKEN in .env
[ ] Verify: live Zerodha holdings auto-populate positions.csv on sync

---

# SECTION 21 — Research Platform [NOT STARTED] <- after Phase 18 + 19

[ ] engines/research/thesis_engine.py (write/read/archive per-symbol investment theses)
[ ] engines/research/thesis_validator.py (quarterly validation vs results + SHP + management)
[ ] engines/research/report_engine.py (weekly Telegram digest + PDF export)
[ ] data/research/theses.csv (symbol, thesis_text, written_date, target_price, target_date)
[ ] data/research/thesis_scores.csv (quarterly validation: score, evidence, verdict)
[ ] Frontend Research page (thesis list, quarterly validation history)

---

# SECTION 22 — Execution Platform [NOT STARTED] <- after Phase 19 + 20

[ ] engines/execution/paper_trader.py (simulate orders vs live prices, no real money)
[ ] engines/execution/order_manager.py (order queue, state machine: PENDING/PLACED/FILLED)
[ ] engines/execution/risk_engine.py (position limits, concentration cap, max drawdown stop)
[ ] engines/execution/live_trader.py (real orders — only enabled by LIVE_TRADE_MODE=true)
[ ] Gate: paper mode must run 4 weeks with Sharpe > 0.8 before live_trader is enabled
[ ] Frontend Execution page (order blotter, risk dashboard, paper vs live toggle)

---

# SECTION 23 — Commercial Platform [NOT STARTED] <- after Phases 17-22 stable

[ ] backend/auth/ (JWT login/refresh, user CRUD, bcrypt passwords)
[ ] backend/subscriptions/ (plan tiers: Free/Pro/Institutional, feature gates)
[ ] frontend/auth/ (login page, subscription management page)
[ ] Per-user data isolation (portfolio, research, alert preferences)
[ ] Stripe payment integration (or equivalent)

---

# CURRENT PLATFORM COMPLETION

```
Foundation + Data         100%  (Phases 1-4)
Participant Intelligence  100%  (Phase 5)
Sector Intelligence       100%  (Phase 6)
Corporate Intelligence    100%  (Phase 7)
Stock Scoring             100%  (Phase 8)
Alert System              100%  (Phase 9)
FastAPI Backend           100%  (Phase 10)
React GUI + Charts        100%  (Phase 11)
ML Layer                  100%  (Phase 12)
RAG Knowledge Base        100%  (Phase 13)
Chatbot                   100%  (Phase 14)
Financial Results + SHP   100%  (Phase 15)
Management Intelligence   100%  (Phase 16)
Daily Refresh             0%    (Phase 17 <- NEXT)
Portfolio Engine          0%    (Phase 18)
Backtesting Framework     0%    (Phase 19)
Broker Adapter            0%    (Phase 20)
Research Platform         0%    (Phase 21)
Execution Platform        0%    (Phase 22)
Commercial Platform       0%    (Phase 23)

Overall: ~55% of full vision complete
Intelligence + Application + AI: 100%. Investment Operating System: 0%.
```
