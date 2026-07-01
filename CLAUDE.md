# CAPITAL FLOW INTELLIGENCE PLATFORM — CLAUDE CONTEXT

## IDENTITY
**Repo:** fii-dii-sector-intelligence | **Domain:** India institutional market intelligence
**Mission:** Identify capital flow (Participant -> Sector -> Theme -> Stock) before broad market recognition.
This is a **decision intelligence platform**, not a screener.

## AI OPERATING MODE
Act as: Senior System Architect + Lead Python Developer + Quant Research Engineer.
Never act as: tutor, explainer, or generic assistant.

## MANDATORY CODING RULES (NON-NEGOTIABLE)
1. Deliver COMPLETE copy-paste-ready files — never partial snippets or patches
2. Provide `git add / git commit / git push` commands after every code change
3. Freeze architecture with user before writing any code
4. Use incremental processing with recovery mechanisms
5. Handle 4500+ symbol universe in every engine — never assume small dataset
6. Listing-date-aware processing: never process data before a stock's listing date
7. Raw data is IMMUTABLE — never modify files under `data/bhavcopy/` or `data/NSE/`
8. Cache is DISPOSABLE — never treat it as source of truth
9. Python environment: always use `py -3.11` — system Python 3.14 lacks pandas/nselib
10. Windows cp1252 terminal: never use Unicode chars (arrows, boxes) in print() — use ASCII

## DATA ACQUISITION PRIORITY (always enforce)
1. nselib (primary)  2. NSE API  3. Alternative sources  4. yFinance (last resort)

## CANONICAL DATA PATHS (from engines/common/config.py — authoritative)
```
data/
|-- NSE/                          <- Structured NSE data (USE THIS)
|   |-- bhavcopy/equity/YYYY/     <- Target for imported bhavcopy
|   |-- bhavcopy/fno/YYYY/
|   |-- equity_master/            <- equity_master.csv + company_fundamentals_master.csv
|   |-- indices/                  <- index constituent CSVs + index_membership.csv
|   |-- corporate_actions/        <- 1999-2026, 28 YYYY.csv files (COMPLETE)
|   |-- results/                  <- quarterly_results.csv (Phase 15 COMPLETE: 4181 rows)
|   `-- shareholding/             <- quarterly_shp.csv (4 quarters Q2FY25-Q1FY26, 7228 rows)
|-- bhavcopy/equity/1995-2026/    <- LEGACY location, 7813 files (USE FOR ML + momentum)
|-- BSE/                          <- Future, no engines yet
|-- cache/stock_history/          <- Per-symbol OHLCV parquet (config: STOCK_HISTORY_CACHE)
|-- historical/institutional/     <- positioning history + cash flows (LIVE)
|-- intelligence/                 <- Derived outputs — all rebuilt by engines (REBUILDABLE)
`-- reference/                    <- sector/theme/classification CSVs
```
**WARNING:** `data/NSE Data/` (with space) does NOT exist — fix any engine referencing it.
**WARNING:** `data/bhavcopy/` is the LEGACY location. New engines write to `data/NSE/bhavcopy/` via config.

## INTELLIGENCE OUTPUTS (current as of 2026-07-02)
```
data/intelligence/
|-- participant_flow_scores.csv          2581 rows  FII/DII/PRO/CLIENT OI+Volume z-scores
|-- participant_intelligence.csv         2581 rows  regime, conviction, smart money, divergence
|-- sector_capital_flows.csv            74269 rows  sector turnover-weighted participant attribution
|-- sector_flow_scores.csv              74269 rows  rolling flow scores + sector weights
|-- sector_rotation_intelligence.csv       29 rows  snapshot: rotation_signal, combined_score
|-- sector_rotation_history.csv         74269 rows  time-series of above
|-- price_momentum.csv                   2441 rows  ret_30d/60d/90d/365d, vol_ratio, price_score
|-- bull_run_probability.csv             2441 rows  4-factor score, label, regime-adjusted
|-- bull_run_watchlist.csv                225 rows  EMERGING symbols only
|-- block_bulk_deals.csv                12467 rows  institutional deal history (6M)
|-- institutional_deal_signals.csv        361 rows  30D net institutional flow per symbol
|-- corporate_action_signals.csv        40517 rows  classified actions 1999-2026
|-- corporate_confidence_scores.csv      1111 rows  12M rolling confidence per symbol
|-- event_calendar.csv                  33839 rows  board meetings + results 2023-2026
|-- upcoming_catalysts.csv                 12 rows  next 60D events with catalyst score
|-- index_momentum.csv + others                     various index intelligence outputs
|-- ml_features/feature_matrix.parquet   2441 rows  24 ML features (Phase 12)
|-- ml_accumulation_scores.csv           2441 rows  XGBoost binary scores (Phase 12)
|-- ml_bull_run_scores.csv               2441 rows  LGB+XGB ensemble scores (Phase 12)
|-- ml_scores_combined.csv               2441 rows  daily combined ML output (Phase 12)
|-- quarterly_results.csv                4181 rows  NSE XBRL P&L, 2084 symbols (Phase 15)
|-- valuation_scores.csv                 2084 rows  P/E, ROE, valuation_label (Phase 15)
`-- management_sentiment.csv              471 rows  Claude tone score, label (Phase 16)
data/NSE/shareholding/
|-- quarterly_shp.csv                    7228 rows  Q2FY25-Q1FY26 FII/DII/promoter % (Phase 15C)
|-- holding_trends.csv                              QoQ promoter/FII/DII deltas (Phase 16)
`-- board_announcements.csv               527 rows  classified board announcements (Phase 16)
```

