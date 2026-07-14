# MASTER ROADMAP
## Capital Flow Intelligence Platform | Updated 2026-07-09

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

## Generation 4 — Investment Operating System (COMPLETE 2026-07-02)
Portfolio management, broker execution, research platform, commercial tiers.
Phases 17-25. All complete. Full investment operating system is live.

## Generation 5 — Trade Intelligence Layer (COMPLETE 2026-07-02)
Per-stock entry/exit synthesis, conviction scoring, technical + F&O intelligence.
Phases A/B/C/D. All complete.

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

## PHASE 11 — React GUI | COMPLETE (2026-07-09)
15 pages. KLineChart Pro v0.1.1 (klinecharts v9.8.12) OHLCV with custom indicators (VOLMain, VWAP, Supertrend, HMA).
Inline styles via C.* token objects (no Tailwind). 5M/15M/1H intraday + 9 daily timeframes.
Dark terminal theme. Port 5173. frontend/ directory.

## PHASE 12 — ML Intelligence Layer | COMPLETE (2026-06-30)
4 engines: feature engineering (24 features), XGBoost accumulation, LGB+XGB bull run ensemble, daily scorer.
2441 symbols scored. SHAP values for top 100.

## PHASE 13 — RAG Knowledge Base | COMPLETE (2026-06-30)
5 engines: document builder (1091 docs), BM25 indexer, FAISS indexer (6 domains), hybrid RRF retriever, daily updater.

## PHASE 14 — Chatbot (Multi-Provider LLM) | COMPLETE (2026-07-09)
Intent router + agentic chat engine + tool registry (11 data access functions) + /api/chat endpoint.
Groq llama-3.3-70b-versatile (primary) via llm_client.py multi-provider fallback chain.
RAG context injection. parallel_tool_calls=False to prevent Llama XML function-call bug.

## PHASE 15 — Financial Results + Shareholding | COMPLETE (2026-07-09)
NSE XBRL P&L: 4181 rows, 2084 symbols (Q2FY25+Q3FY25, 99% EQ universe).
Shareholding: quarterly_shp.csv (76170 rows, Q1FY24-Q1FY26 8 quarters, fraction-scale fixed in Phase SH).
Valuation: P/E + ROE scores, 2084 symbols.
Extended Financials (Phase 15B): OPM%, ROCE%, Book Value/share, Sales Growth CAGR.

## PHASE 16 — Management Intelligence | COMPLETE (2026-06-30)
3 engines: holding_trend_engine.py, announcement_fetcher.py, management_sentiment_engine.py.
527 board announcements classified; 471 symbols scored; Claude API tone scoring.

---

---

# GENERATION 4 — Investment Operating System (COMPLETE 2026-07-02)

All 9 phases complete. Platform now covers the full investment loop.

## PHASE 17 — Symbol Change History | COMPLETE
`engines/foundation/symbol_change_engine.py` | 1038 NSE symbol renames (e.g. IIFLWAM→360ONE)
Data: `data/NSE/equity_master/symbol_change_history.csv`

## PHASE 18 — Corporate Announcements Intelligence | COMPLETE
`engines/corporate/` | NSE XBRL announcement fetcher, 12 announcement types classified
Data: `data/intelligence/company_announcements.csv`, `announcement_signals.csv`

## PHASE 19 — Daily Intelligence Refresh | COMPLETE
`engines/orchestration/refresh_scheduler.py` | APScheduler 18:00 IST weekdays
Full pipeline: 5A→6A→6B→6C→7A→18→8A→8B→12→13→9

## PHASE 20 — Portfolio Engine | COMPLETE
`engines/portfolio/` | transactions.csv, unrealised P&L, sector allocation
Backend: `/api/portfolio/positions`, `/exposure`, `/pnl`
Frontend: Portfolio page

## PHASE 21 — Backtesting Framework | COMPLETE
`engines/backtest/` | 3 strategies, 5 horizons, Sharpe/drawdown/win-rate metrics
Frontend: Backtest page (equity curve, signal accuracy table)

## PHASE 22 — Broker Adapter (Read-Only) | COMPLETE
`engines/broker/` | Dhan + CSV adapters, broker sync engine
`backend/routers/broker.py` | Frontend: Broker page

## PHASE 23 — Research Platform | COMPLETE
`engines/research/` | 2406-symbol screener (15 filters), comparator, notes engine
Frontend: Research page

## PHASE 24 — Execution Platform | COMPLETE
`engines/execution/` | risk engine, paper/live orders, signal recommender
`engines/execution/dhan_order_adapter.py` | Frontend: Execution page

## PHASE 25 — Commercial Platform | COMPLETE (auth off by default)
`backend/auth/` | SQLite sessions, roles, API keys
`POST /api/auth/setup` | Frontend: Admin page (Auth Config panel)

---

