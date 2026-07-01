# MASTER ROADMAP
## Capital Flow Intelligence Platform | Updated 2026-07-02

---

# Purpose

Define the long-term development strategy. Ensure development stays aligned with the
core mission: identify capital flow (Participant -> Sector -> Stock) before broad market recognition.

---

# Core Mission

Track participant behavior (FII / DII / PRO / CLIENT) and identify how capital moves:

  Market -> Participant -> Sector -> Theme -> Stock -> Portfolio -> Execution

before broad market recognition.

---

# Development Philosophy

Every feature must support one or more of:
1. Detect capital flow
2. Detect rotation
3. Detect accumulation
4. Explain opportunity
5. Improve decision making
6. Improve user experience
7. Improve execution quality

---

# Platform Generations

## Generation 1 — Institutional Intelligence (COMPLETE)
FII/DII positioning, regime detection, basic index intelligence.
Output: institutional_positioning_history.csv, regime engine.

## Generation 2 — Capital Flow Intelligence (COMPLETE 2026-06-30)
Full participant -> sector -> stock cascade.
Output: 32 intelligence CSVs, bull run watchlist, 225 EMERGING symbols.

## Generation 3 — Application Layer (COMPLETE 2026-07-02)
Alert delivery, GUI, ML models, conversational AI.
Phases 9-16. All complete.

## Generation 4 — Investment Operating System (FUTURE)
Portfolio management, broker execution, research platform, commercial tiers.

---

# STRATEGIC PHASES

---

## PHASE 1 — Foundation Layer | COMPLETE
Bhavcopy import, equity master, project structure, ADR framework.
Engines: bhavcopy_import_engine.py, equity_master_engine.py, cache_manager.py

## PHASE 2 — Classification Engine | COMPLETE (99.5%)
29-sector, 18-theme taxonomy. 2123 symbols classified.
Engines: classification_engine_v4.py, industry_master_engine.py
Output: data/reference/company_classification_v4.csv

## PHASE 3 — Index Intelligence | COMPLETE
139 NSE indices tracked. Index momentum, strength, leadership persistence.
Engines: index_intelligence_engine.py, sector_leadership_persistence_engine.py
Output: data/intelligence/index_momentum.csv, index_strength.csv

## PHASE 3B — Guardrails + Test Suite | COMPLETE
55 guardrail rules across 12 sections. 400+ automated tests.
Files: engines/common/guardrails.py, tests/ (16 test files)

## PHASE 4 — Fundamentals Layer | COMPLETE
Company fundamentals, industry master, NSE constituents.
4A: company_fundamentals_master_engine.py -> company_fundamentals_master.csv
4B: industry_master_engine.py -> industry_master.csv (183 industries)
4C: classification_engine_v4.py completion -> 99.53% coverage
4D: nse_constituents_engine_v1.py -> index_membership.csv (30 indices, 506 symbols)

## PHASE 5 — Participant Intelligence Layer | COMPLETE
FII/DII/PRO/CLIENT F&O OI + Volume + Cash market flows. Daily incremental.
5A: participant_acquisition_engine.py -> institutional_positioning_history.csv (2581 rows)
5B: participant_flow_engine.py -> participant_flow_scores.csv (2581 rows, 62 cols)
5C: participant_intelligence_engine.py -> participant_intelligence.csv
Current regime: NEUTRAL | FII conviction: 40% | Smart Money: -4.7

## PHASE 6 — Sector Rotation + Capital Flow | COMPLETE
Turnover-weighted FII/DII attribution across 29 sectors. 2016-2026.
6A: sector_capital_flow_engine.py -> sector_capital_flows.csv (74269 rows)
6B: sector_flow_score_engine.py -> sector_flow_scores.csv (74269 rows)
6C: sector_rotation_intelligence_engine.py -> sector_rotation_intelligence.csv (29 sectors)

## PHASE 7 — Corporate Intelligence Layer | COMPLETE (per ADR-020)
Block/bulk deals, event calendar, corporate action confidence scoring.
7A: block_bulk_deal_engine.py -> institutional_deal_signals.csv (361 symbols)
7B: corporate_event_calendar_engine.py -> event_calendar.csv (33839 rows)
7C: corporate_action_intelligence_engine.py -> corporate_confidence_scores.csv (1111 symbols)

## PHASE 8 — Bull Run Probability Engine | COMPLETE
Multi-factor per-stock scoring. Price + Sector + Institutional + Corporate signals.
8A: price_momentum_engine.py -> price_momentum.csv (2441 symbols)
8B: bull_run_probability_engine.py -> bull_run_probability.csv + watchlist (225 EMERGING)

---

## PHASE 9 — Alert System | COMPLETE (2026-06-30)
7 alert types: regime change, STRONG_CANDIDATE, block deal, sector rotation, catalyst, divergence, daily digest.
118 alerts on first run. APScheduler: digest at 18:30 IST, signal checks at 19:00 IST.
Telegram bot live and tested.