## PHASE STATUS (2026-07-02)
| Phase | Name                          | Status           | Notes |
|-------|-------------------------------|------------------|-------|
| 1     | Foundation Layer              | COMPLETE 100%    | bhavcopy import, equity master |
| 2     | Classification Engine         | COMPLETE 99.5%   | 2123 symbols, 27 sectors, 10 OTHER remain |
| 3     | Index Intelligence            | COMPLETE 100%    | 139 indices, index_membership.csv |
| 3B    | Guardrails + Test Suite       | COMPLETE 100%    | 55 rules, 400+ tests |
| 4A    | Company Fundamentals Master   | COMPLETE 100%    | 2123 symbols |
| 4B    | Industry Master Engine        | COMPLETE 100%    | 183 industries, 96.7% sector coverage |
| 4C    | Classification V4             | COMPLETE 100%    | 99.53% coverage |
| 4D    | NSE Constituents Downloader   | COMPLETE 100%    | 30 indices, 506 symbols |
| 5A    | Participant Acquisition       | COMPLETE 100%    | F&O 2016-2026, Cash 2024-2026 |
| 5B    | Participant Flow Engine       | COMPLETE 100%    | 2581 rows, OI delta + z-scores |
| 5C    | Participant Intelligence      | COMPLETE 100%    | regime=NEUTRAL, Smart Money=-4.7 |
| 6A    | Sector Capital Flow           | COMPLETE 100%    | 74k rows, 2016-2026, 29 sectors |
| 6B    | Sector Flow Scores            | COMPLETE 100%    | rolling 5D/20D/60D weights |
| 6C    | Sector Rotation Intelligence  | COMPLETE 100%    | rotation_signal + combined_score |
| 7A    | Block/Bulk Deal Engine        | COMPLETE 100%    | 12467 deals, 361 signals |
| 7B    | Event Calendar Engine         | COMPLETE 100%    | 33839 events 2023-2026 |
| 7C    | Corporate Action Intelligence | COMPLETE 100%    | 40517 actions, 1111 confidence scores |
| 8A    | Price Momentum Engine         | COMPLETE 100%    | 2441 symbols, 5 lookbacks |
| 8B    | Bull Run Probability Engine   | COMPLETE 100%    | 225 EMERGING, regime NEUTRAL x0.90 |
| 9     | Alert System (Telegram)       | COMPLETE 100%    | 7 alert types, APScheduler, 118 alerts on first run |
| 10    | FastAPI Backend               | COMPLETE 100%    | 16 endpoints, port 8001, WebSocket live ticker |
| 11    | React GUI                     | COMPLETE 100%    | 10 pages + Charts page, TradingView OHLCV, IST timestamps |
| 12    | ML Intelligence Layer         | COMPLETE 100%    | XGBoost+LightGBM, 24 features, 4 model outputs |
| 13    | RAG Knowledge Base            | COMPLETE 100%    | FAISS+BM25, 6 domain indexes, hybrid RRF retrieval |
| 14    | Chatbot (Claude API)          | COMPLETE 100%    | 4 agents, tool registry, /api/chat endpoint |
| 15    | Financial Results + SHP       | COMPLETE 100%    | 4181 XBRL rows, 2084 symbols; 4 quarters shareholding |
| 16    | Management Intelligence       | COMPLETE 100%    | 3 engines: holding trends, announcements, sentiment |

