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

## PHASE 17 — Symbol Change History | Priority 1 (NEXT)

**Why:** Data integrity prerequisite. NSE renames symbols when companies rebrand or merge
(e.g., IIFLWAM -> 360ONE on 23-Jan-2023). Without this, Phase 21 backtesting silently
returns wrong or missing results for any symbol that changed name historically. Also prevents
bhavcopy lookups from failing for renamed stocks in all downstream engines.

Location: `engines/foundation/`
Source: NSE archives `https://nsearchives.nseindia.com/content/equities/symbolchange.csv`
        (1038 records, open endpoint, no auth required)

Files:
- `engines/foundation/symbol_change_engine.py` — download, clean, deduplicate, save

Data:
- `data/NSE/equity_master/symbol_change_history.csv`
  columns: company_name, old_symbol, new_symbol, change_date

Usage in downstream engines: every engine doing historical bhavcopy lookups must resolve
old_symbol -> new_symbol using this file before loading price data.

Success criteria: 1000+ records downloaded, all major known renames present (IIFLWAM/360ONE,
BIRLA3M/3MINDIA, etc.), integrated into bhavcopy_import_engine.py as a lookup layer.

---

## PHASE 18 — Corporate Announcements Intelligence | Priority 2 (after Phase 5A)

**Why:** The board_announcements.csv (527 rows, Phase 16) uses the corporate_actions_for_equity()
API — same source as dividends and splits. The REAL NSE announcements API is entirely separate and
provides qualitative corporate disclosures that are critical for management intelligence:
- Press Releases (management narrative)
- Analysts/Institutional Investor Meet outcomes (FII-management interaction signals)
- Outcome of Board Meetings (decisions, not just actions)
- SEBI Takeover + Insider Trading disclosures (stake change signals)
- Financial Result Updates (timeline of result filings)
- Trading Window closures (insider signal — window closes before sensitive events)

NSE endpoint: `GET /api/corporate-announcements?index=equities&symbol=X`
Sample scale: RELIANCE=3313, TCS=3321, HDFCBANK=2306 announcements each.

Location: `engines/corporate/`
Stack: nselib nse_urlfetch (existing), APScheduler (for daily update via Phase 19)

Files:
- `engines/corporate/announcement_intelligence_engine.py`
  - incremental download per symbol (from last_fetched_date)
  - classify by `desc` field into 12 announcement types
  - score by signal value (Analyst Meet > Press Release > Trading Window etc.)
  - output: per-symbol announcement history + latest signal score

Data:
- `data/intelligence/company_announcements.csv`
  columns: symbol, date, announcement_type, signal_score, title_snippet, has_attachment
- `data/intelligence/announcement_signals.csv`
  columns: symbol, latest_signal_date, dominant_type, announcement_score (0-100)

Feeds into:
- Phase 16 management_sentiment (expands source from 527 board_announcements to full feed)
- Phase 19 daily refresh (announcements updated daily)
- Phase 21 backtesting (announcement signal as a feature)
- Phase 23 research platform (thesis validation uses result/meeting announcements)

Success criteria: 50,000+ announcements downloaded for the 2441-symbol universe covering
the last 2 years; announcement_signals.csv scored for all symbols.

---

## PHASE 19 — Daily Intelligence Refresh | Priority 3 (after Phases 1-18)

Automated orchestration pipeline. Runs every market day at 18:00 IST.
Transforms the platform from a static historical report into a live capital flow radar.

Location: `engines/orchestration/`
Stack: APScheduler (already installed), all existing engines

Engine pipeline (18:00 IST, market days only):
```
5A participant_acquisition (incremental F&O + cash)
  -> 6A sector_capital_flow (rebuild)
  -> 6B sector_flow_scores (rebuild)
  -> 6C sector_rotation_intelligence (rebuild)
  -> 7A block_bulk_deal (incremental 1-day)
  -> 18  announcement_intelligence (incremental, last 1 day per symbol)
  -> 8A price_momentum (rebuild)
  -> 8B bull_run_probability (rebuild)
  -> 12  ml_scorer (daily inference, no retraining)
  -> 13  RAG index_updater (rebuild from fresh CSVs)
  -> 9   alert_engine (evaluate fresh signals, push Telegram)
```

Files:
- `engines/orchestration/daily_refresh.py` — ordered pipeline, per-stage error isolation
- `engines/orchestration/refresh_scheduler.py` — APScheduler trigger (18:00 IST weekdays)
- `engines/orchestration/refresh_monitor.py` — staleness checker, refresh_log.csv

Success criteria: Platform runs without manual intervention every market day.

---

## PHASE 20 — Portfolio Engine | Priority 4 (after Phase 19)

Track real positions against the intelligence signals the platform generates.

Location: `engines/portfolio/`, `backend/routers/portfolio.py`, `frontend/` Portfolio page

