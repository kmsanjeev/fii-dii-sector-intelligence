# CHANGELOG

## Project

Capital Flow Intelligence Platform

---

# Version 4.6.0

Chat Engine Robustness + Project Migration to D:\Projects

Date: 2026-07-02

Status: Completed

---

## Summary

Fixed two Groq chat reliability issues and migrated the entire project from
`C:\Users\hp\fii-dii-sector-intelligence` to `D:\Projects\fii-dii-sector-intelligence`
without breaking Git history or any functionality.

## Changes

- `engines/ai/chatbot/chat_engine.py`:
  - `parallel_tool_calls=False` added — prevents Llama 3.3 70B from generating
    malformed XML-style function calls (`<function=name{args}/>`) instead of JSON
  - Tool loop restructured: `break` on `tool_use_failed` → final text-only call
  - Final forced call uses clean synthesised prompt (tool results only, not full history)
    to prevent model confusion when MAX_TOOL_ROUNDS is exhausted
  - Rate limit (429) now surfaced as a readable message in both tool loop and final call
  - `MAX_TOOL_ROUNDS` reduced 5 → 3 (each round costs 2-5k tokens on Groq free tier)
- Project root: `D:\Projects\fii-dii-sector-intelligence` (migrated via robocopy)
  - 52,323 files, ~21 GB, 0 failures
  - Git remote URL (HTTPS) and history unchanged — GitHub connection intact

## Commits

`af498cd` `6dbacd3`

---

# Version 4.5.0

Groq Migration — Anthropic API replaced with Groq llama-3.3-70b-versatile (free tier)

Date: 2026-07-02

Status: Completed

---

## Summary

Replaced the Phase 14 chatbot backend (Anthropic claude-sonnet-4-6) with Groq's free-tier
`llama-3.3-70b-versatile` model to eliminate API costs during development. Anthropic API
key is retained in .env for Phase 16 management sentiment only.

## Changes

- `engines/ai/chatbot/chat_engine.py` — full rewrite for Groq:
  - Model: `llama-3.3-70b-versatile` via `groq` Python package
  - `_to_groq_tools()`: converts Anthropic `input_schema` format to OpenAI/Groq
    `{"type":"function","function":{...,"parameters":...}}` format at module load
  - Agentic loop uses `msg.tool_calls` (OpenAI format) instead of Anthropic `stop_reason`
  - History uses OpenAI message format: `role:"tool"` + `tool_call_id` for tool results
  - System prompt injected as first message in `messages` list (not separate API arg)
- `engines/ai/chatbot/tools/tool_registry.py` — tool schemas retained as Anthropic format
  (converted at load time via `_to_groq_tools()`)
- `backend/routers/chat.py` — env var check changed from `ANTHROPIC_API_KEY` to `GROQ_API_KEY`
- `.env` — `GROQ_API_KEY` added; `ANTHROPIC_API_KEY` retained for Phase 16

## Packages

`groq` Python package installed

---

# Version 4.4.0

Phase D — Chat Page full implementation

Date: 2026-07-02

Status: Completed

---

## Summary

Replaced the 17-line ChatPage.tsx placeholder (Phase 11) with a full 355-line production
chat UI backed by the Phase 14 Groq chatbot endpoint.

## Changes

- `frontend/src/pages/ChatPage.tsx` — complete rewrite:
  - Multi-turn session via `session_id` (persists across sends on same page load)
  - Intent badge (MARKET / SECTOR / STOCK / CORPORATE / RESEARCH) on each assistant reply
  - `TypingDots` animation while waiting for API response
  - 6 suggested prompt chips visible on first turn (auto-hide after first message)
  - Auto-resize textarea (1–4 lines), Shift+Enter for newline, Enter to send
  - `New Chat` button resets session and clears history
  - API error banner when GROQ_API_KEY is not configured
  - WELCOME message pre-populated; capability domain chips shown on first turn
- `frontend/src/api/client.ts` — added:
  - `ChatResponseData` type: `{ reply, session_id, intent }`
  - `sendChat(message, session_id?)` helper
  - `resetChatSession(session_id)` helper

---

# Version 4.3.0

Phase C — Trade Conviction Alerts (P9/P10)

Date: 2026-07-02

Status: Completed

---

## Summary

Built the server-side trade conviction engine and two new alert types (P9 TRADE_CONVICTION,
P10 OI_SIGNAL_FLIP) that fire daily based on the same 7-factor score used by Phase B's
TradeIntelligenceCard frontend component.

## Changes