## PHASE 10 — FastAPI Backend | COMPLETE (2026-06-30)
16 endpoints + WebSocket. Port 8001. 60min in-memory CSV reload. start.ps1/stop.ps1 for persistent launch.

## PHASE 11 — React GUI | COMPLETE (2026-07-02)
10 pages + Charts page. TradingView OHLCV with IST timestamp correction. 5M/15M/1H intraday + 9 daily timeframes.
Dark terminal theme. Port 5173.

## PHASE 12 — ML Intelligence Layer | COMPLETE (2026-06-30)
4 engines: feature engineering (24 features), XGBoost accumulation, LGB+XGB bull run ensemble, daily scorer.
2441 symbols scored. SHAP values for top 100.

## PHASE 13 — RAG Knowledge Base | COMPLETE (2026-06-30)
5 engines: document builder (1091 docs), BM25 indexer, FAISS indexer (6 domains), hybrid RRF retriever, daily updater.

## PHASE 14 — Chatbot (Claude API) | COMPLETE (2026-06-30)
Intent router + agentic chat engine + tool registry (11 data access functions) + /api/chat endpoint.
claude-sonnet-4-6 with RAG context injection.

## PHASE 15 — Financial Results + Shareholding | COMPLETE (2026-07-01)
NSE XBRL P&L: 4181 rows, 2084 symbols (Q2FY25+Q3FY25, 99% EQ universe).
Shareholding: quarterly_shp.csv (7228 rows, Q2FY25-Q1FY26, 98.9% FII coverage).
Valuation: P/E + ROE scores, 2084 symbols.

## PHASE 16 — Management Intelligence | COMPLETE (2026-06-30)
3 engines: holding_trend_engine.py, announcement_fetcher.py, management_sentiment_engine.py.
527 board announcements classified; 471 symbols scored; Claude API tone scoring.

---

---

# GENERATION 4 — Investment Operating System (CURRENT FOCUS)

Phases 17-23. Each phase is independently deliverable and testable.
Dependency chain is strictly linear — no phase can be skipped.

---

## PHASE 17 — Daily Intelligence Refresh | Priority 1 (NEXT)

**Why first:** Every downstream phase (portfolio, execution, research) depends on fresh
intelligence. Without this, the platform is a static historical report, not a live radar.
The alert system exists and the Telegram bot is live — but they fire on stale data.

Location: `engines/orchestration/`
Stack: APScheduler (already installed), existing engines 5A/6A/8A/8B/12/13/9

Engine pipeline (18:00 IST, market days only):
```
5A participant_acquisition (incremental F&O + cash)
  -> 6A sector_capital_flow (rebuild)
  -> 6B sector_flow_scores (rebuild)
  -> 6C sector_rotation_intelligence (rebuild)
  -> 7A block_bulk_deal (incremental 1-day)
  -> 8A price_momentum (rebuild)
  -> 8B bull_run_probability (rebuild)
  -> 12  ml_scorer (daily inference, no retraining)
  -> 13  RAG index_updater (rebuild from fresh CSVs)
  -> 9   alert_engine (evaluate fresh signals, push Telegram)
```

Files:
- `engines/orchestration/daily_refresh.py` — ordered pipeline with per-stage error isolation
- `engines/orchestration/refresh_scheduler.py` — APScheduler trigger (18:00 IST weekdays)
- `engines/orchestration/refresh_monitor.py` — staleness checker, logs to refresh_log.csv

Success criteria: Platform runs without manual intervention every market day.

---

## PHASE 18 — Portfolio Engine | Priority 2 (needs Phase 17)

Track real positions against the intelligence signals the platform generates.

Location: `engines/portfolio/`, `backend/routers/portfolio.py`, `frontend/` Portfolio page
Stack: pandas, FastAPI (existing), React (existing)

Files:
- `engines/portfolio/position_engine.py` — CRUD: add/close/update positions
- `engines/portfolio/exposure_engine.py` — sector/theme exposure vs rotation signal
- `engines/portfolio/pnl_engine.py` — unrealised P&L from bhavcopy cache prices
- `backend/routers/portfolio.py` — REST endpoints: /api/portfolio/positions + /exposure + /pnl
- Frontend Portfolio page: holdings table, sector exposure bar, signal alignment gauge

Data:
- `data/portfolio/positions.csv` — symbol, qty, entry_price, entry_date, sector, status
- `data/portfolio/portfolio_snapshot.csv` — daily exposure + P&L snapshot

Success criteria: Can enter positions and see live sector exposure vs sector_rotation_intelligence.

---

## PHASE 19 — Backtesting Framework | Priority 3 (needs Phase 18)

Validate whether intelligence signals actually predict price moves before risking real money.
Replay historical bull_run_probability signals against actual subsequent price returns.