Files:
- `engines/portfolio/position_engine.py` — CRUD: add/close/update positions
- `engines/portfolio/exposure_engine.py` — sector/theme exposure vs rotation signal
- `engines/portfolio/pnl_engine.py` — unrealised P&L from bhavcopy parquet cache
- `backend/routers/portfolio.py` — /api/portfolio/positions + /exposure + /pnl
- Frontend Portfolio page

Data:
- `data/portfolio/positions.csv` — symbol, qty, entry_price, entry_date, sector, status
- `data/portfolio/portfolio_snapshot.csv` — daily sector exposure + P&L

Success criteria: Can enter positions and see live sector exposure vs sector_rotation_intelligence.

---

## PHASE 21 — Backtesting Framework | Priority 5 (after Phase 20)

Validate intelligence signals against historical price outcomes before risking real money.
Requires Phase 17 (symbol change history) for correct historical bhavcopy lookups.

Location: `engines/backtest/`

Files:
- `engines/backtest/signal_backtester.py` — replay EMERGING signals, compute forward returns
- `engines/backtest/strategy_engine.py` — entry/exit rules (N-day hold, stop, target)
- `engines/backtest/performance_engine.py` — Sharpe, drawdown, win rate, hit rate by sector
- Frontend Backtest page (equity curve, signal accuracy table)

Data:
- `data/intelligence/backtest_results.csv`
- `data/intelligence/strategy_performance.csv`

Success criteria: 2 years of signals replayed. Sharpe and win rate quantified per label tier.

---

## PHASE 22 — Broker Adapter (Read-Only) | Priority 6 (after Phase 20)

Sync live broker positions into the portfolio engine. Read-only first.

Location: `engines/broker/`

Files:
- `engines/broker/base_adapter.py` — abstract BrokerAdapter (ADR-013)
- `engines/broker/zerodha_adapter.py` — Kite Connect: holdings, positions, margins
- `engines/broker/position_sync.py` — map broker -> portfolio schema

Env vars: ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_ACCESS_TOKEN

Success criteria: Live Zerodha holdings auto-import into positions.csv on sync.

---

## PHASE 23 — Research Platform | Priority 7 (after Phases 20 + 21)

Investment thesis library. Auto-validates each quarter using announcements + results + SHP.

Location: `engines/research/`

Files:
- `engines/research/thesis_engine.py` — write/read/archive per-symbol theses
- `engines/research/thesis_validator.py` — quarterly score vs results + SHP + announcements
- `engines/research/report_engine.py` — weekly Telegram digest + PDF

Data:
- `data/research/theses.csv`, `data/research/thesis_scores.csv`

---

## PHASE 24 — Execution Platform | Priority 8 (after Phases 21 + 22)

Paper trading first. Live orders only after backtesting validates signal quality.
Hard gate: LIVE_TRADE_MODE=true in .env required, off by default.

Location: `engines/execution/`

Files:
- `engines/execution/paper_trader.py` — simulate orders, no real money
- `engines/execution/order_manager.py` — state machine: PENDING/PLACED/FILLED/FAILED
- `engines/execution/risk_engine.py` — position limits, concentration, drawdown stop
- `engines/execution/live_trader.py` — real orders (gate: LIVE_TRADE_MODE=true)

Gate: paper mode must achieve Sharpe > 0.8 over 4 weeks before live_trader is enabled.

---

## PHASE 25 — Commercial Platform | Priority 9 (after Phases 19-24 stable)

Productize for multiple users. Last phase — only after core investment loop is proven.

Location: `backend/auth/`, `backend/subscriptions/`, `frontend/auth/`

Files:
- `backend/auth/` — JWT, bcrypt, user CRUD, role-based access
- `backend/subscriptions/` — Free/Pro/Institutional tiers, feature gates
- `frontend/auth/` — login, subscription management
- Per-user portfolio, research, alert isolation
- Stripe or equivalent payment integration

---

# CURRENT STATUS (2026-07-02)

Phases 1-16 COMPLETE (with 4 output gaps: RAG indexes, valuation_scores, holding_trends, shap_values).
Generation 4 active. Build order is strict — Phase 17 first, no exceptions.

```
Phase 17  Symbol Change History      engines/foundation/      <- BUILD NOW
Phase 18  Corporate Announcements    engines/corporate/       <- after 17
Phase 19  Daily Intelligence Refresh engines/orchestration/   <- after 1-18
Phase 20  Portfolio Engine           engines/portfolio/       <- after 19
Phase 21  Backtesting Framework      engines/backtest/        <- after 20
Phase 22  Broker Adapter (R/O)       engines/broker/          <- after 20
Phase 23  Research Platform          engines/research/        <- after 20+21
Phase 24  Execution Platform         engines/execution/       <- after 21+22
Phase 25  Commercial Platform        backend/auth/            <- after 19-24 stable
```