- `engines/intelligence/trade_conviction_engine.py` (new):
  - 7-factor conviction score for 2,406 symbols: trend/DMA (25%), F&O OI (20%),
    sector rotation (15%), shareholding QoQ (15%), valuation (10%), ML score (10%),
    management sentiment (5%)
  - Output: `data/intelligence/trade_conviction_scores.csv` (2406 rows)
  - Action labels: STRONG_BUY / BUY / HOLD / REDUCE / EXIT
- `alerts/alert_engine.py` — added P9 TRADE_CONVICTION + P10 OI_SIGNAL_FLIP alert types
  - P9: fires when conviction_score >= 75 and action in (STRONG_BUY, BUY); capped 3/day
  - P10: fires on OI signal flip (LONG_BUILDUP ↔ SHORT_BUILDUP); capped 5/day
- Alert types total: 10 (was 7)

## Commits

`6b40076`

---

# Version 4.2.0

Phase B — Trade Intelligence Card with entry/exit synthesis

Date: 2026-07-02

Status: Completed

---

## Summary

Built the WHY BUY / EXIT WATCH synthesis panel on StockDetailPage and enriched all
stock listing endpoints with technical/F&O/ML bulk fields.

## Changes

- `frontend/src/components/platform/TradeIntelligenceCard.tsx` (new):
  - `computeTradeSignal(data)`: 7-factor conviction score (0–100) from existing stock data
  - Factors: trend/DMA (25%), OI signal (20%), sector rotation (15%), shareholding QoQ (15%),
    valuation (10%), ML bull run score (10%), management sentiment (5%)
  - Entry zone: LTP ±2%; stop loss: max(dma_200×0.98, close×0.90); trail: ×1.05
  - `ScoreBar`: 0–100 gradient bar with STRONG BUY / BUY / HOLD / REDUCE / EXIT labels
  - Action colors: STRONG BUY=#22C55E, BUY=#10B981, HOLD=#F59E0B, REDUCE=#F97316, EXIT=#EF4444
- `backend/routers/stocks.py`:
  - `_enrich_bulk(df)`: merges `trend_signal`, `vs_dma_200`, `prox_52w_high` from technical;
    `oi_signal` from fno_intel; `ml_bull_run_score`, `accumulation_score` from ml_scores
  - `get_stock_detail()`: added `sector_rotation_signal` via join with sector_rotation_intelligence.csv
  - Both `get_watchlist()` and `get_all_stocks()` call `_enrich_bulk()`
- `frontend/src/api/client.ts`:
  - Added `sector_rotation_signal?`, `trend_signal?`, `oi_signal?`, `ml_bull_run_score?`,
    `accumulation_score?`, `holding_trends?`, `management?` fields to `Stock` type
- `frontend/src/pages/WatchlistPage.tsx`:
  - Added `ActionBadge` component (STR BUY/BUY/HOLD/REDUCE/EXIT from label+trend+oi)
  - New ACTION column in stock table
- `frontend/src/pages/Dashboard.tsx`:
  - Quick action badge on EMERGING watchlist cards using `stock.trend_signal`
- Backend endpoints: 20 total (was 16)

## Commits

`552cf0e` `bbfe947`

---

# Version 4.1.0

Phase A — Technical + F&O Intelligence + Market Context Dashboard

Date: 2026-07-02

Status: Completed

---

## Summary

Added real-time technical indicators (52W H/L, DMAs, trend signal) and F&O intelligence
(futures OI, OI signal) for the full stock universe, plus a market PCR pulse dashboard.

## Changes

- `engines/intelligence/technical_engine.py` (new):
  - 52W High/Low proximity, 20/50/200 DMA, trend_signal (STRONG_UPTREND to STRONG_DOWNTREND)
  - Output: `data/intelligence/technical_indicators.csv` (2717 rows)
- `engines/intelligence/fno_engine.py` (new):
  - Per-stock futures OI, 1D/5D OI delta, oi_signal (LONG_BUILDUP / SHORT_COVER / etc.)
  - Output: `data/intelligence/fno_intelligence.csv` (211 F&O stocks)
- `data/intelligence/market_context.json` — market PCR + regime pulse
- GUI: Market Pulse dashboard panel added (PCR, regime, breadth counts)

## Commits

`bbfe947` `1ae9443`

---

# Version 4.0.0

Generation 4 — Investment Operating System Complete (Phases 17-25)

Date: 2026-07-02

Status: Completed

---

## Summary

All 9 Generation 4 phases built and integrated. Platform now covers the full investment
loop: data → intelligence → alerts → GUI → research → portfolio → execution → commercial.

## Phases Completed