Location: `engines/backtest/`
Stack: pandas, bhavcopy parquet cache (existing), pyarrow (existing)

Files:
- `engines/backtest/signal_backtester.py` — replay past EMERGING signals, compute forward returns
- `engines/backtest/strategy_engine.py` — entry/exit rules (entry on signal, exit after N days or stop)
- `engines/backtest/performance_engine.py` — Sharpe, max drawdown, win rate, hit rate by sector
- Frontend Backtest page (new): equity curve, performance table, signal accuracy by label

Data:
- `data/intelligence/backtest_results.csv` — per-signal actual return vs signal score
- `data/intelligence/strategy_performance.csv` — aggregate strategy metrics

Success criteria: Can quantify historical signal quality. Basis for deciding what score threshold to act on.

---

## PHASE 20 — Broker Adapter (Read-Only) | Priority 4 (needs Phase 18)

Sync live broker positions into the portfolio engine. Read-only first — no order placement.

Location: `engines/broker/`
Stack: kiteconnect (Zerodha), abstract adapter interface for broker independence

Files:
- `engines/broker/base_adapter.py` — abstract BrokerAdapter interface (ADR-013 compliant)
- `engines/broker/zerodha_adapter.py` — Kite Connect API: holdings, positions, margins
- `engines/broker/position_sync.py` — map broker positions to portfolio engine schema

Env vars:
- `ZERODHA_API_KEY`, `ZERODHA_API_SECRET`, `ZERODHA_ACCESS_TOKEN` (in .env, never hardcoded)

Success criteria: Live Zerodha holdings auto-import into portfolio engine without manual entry.

---

## PHASE 21 — Research Platform | Priority 5 (needs Phase 18 + 19)

Investment thesis library: record the reasoning behind each position and validate it
automatically each quarter against financial results, shareholding changes, and management signals.

Location: `engines/research/`
Stack: pandas, anthropic SDK (existing for Claude API), Telegram (existing)

Files:
- `engines/research/thesis_engine.py` — write/read/archive investment theses per symbol
- `engines/research/thesis_validator.py` — score thesis quarterly vs results + SHP changes
- `engines/research/report_engine.py` — weekly intelligence digest (Telegram + PDF)

Data:
- `data/research/theses.csv` — symbol, thesis_text, written_date, target_price, target_date
- `data/research/thesis_scores.csv` — quarterly validation scores per thesis

Success criteria: Theses auto-validate each quarter; weekly digest Telegram message includes thesis status.

---

## PHASE 22 — Execution Platform | Priority 6 (needs Phase 19 + 20)

Paper trading first. Live orders only after backtesting proves signal quality.
Hard gate: live_mode flag off by default, enabled only by explicit env var.

Location: `engines/execution/`
Stack: kiteconnect (existing from Phase 20)

Files:
- `engines/execution/paper_trader.py` — simulate orders against live prices, no money at risk
- `engines/execution/order_manager.py` — order queue, state machine (PENDING/PLACED/FILLED/FAILED)
- `engines/execution/risk_engine.py` — position limits, sector concentration, max drawdown stop
- `engines/execution/live_trader.py` — real order placement (requires `LIVE_TRADE_MODE=true` in .env)

Success criteria:
- Paper mode: place 20 simulated trades over 2 weeks, verify P&L tracking correct
- Live mode: only enable after paper mode Sharpe > 0.8 over minimum 4-week window

---

## PHASE 23 — Commercial Platform | Priority 7 (needs Phases 17-22 stable)

Productize the platform for multiple users. Last phase — never before the core is stable.

Location: `backend/auth/`, `backend/subscriptions/`, `frontend/auth/`
Stack: JWT (python-jose), bcrypt, Stripe (payment), PostgreSQL or SQLite

Files:
- `backend/auth/` — JWT login/refresh, user CRUD, role-based access
- `backend/subscriptions/` — plan tiers (Free/Pro/Institutional), feature gates
- `frontend/auth/` — login page, subscription management page
- Multi-user data isolation: per-user portfolio, research, and alert preferences

Success criteria: Two users can log in simultaneously with separate portfolios and alert configs.

---

# CURRENT STATUS (2026-07-02)

Phases 1-16 COMPLETE. Generation 3 (intelligence + application + AI) fully operational.
Generation 4 active. Build order is strict — Phase 17 first, no exceptions.

```
Phase 17  Daily Refresh       engines/orchestration/   <- BUILD NOW
Phase 18  Portfolio Engine    engines/portfolio/        <- after 17
Phase 19  Backtesting         engines/backtest/         <- after 18
Phase 20  Broker Adapter      engines/broker/           <- after 18
Phase 21  Research Platform   engines/research/         <- after 18 + 19
Phase 22  Execution Platform  engines/execution/        <- after 19 + 20
Phase 23  Commercial Platform backend/auth/             <- after 17-22 stable
```
