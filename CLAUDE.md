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
|   |-- results/                  <- quarterly results (Phase 15, empty)
|   `-- shareholding/             <- shareholding patterns (Phase 15, empty)
|-- bhavcopy/equity/1995-2026/    <- LEGACY location, 7813 files (USE FOR ML + momentum)
|-- BSE/                          <- Future, no engines yet
|-- cache/stock_history/          <- Per-symbol OHLCV (config: STOCK_HISTORY_CACHE)
|-- historical/institutional/     <- positioning history + cash flows (LIVE)
|-- intelligence/                 <- Derived outputs — all rebuilt by engines (REBUILDABLE)
`-- reference/                    <- sector/theme/classification CSVs
```
**WARNING:** `data/NSE Data/` (with space) does NOT exist — fix any engine referencing it.
**WARNING:** `data/bhavcopy/` is the LEGACY location. New engines write to `data/NSE/bhavcopy/` via config.

## INTELLIGENCE OUTPUTS (all current as of 2026-06-30)
```
data/intelligence/
|-- participant_flow_scores.csv      2581 rows  FII/DII/PRO/CLIENT OI+Volume z-scores
|-- participant_intelligence.csv     2581 rows  regime, conviction, smart money, divergence
|-- sector_capital_flows.csv        74269 rows  sector turnover-weighted participant attribution
|-- sector_flow_scores.csv          74269 rows  rolling flow scores + sector weights
|-- sector_rotation_intelligence.csv   29 rows  snapshot: rotation_signal, combined_score
|-- sector_rotation_history.csv     74269 rows  time-series of above
|-- price_momentum.csv               2441 rows  ret_30d/60d/90d/365d, vol_ratio, price_score
|-- bull_run_probability.csv         2441 rows  4-factor score, label, regime-adjusted
|-- bull_run_watchlist.csv            225 rows  EMERGING symbols only
|-- block_bulk_deals.csv            12467 rows  institutional deal history (6M)
|-- institutional_deal_signals.csv    361 rows  30D net institutional flow per symbol
|-- corporate_action_signals.csv    40517 rows  classified actions 1999-2026
|-- corporate_confidence_scores.csv  1111 rows  12M rolling confidence per symbol
|-- event_calendar.csv              33839 rows  board meetings + results 2023-2026
|-- upcoming_catalysts.csv             12 rows  next 60D events with catalyst score
`-- index_momentum.csv + others          various index intelligence outputs
```

## PHASE STATUS (2026-06-30)
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
| 9     | Alert System (Telegram)       | NOT STARTED      | 7 alert types, APScheduler |
| 10    | FastAPI Backend               | NOT STARTED      | REST + WebSocket, 12 routes |
| 11    | React GUI                     | NOT STARTED      | 10 pages, dark terminal |
| 12    | ML Intelligence Layer         | NOT STARTED      | XGBoost + LightGBM, 4 models |
| 13    | RAG Knowledge Base            | NOT STARTED      | FAISS + BM25, 6 indexes |
| 14    | Chatbot (Claude API)          | NOT STARTED      | 5 agents + tool registry |
| 15    | Financial Results             | NOT STARTED      | yfinance quarterly data |
| 16    | Management Intelligence       | NOT STARTED      | holding trends + Claude tone scoring |

## CURRENT BUILD TARGET: Phase 9 — Alert System
**Next file:** `alerts/alert_engine.py`
**Then:** `alerts/alert_store.py`, `alerts/telegram_bot.py`, `alerts/daily_digest.py`, `alerts/alert_scheduler.py`
**Packages needed:** `py -3.11 -m pip install python-telegram-bot==21.* APScheduler==3.*`
**Env vars required:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## CRITICAL PATH (Phases 9-16)
```
Phase 9  Alert System      alerts/           <- START HERE
Phase 10 FastAPI Backend   backend/
Phase 11 React GUI         frontend/         <- needs Phase 10
Phase 12 ML Layer          engines/ml/       <- independent
Phase 13 RAG               engines/ai/knowledge/  <- independent
Phase 14 Chatbot           engines/ai/chatbot/    <- needs Phase 10 + 13
Phase 15 Financial Results engines/fundamentals/  <- data enrichment
Phase 16 Mgmt Intelligence engines/management/   <- needs Phase 14
```

## COMPLETED INTELLIGENCE STACK
```
Participant (5A/5B/5C) -> Sector (6A/6B/6C) -> Corporate (7A/7B/7C) -> Stock (8A/8B)
```
Full cascade is operational. All intelligence CSVs current as of 2026-06-29 to 2026-06-30.

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

## NEW MODULE LOCATIONS (Phases 9-16)
```
alerts/                <- Phase 9:  Alert engine + Telegram bot
backend/               <- Phase 10: FastAPI REST + WebSocket
frontend/              <- Phase 11: React 18 + TypeScript + Vite
engines/ml/            <- Phase 12: XGBoost + LightGBM + Isolation Forest
engines/ai/knowledge/  <- Phase 13: FAISS + BM25 RAG indexes
engines/ai/chatbot/    <- Phase 14: Claude API agents + tool registry
engines/fundamentals/  <- Phase 15: yfinance quarterly results
engines/management/    <- Phase 16: holding trends + Claude tone scoring
```

## PACKAGES TO INSTALL (Phases 9-16)
```bash
py -3.11 -m pip install python-telegram-bot==21.* APScheduler==3.*   # Phase 9
py -3.11 -m pip install fastapi uvicorn[standard] pydantic            # Phase 10
py -3.11 -m pip install xgboost lightgbm scikit-learn shap pyarrow   # Phase 12
py -3.11 -m pip install faiss-cpu sentence-transformers rank-bm25     # Phase 13
py -3.11 -m pip install anthropic                                      # Phase 14
```

## ENV VARS REQUIRED (never hardcode)
```
TELEGRAM_BOT_TOKEN    Phase 9
TELEGRAM_CHAT_ID      Phase 9
ANTHROPIC_API_KEY     Phase 14, 16
```

## ARCHITECTURE REFERENCE
Full guide: `docs/CLAUDE_MASTER_DEV_GUIDE.md`
Guardrails: `docs/governance/GUARDRAILS.md` (55 rules)
Module specs: `docs/modules/`
ADR decisions: `docs/decisions/` (ADR-001 through ADR-020; next = ADR-021)