| Phase | Name | Key Outputs |
|-------|------|-------------|
| 17 | Symbol Change History | engines/foundation/symbol_change_engine.py; 1038 renames |
| 18 | Corporate Announcements | engines/corporate/; NSE XBRL announcement fetcher |
| 19 | Daily Intelligence Refresh | engines/orchestration/refresh_scheduler.py; APScheduler 18:00 IST |
| 20 | Portfolio Engine | engines/portfolio/; transactions.csv, P&L, sector allocation |
| 21 | Backtesting Framework | engines/backtest/; 3 strategies, 5 horizons, Sharpe/drawdown metrics |
| 22 | Broker Adapter (R/O) | engines/broker/; Dhan + CSV adapters; broker sync engine |
| 23 | Research Platform | engines/research/; 2406-symbol screener, comparator, notes engine |
| 24 | Execution Platform | engines/execution/; risk engine, paper/live orders, signal recommender |
| 25 | Commercial Platform | backend/auth/; SQLite sessions, roles, API keys; auth off by default |

## GUI Pages Added (Phases 17-25)

Portfolio, Backtest, Broker, Research, Execution, Admin (auth config)
GUI total: 14 pages (was 10)

---

# Version 3.12.0

Charts Page: OHLCV candlestick + intraday + IST timestamps + bhavcopy parquet cache

Date: 2026-07-02

Status: Completed

---

## Summary

Built a full-featured Charts page within the React GUI (Phase 11 enhancement) with
TradingView Lightweight Charts v5.2.0, multiple timeframe selectors (5M/15M/1H intraday
and 1D/1W/3M/1Y/3Y/5Y daily), bhavcopy parquet as primary OHLCV source with IST timestamp
correction, and a stock intelligence panel. Fixed multiple v5 API compatibility bugs.

## Changes

- `backend/routers/charts.py` (new router):
  - `GET /api/charts/{symbol}/ohlcv` -- bhavcopy parquet primary + price adjustment pipeline
  - `GET /api/charts/{symbol}/intraday` -- nselib 5M/15M/1H candles with IST offset correction
  - IST_OFFSET = 19800 seconds: lightweight-charts renders unix as UTC; adding offset makes
    IST times display correctly (09:15 IST open shows as 09:15, not 03:45)
  - Deduplication of timestamps in intraday responses (seen set)
- `frontend/src/pages/ChartsPage.tsx` (new page):
  - Timeframe selector: 5M, 15M, 1H (intraday) | 1D, 1W, 3M, 1Y, 3Y, 5Y (daily)
  - TradingView Lightweight Charts v5.2.0 candlestick + volume histogram
  - Reset button; errors caught via useState (ErrorBoundary cannot catch useEffect errors)
  - Removed TradingView attribution watermark logo
  - Stock intelligence panel: bull_run_score, sector, label, price_score
- `frontend/src/App.tsx`: added /charts route
- `backend/main.py`: included charts router

## Bug Fixes

- `chart.priceScale('vol')` -> `volume.priceScale()` (v5 API naming change)
- `useEffect` errors caught via state flag -- ErrorBoundary cannot intercept hook errors
- Duplicate timestamps from nselib response deduplicated server-side
- `from_date`/`to_date` date math corrected for 3M/3Y/5Y ranges
- Volume histogram uses `createHistogramSeries` (not `createVolumeSeries`) in v5

## Commits

`48c6bcf` `93cc755` `31dfb18` `19953ae` `456fcd9` `da40bec` `9e2d389`

---

# Version 3.11.0

Server startup scripts + backend port fix

Date: 2026-07-01

Status: Completed

---

## Summary

Created permanent server startup/shutdown scripts and fixed backend port mismatch (Vite proxy
targets port 8001 but backend was starting on 8000 by default) that caused blank frontend data.

## Changes

- `start.ps1` (new): launches backend (port 8001) and frontend dev server (port 5173) as
  detached OS-level processes via `Start-Process -WindowStyle Hidden`. Survives Claude session
  termination. Idempotent -- checks if port already occupied before starting.
- `stop.ps1` (new): kills both servers by port using netstat PID lookup and Stop-Process.
- `backend/main.py`: startup docstring corrected to show `--port 8001` command.

## Root Cause

Vite proxy in `frontend/vite.config.ts` targets `http://localhost:8001` but backend was
being launched with default `--port 8000`. All API calls silently returned ECONNREFUSED,
causing blank data on every frontend page.

## Commit

`87e252f` -- chore: add start/stop scripts + fix backend port to 8001

---

# Version 3.10.0

Phase 15C -- Shareholding Engine: full historical backfill + data validation + moved to Acquisition section

Date: 2026-07-01

Status: Completed

---

## Summary

Shareholding Engine upgraded with full historical backfill (FY2008 to present), incremental processing,
per-window data validation, and pipeline moved from Fundamentals to Data Acquisition section
in both backend and frontend.

## Changes