## CURRENT PLATFORM STATUS (2026-07-02)
**ALL 16 PHASES COMPLETE.** Full intelligence-to-UI stack is live.
- Backend: `py -3.11 -m uvicorn backend.main:app --port 8001 --reload`
- Frontend: `npm run dev` in `frontend/` (Vite at http://localhost:5173)
- Startup: Run `./start.ps1` to launch both servers as detached background processes
- Telegram bot: Live and tested (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in `.env`)

**Generation 4 — Investment Operating System (phases 17-25, strict order):**
| Phase | Name                        | Location                  | Depends On | Status      |
|-------|-----------------------------|---------------------------|------------|-------------|
| 17    | Symbol Change History       | engines/foundation/       | Phase 1    | NOT STARTED |
| 18    | Corporate Announcements     | engines/corporate/        | Phase 5A   | NOT STARTED |
| 19    | Daily Intelligence Refresh  | engines/orchestration/    | 1-18       | NOT STARTED |
| 20    | Portfolio Engine            | engines/portfolio/        | Phase 19   | NOT STARTED |
| 21    | Backtesting Framework       | engines/backtest/         | Phase 20   | NOT STARTED |
| 22    | Broker Adapter (R/O)        | engines/broker/           | Phase 20   | NOT STARTED |
| 23    | Research Platform           | engines/research/         | 20 + 21    | NOT STARTED |
| 24    | Execution Platform          | engines/execution/        | 21 + 22    | NOT STARTED |
| 25    | Commercial Platform         | backend/auth/             | 19-24 done | NOT STARTED |

**NEXT BUILD: Phase 17 — Symbol Change History**
- Source: `https://nsearchives.nseindia.com/content/equities/symbolchange.csv` (1038 records, live)
- Output: `data/NSE/equity_master/symbol_change_history.csv`
- Engine: `engines/foundation/symbol_change_engine.py`
- Without this, Phase 21 backtesting returns wrong results for renamed companies (e.g., IIFLWAM→360ONE)

## COMPLETED FULL STACK
```
Intelligence:  Participant (5A/5B/5C) -> Sector (6A/6B/6C) -> Corporate (7A/7B/7C) -> Stock (8A/8B)
Application:   Alert System (9) -> FastAPI Backend (10) -> React GUI (11)
AI/ML:         ML Models (12) -> RAG Knowledge Base (13) -> Claude Chatbot (14)
Fundamentals:  Financial Results (15) -> Shareholding (15C) -> Management Intel (16)
```

## FILES MARKED FOR REMOVAL (confirm before deleting)
- `engines/index_intelligence_engine_v1_backup.py` — backup copy, redundant
- `engines/intelligence/index_intelligence_engine_v2.py` — 80-line stub
- `engines/intelligence/leadership_persistence_engine_v2.py` — 30-line stub
- `engines/fundamentals/security_master_engine.py` — superseded by v2
- `engines/classification_engine.py` — v1, superseded by v4

## KNOWN BUGS
- ADANIPORTS classifies as AEROSPACE (wrong) — should be LOGISTICS/PORTS
  Root cause: Industry Master has limited override coverage. Low priority now.
- Cash market flows: 2026-02-19 failed (tz-aware/naive mixing in NSE API response)
  Fix: add explicit timezone normalization in participant_acquisition_engine.py

## MANDATORY GUARDRAILS (enforce in every engine)
Full spec: `docs/governance/GUARDRAILS.md`

| ID | Rule | How |
|----|------|-----|
| G-D-01 | Raw data IMMUTABLE | Raise if target path exists before writing raw file |
| G-D-02 | Atomic writes | Write to `.tmp`, then `shutil.move()` — never direct write |
| G-D-03 | No empty DataFrames | Check `df.empty` before any file write |
| G-D-04 | Schema validation | Validate required columns + nulls before saving |
| G-D-05 | No duplicate dates | `safe_append()` — deduplicate by date before concat |
| G-A-01 | Rate limiting | `time.sleep(cfg.API_DELAY)` between every nselib call |
| G-A-02 | Retry + backoff | 3 retries with exponential delay on every API call |
| G-A-03 | Recovery queue | Write failed items to `NSE/recovery_queue.csv` |
| G-A-04 | Market hours guard | No heavy batch ops during 09:15-15:30 IST |
| G-S-01 | EQ series only | `df = df[df["series"] == "EQ"]` at universe entry |
| G-S-02 | Listing date aware | Filter files by listing_date before reading |
| G-S-04 | Universe size check | Raise if equity_master has < 1800 EQ symbols |
| G-C-01 | No null sectors | `fillna("UNCATEGORIZED")` then log to review queue |
| G-C-02 | Manual override frozen | Always apply manual_override.csv last, immutably |
| G-P-01 | No negative prices | Drop rows where Open/High/Low/Close <= 0 |
| G-P-02 | OHLC consistency | High >= Low >= 0; High >= Open/Close |
| G-I-01 | Min 5 sessions | Return `None` (not 0) if data < 5 trading days |
| G-I-04 | NaN handling | Never `fillna(0)` on price/volume/flow — masks real gaps |
| G-SYS-01 | Env var guard | Check all required env vars at module startup |
| G-SYS-02 | Git security | No data CSVs, no credentials ever committed |

## KEY EDGE CASES (quick reference)
- **Weekend dates:** Not missing — NSE closed Sat/Sun. Skip silently.
- **Mahurat trading:** 1-hour Diwali session — real data, low volume, process normally
- **Circuit breaker halt:** Partial day — bhavcopy still exists, not a gap
- **Zero volume day:** Log warning, do not drop — may be valid circuit limit hit
- **F&O expiry (last Thu):** Higher volume expected — not anomalous
- **ISIN duplicates (merger):** Keep active symbol, flag retired one as DELISTED
- **Conglomerates:** Use primary revenue segment for classification (ITC -> FMCG)
- **T+1 institutional lag:** FII/DII data may arrive next day — wait until 18:00 IST
- **Pre-2016 OI data:** Not available — do not backfill participant OI before 2016
- **ETFs/REITs in bhavcopy:** Filter out using EXCLUDE_KEYWORDS before classification
- **Windows terminal:** Never use Unicode arrows/boxes in print() — cp1252 will crash

## MODULE LOCATIONS (ALL BUILT)
```
alerts/                <- Phase 9:  alert_engine.py, alert_store.py, telegram_bot.py, daily_digest.py, alert_scheduler.py
backend/               <- Phase 10: main.py (port 8001), routers/, services/, ws/
frontend/              <- Phase 11: React 18 + TypeScript + Vite (port 5173), TradingView charts
engines/ml/            <- Phase 12: feature_engineering.py, accumulation_model.py, bull_run_model.py, ml_scorer.py
engines/ai/knowledge/  <- Phase 13: document_builder.py, faiss_indexer.py, bm25_indexer.py, retriever.py
engines/ai/chatbot/    <- Phase 14: intent_router.py, chat_engine.py, tools/
engines/fundamentals/  <- Phase 15: financial_results_engine.py, valuation_engine.py, shareholding_engine.py
engines/management/    <- Phase 16: holding_trend_engine.py, announcement_fetcher.py, management_sentiment_engine.py
start.ps1              <- Launch both servers as detached background processes (idempotent)
stop.ps1               <- Kill both servers by port (8001 + 5173)
```

## PACKAGES INSTALLED
```bash
python-telegram-bot==21.11.1, APScheduler==3.11.3     # Phase 9
fastapi==0.138.2, uvicorn[standard]                   # Phase 10
xgboost==3.2.0, lightgbm==4.6.0, scikit-learn==1.9.0 # Phase 12
faiss-cpu==1.14.3, sentence-transformers==5.6.0       # Phase 13
anthropic==0.113.0                                     # Phase 14
```

## ENV VARS (in .env — never hardcode)
```
TELEGRAM_BOT_TOKEN    Phase 9  (live and tested)
TELEGRAM_CHAT_ID      Phase 9  (live and tested)
ANTHROPIC_API_KEY     Phase 14, 16
```

## ARCHITECTURE REFERENCE
Full guide: `docs/CLAUDE_MASTER_DEV_GUIDE.md`
Guardrails: `docs/governance/GUARDRAILS.md` (55 rules)
Module specs: `docs/modules/`
ADR decisions: `docs/decisions/` (ADR-001 through ADR-020; next = ADR-021)