# GENERATION 5 — Trade Intelligence Layer (COMPLETE 2026-07-02)

Per-stock entry/exit synthesis, conviction scoring, technical + F&O overlays, full chat UI.

## PHASE A — Technical + F&O Intelligence | COMPLETE
`engines/intelligence/technical_engine.py` | 52W H/L, 20/50/200 DMA, trend_signal (2718 rows)
`engines/intelligence/fno_engine.py` | futures OI, 1D/5D delta, oi_signal (211 F&O stocks)
`data/intelligence/market_context.json` | market PCR + regime pulse

## PHASE B — Trade Intelligence Card | COMPLETE
`frontend/src/components/platform/TradeIntelligenceCard.tsx` | 7-factor WHY BUY / EXIT WATCH panel
`backend/routers/stocks.py` `_enrich_bulk()` | merges tech/FNO/ML into all stock listing endpoints
Stock listing endpoints: 20 total. WatchlistPage: ACTION column. Dashboard: action badge.

## PHASE C — Trade Conviction Alerts (P9/P10) | COMPLETE
`engines/intelligence/trade_conviction_engine.py` | server-side 7-factor score, 2406 symbols
`data/intelligence/trade_conviction_scores.csv` | action: STRONG_BUY/BUY/HOLD/REDUCE/EXIT
Alert types: 10 total (P9 TRADE_CONVICTION cap 3/day, P10 OI_SIGNAL_FLIP cap 5/day)

## PHASE D — Chat Page (Full UI) | COMPLETE
`frontend/src/pages/ChatPage.tsx` | 355 lines: session chat, intent badge, typing dots,
6 suggested prompts, auto-resize textarea, New Chat reset, API error banner
`frontend/src/api/client.ts` | ChatResponseData type, sendChat(), resetChatSession()
LLM backend: Groq llama-3.3-70b-versatile (free tier, replaced Anthropic API)
`engines/ai/chatbot/chat_engine.py` | Groq agentic loop with tool_use_failed fallback

---

---

# GENERATION 6 — AstroFinance + KLineChart Pro + Intelligence Expansion (COMPLETE 2026-07-09)

## PHASE FPI — Sector FPI Fortnightly | COMPLETE
Fortnightly sector-level FPI data. 8690 rows.

## PHASE KU — Kundli + Gann Intelligence | COMPLETE
Vedic astro + Gann angle analysis for market timing signals.

## PHASE AF — AstroFinance Planetary Intelligence | COMPLETE (corrected 2026-07-15, see ADR-022)
`engines/intelligence/astro_engine.py` | data/intelligence/astro_signals.csv (31 sectors, daily)
Phase AF = planetary signals integrated into daily pipeline. Full spec:
docs/modules/ASTRO.md. (This entry previously cited a non-existent path,
`engines/astro/planetary_intelligence_layer.py` / `planetary_intelligence.csv`
— fixed under ADR-022's documentation pass.)

## PHASE CH — KLineChart Pro Charts | COMPLETE
Replaced TradingView Lightweight Charts with klinecharts v9.8.12 (KLineChart Pro v0.1.1).
Custom indicators: VOLMain, VWAP, Supertrend, HMA — `frontend/src/indicators/customIndicators.ts`
Inline styles via C.* token objects (no Tailwind, no shadcn/ui, no Framer Motion).

## PHASE TI — Technical Indicators Expansion | COMPLETE
Added RSI, MACD, ATR, Bollinger Bands, OBV, ADX columns to technical_indicators.csv (2718 rows).

## PHASE SH — Shareholding XBRL Fix + 8-Score Panel | COMPLETE
Fixed fraction-scale bug in NSE XBRL parser. 76170 rows (Q1FY24-Q1FY26, 8 quarters).
8-score panel UI added to ShareholdingPage.

## PHASE UI-S — Sectors + Social Pulse UI | COMPLETE
Updated sector dashboard with Social Pulse integration.

---

# CURRENT STATUS (2026-07-09)

ALL 25 CORE PHASES + A/B/C/D/FPI/KU/AF/CH/TI/SH/UI-S COMPLETE. Full investment operating system is live.
Project location: `D:\Projects\fii-dii-sector-intelligence`

```
Gen 1  Institutional Intelligence   Phases 1-8         COMPLETE
Gen 2  Application Layer            Phases 9-16        COMPLETE
Gen 3  Investment Operating System  Phases 17-25       COMPLETE
Gen 5  Trade Intelligence Layer     Phases A-D         COMPLETE
Gen 6  AstroFinance + Charts        Phases FPI/KU/AF/CH/TI/SH/UI-S  COMPLETE
```

Ongoing:
- Daily data refresh (refresh_scheduler.py, 18:00 IST weekdays)
- Chat token conservation (Groq free tier: 100k tokens/day)
- Theme Intelligence expansion (35% — rotation engines planned as next major phase)