- `engines/fundamentals/shareholding_engine.py`: major upgrade
  - Added `_generate_all_windows()`: dynamically generates all quarterly windows from Q1FY09 to current
  - Added `--backfill` flag: fetches all historical quarters oldest-first (incremental: skips done labels)
  - Added `--windows N` flag: fetch N most-recent quarters (default: 1 for incremental mode)
  - Added `--validate` flag: prints per-window data quality report (FII coverage %, symbol count, sum sanity)
  - Per-window validation: min 50 symbols guard, promoter+public sum check, schema validation
  - Historical coverage: NSE SHP API has meaningful data from Q4FY08 (1,264 symbols); pre-FY08 skipped
  - Incremental by default: loads existing quarterly_shp.csv and skips already-fetched windows
- `backend/routers/data_ops.py`:
  - Renamed `fundamentals_15c` → `shp_acquisition` (incremental, --windows 1)
  - Renamed `fundamentals_15c_full` → `shp_acquisition_full` (--backfill, full history)
  - Added `shp_acquisition` to `ACQUISITION_PIPELINE`
  - Moved shareholding status from `fundamentals` dict to `acquisition` dict in /api/data/status
- `frontend/src/pages/DataControlPage.tsx`:
  - Updated ENGINE_MAP: `shareholding: 'shp_acquisition'`
  - Shareholding now appears in DATA ACQUISITION section table (not FUNDAMENTALS)
  - Health bar counts updated to use named variables (acqLen, intLen, funLen)

## Data Availability Note

NSE SHP API returns 0 records before FY05, 10 records for Q4FY05, ~1,264 for Q4FY08.
Practical historical start: Q1FY09 (Apr-Jun 2008). Pre-XBRL era (before 2008) not parseable.
"Since 1995" backfill is not feasible from NSE electronic filings; engine auto-skips those windows.

---

# Version 3.9.0

Phase 15A/15B -- Financial Results + Valuation Engine

Date: 2026-07-01

Status: Completed

---

## Summary

Rewrote Phase 15A financial results engine to fetch real NSE XBRL data using
filing-season date windows. Phase 15B valuation engine fixed to read parquet cache.
Backend upgraded to 22 engines with fundamentals status section.

## Changes

- `engines/fundamentals/financial_results_engine.py`: complete rewrite
  - Replaced FETCH_PERIODS (financial period dates) with FILING_WINDOWS (filing-season dates)
  - Calls get_financial_results_master() directly; skips entries where xbrl ends in /xbrl/-
  - Concurrent XBRL parsing via ThreadPoolExecutor
  - Output: 4,181 rows, 2,084 symbols, Q2FY25 + Q3FY25 coverage (99% EQ universe)
  - Validated: RELIANCE 128,260cr, TCS 63,973cr, INFY 41,764cr match NSE actuals
- `engines/fundamentals/valuation_engine.py`: two fixes
  - _load_prices: reads .parquet from STOCK_HISTORY_CACHE (not .csv)
  - _compute_ttm: uses date_end column (quarterly_results schema)
  - Output: 2,084 symbols, 1,685 PE ratios, 2,034 ROE values, 4 valuation labels
- `backend/routers/data_ops.py`: added 3 Phase 15 engines + fundamentals status section
- `frontend/src/pages/DataControlPage.tsx`: added FUNDAMENTALS section + ENGINE_MAP entries

## Known Gaps

- Major banks (HDFCBANK, ICICIBANK, SBIN) missing from XBRL -- different schema (~5/2083 = 0.24% miss)
- yfinance disabled by default -- empty quarterly_income_stmt for all NSE.NS tickers

## Commit

`228902d` -- fix: valuation engine parquet cache + date_end column
`ec09e7c` -- feat: Phase 15A financial results engine + backend + frontend

---

# Version 3.8.2

Progress bars + Phase 6C pd.NA crash fix

Date: 2026-06-30

Status: Completed

---

## Summary

Added `tqdm` progress bars to engines that process large loops (Phases 5A, 7B, 7C)
and fixed a `TypeError` crash in Phase 6C when printing the sector rotation table.

## Changes

- `participant_acquisition_engine.py` (5A): progress bars on F&O and cash date loops
- `corporate_action_intelligence_engine.py` (7C): progress bar on 28-file CSV loading loop
- `corporate_event_calendar_engine.py` (7B): progress bar on chunked 30-day download loop
- `sector_rotation_intelligence_engine.py` (6C): fixed `int(pd.NA)` TypeError in
  `_print_summary()` -- replaced `or 0` chain with explicit `pd.isna()` guard

## Verification

Full stack run (Phases 5–14) completed successfully with all phases PASS.
Phase 6C no longer crashes when combined_rank contains pd.NA (nullable Int64).

## Commit

`768c662` -- Add progress bars to Phases 5A/7B/7C and fix Phase 6C pd.NA crash

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
