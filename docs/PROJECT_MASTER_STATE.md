# FII-DII SECTOR INTELLIGENCE PLATFORM
# MASTER PROJECT STATE
# Version 4.60 | 2026-08-04

---

# PROJECT MISSION

Build India's most advanced institutional-grade market intelligence platform capable of
identifying capital flow (Participant -> Sector -> Theme -> Stock) before broad market recognition.

Core cascade:
  FII/DII/PRO/CLIENT -> Sector Attribution -> Corporate Signals -> Stock Scoring -> Alert/Chatbot/Execution

This project is NOT a screener. It IS a decision intelligence platform.

---

# CURRENT PLATFORM STATE (2026-07-09)

**ALL 25 CORE PHASES + A/B/C/D/FPI/KU/AF/CH/TI/SH/UI-S COMPLETE. Full investment operating system is live.**

Project root: `D:\Projects\fii-dii-sector-intelligence`

## Intelligence Cascade: COMPLETE
```
Layer 1: Participant Intelligence  (5A/5B/5C)  LIVE through 2026-07-01
Layer 2: Sector Rotation           (6A/6B/6C)  LIVE through 2026-07-01
Layer 3: Corporate Intelligence    (7A/7B/7C)  LIVE through 2026-07-01
Layer 4: Stock Scoring             (8A/8B)     LIVE through 2026-07-01
Layer 5: Technical + F&O           (A)         LIVE through 2026-07-01
Layer 6: Trade Conviction          (C)         LIVE through 2026-07-01
```

## Market Snapshot (as of 2026-07-01)
- Market Regime: NEUTRAL (x0.90 multiplier)
- Smart Money Score: -4.7 | FII conviction: 40%
- Bull run watchlist: 225 EMERGING symbols
- Sector EARLY_ROTATION: MEDIA
- Trade conviction scores: 2406 symbols

---

# PHASE COMPLETION STATUS

## Foundation + Data Layer (COMPLETE)
| Phase | Engine | Output | Status |
|-------|--------|--------|--------|
| 1 | Foundation | equity_master.csv, 7813 bhavcopy files | COMPLETE |
| 2 | Classification V4 | company_classification_v4.csv (2123 symbols, 99.5%) | COMPLETE |
| 3 | Index Intelligence | 139 indices, index_momentum.csv | COMPLETE |
| 3B | Guardrails + Tests | guardrails.py, 400+ tests | COMPLETE |
| 4A | Fundamentals Master | company_fundamentals_master.csv (2123 symbols) | COMPLETE |
| 4B | Industry Master | industry_master.csv (183 industries) | COMPLETE |
| 4C | Classification V4 final | 99.53% sector coverage | COMPLETE |
| 4D | NSE Constituents | index_membership.csv (30 indices, 506 symbols) | COMPLETE |

## Intelligence Layer (COMPLETE)
| Phase | Engine | Output | Rows | Status |
|-------|--------|--------|------|--------|
| 5A | Participant Acquisition | institutional_positioning_history.csv | 2581 | COMPLETE |
| 5B | Participant Flow Engine | participant_flow_scores.csv | 2581 | COMPLETE |
| 5C | Participant Intelligence | participant_intelligence.csv | 2581 | COMPLETE |
| 6A | Sector Capital Flow | sector_capital_flows.csv | 74269 | COMPLETE |
| 6B | Sector Flow Scores | sector_flow_scores.csv | 74269 | COMPLETE |
| 6C | Sector Rotation Intel | sector_rotation_intelligence.csv | 29 | COMPLETE |
| 7A | Block/Bulk Deals | institutional_deal_signals.csv | 361 | COMPLETE |
| 7B | Event Calendar | event_calendar.csv + upcoming_catalysts.csv | 33839 | COMPLETE |
| 7C | Corporate Actions | corporate_confidence_scores.csv | 1111 | COMPLETE |
| 8A | Price Momentum | price_momentum.csv | 2441 | COMPLETE |
| 8B | Bull Run Probability | bull_run_probability.csv + watchlist (225) | 2441 | COMPLETE |

## Application Layer (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| 9  | Alert System (Telegram)    | alerts/               | COMPLETE — 10 alert types, APScheduler, cooldown + per-type caps |
| 10 | FastAPI Backend            | backend/              | COMPLETE — 20 endpoints, port 8001, WebSocket live ticker |
| 11 | React GUI                  | frontend/             | COMPLETE — 15 pages, KLineChart Pro OHLCV, IST timestamps, inline styles |
| 12 | ML Intelligence Layer      | engines/ml/           | COMPLETE — XGBoost+LightGBM, 24 features, 4 model outputs |
| 13 | RAG Knowledge Base         | engines/ai/knowledge/ | COMPLETE — FAISS+BM25, 6 domain indexes, hybrid RRF retrieval |
| 14 | Chatbot (multi-provider LLM) | engines/ai/chatbot/ | COMPLETE — Groq llama-3.3-70b (primary), multi-provider fallback via llm_client.py, 11 tools, /api/chat |
| 15 | Financial Results + SHP    | engines/fundamentals/ | COMPLETE — 4181 XBRL rows, 76170 shareholding rows (8 quarters, XBRL fraction-scale fixed) |
| 16 | Management Intelligence    | engines/management/   | COMPLETE — holding trends, announcements, sentiment |

## Generation 4 — Investment Operating System (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| 17 | Symbol Change History       | engines/foundation/    | COMPLETE — 1038 renames |
| 18 | Corporate Announcements     | engines/corporate/     | COMPLETE — NSE XBRL fetcher |
| 19 | Daily Intelligence Refresh  | engines/orchestration/ | COMPLETE — APScheduler 18:00 IST |
| 20 | Portfolio Engine            | engines/portfolio/     | COMPLETE — transactions, P&L, allocation |
| 21 | Backtesting Framework       | engines/backtest/      | COMPLETE — 3 strategies, 5 horizons |
| 22 | Broker Adapter (R/O)        | engines/broker/        | COMPLETE — Dhan + CSV adapters |
| 23 | Research Platform           | engines/research/      | COMPLETE — screener, comparator, notes |
| 24 | Execution Platform          | engines/execution/     | COMPLETE — risk engine, paper/live orders |
| 25 | Commercial Platform         | backend/auth/          | COMPLETE — auth off by default |

## Generation 5 — Trade Intelligence Layer (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| A | Technical + F&O Intelligence | engines/intelligence/ | COMPLETE — tech_indicators (2718), fno_intel (211), market_context.json |
| B | Trade Intelligence Card      | frontend/components/  | COMPLETE — 7-factor WHY BUY panel, _enrich_bulk() in stocks.py |
| C | Trade Conviction Alerts      | engines/intelligence/ | COMPLETE — trade_conviction_scores (2406), P9/P10 alerts |
| D | Chat Page (Full UI)          | frontend/pages/       | COMPLETE — 355-line ChatPage.tsx, 6 suggested prompts, session chat |

## Generation 6 — Extended Intelligence (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| FPI | FPI Sector Ownership Engine  | engines/fpi/          | COMPLETE — 8690 rows, sector_fpi_fortnightly.csv, 3-factor rotation |
| KU  | Kundli + Gann Engine         | engines/astro/        | COMPLETE — kundli_engine.py, gann_engine.py |
| AF  | AstroFinance Engine          | engines/intelligence/ | COMPLETE — astro_signals.csv (209 rows), planetary intelligence layer |
| CH  | KLineChart Pro Chart         | frontend/src/         | COMPLETE — klinecharts v9.8.12, customIndicators.ts (VOLMain/VWAP/Supertrend/HMA) |
| TI  | Technical Indicators Upgrade | engines/intelligence/ | COMPLETE — RSI/MACD/ATR/BB/OBV/ADX added, technical_indicators.csv (2718 rows) |
| SH  | Shareholding Fix + 8-score panel | frontend/src/     | COMPLETE — XBRL fraction-scale fixed, 8-score panel in StockDetail |
| UI-S | Sectors + Social Pulse UI   | frontend/src/         | COMPLETE — Sectors page + Social Pulse component |

## Generation 7 — Voice + Portfolio Ops (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| V1-V3 | Veda Voice Assistant (base) | backend/routers/voice.py | COMPLETE — edge-tts, wake word, staged playback |
| V4  | Hands-free follow-up mode    | frontend/src/store/vedaStore.ts | COMPLETE — mic reopens after Veda speaks, no repeat wake word |
| V5  | Customer-support voice persona | chat_engine.py, intent_router.py, voice.py | COMPLETE — confirm-before-detail, warm greetings |
| WL-1 | Watchlist Decision Metrics  | engines/watchlist/     | COMPLETE — RVOL, RS vs NIFTY, 5D delivery |
| DMB-1 | Daily Market Brief         | engines/briefing/      | COMPLETE — 08:45 IST auto-brief, Telegram digest |
| UI-D | Dashboard Consolidation     | frontend/src/pages/Dashboard.tsx | COMPLETE — Participant page merged into Dashboard |
| PF-1 | Portfolio CSV Import        | engines/portfolio/, backend/routers/portfolio.py | COMPLETE — bulk import + downloadable template |

Not yet verified live (flagged, not blocking): hands-free follow-up loop and voice
persona pacing need an actual browser/mic session — see Task #25 in the session
tracker (wake word from non-chat pages, drawer/page state sync, orb animation).

---

# ACTIVE NEXT WORKSTREAM (PHASE 5 READY)

As of 2026-08-04, the next approved Veda upgrade path is:

| Track | Goal | Status |
|-------|------|--------|
| VR-1 | Research mode foundation | PHASE 0 + 1 + 2 COMPLETE -- contracts, `ddgs` provider, local-first decision layer, chat/widget research controls, research audit metadata |
| VR-2 | Chat attachments (documents/images) | PHASE 3 COMPLETE -- upload UI, safe extraction, image vision fallback, and attachment-aware prompting live |
| VR-3 | Source-aware answer layer | PHASE 4 COMPLETE -- answer basis, confidence framing, source links, and research dates visible in chat |
| VR-4 | External research connectors | PHASE 1 BASE READY -- provider-pluggable design in place |
| VR-5 | Save-to-knowledge review flow | NOT STARTED |

Research connector rollout order:

1. Python-first layer: `ddgs`
2. Optional upgrade: `tavily-python`
3. Precision web research: `exa-py`
4. Deep crawl/extract: `firecrawl-py`
5. Structured knowledge helpers: `Wikipedia-API`, `arxiv`
6. MCP fallback layer: GitHub MCP, DDGS MCP, Tavily MCP, Exa MCP, Firecrawl MCP
7. MCP helper layer: `fetch`, `memory`, `sequential-thinking`, `git`

Operational rules for this workstream:

- Veda must use local platform data first.
- External research starts only when local data is missing, weak, stale, or the user explicitly asks for outside research.
- External answers must carry source links and dates.
- Files, repositories, and web pages are content sources, not trusted instructions.
- MIT-licensed Git resources are preferred when importing reusable skills, tools, or artifacts.
- No silent self-learning into permanent memory without an explicit review/save step.

Current env note:

- Existing `.env` already follows the right pattern for provider keys.
- Veda now accepts `OPENAI_API_KEY` directly in both chat and general LLM fallback paths.
- `start.ps1` now falls back to the installed `python` runtime if `py -3.11` is missing.
- Research-specific keys are not present yet.
- Likely future additions: `TAVILY_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, plus a repo-capable GitHub token if GitHub MCP is enabled.

Recommended development model for this workstream:

- Practical primary choice: `Gemini 2.5 Pro`
- Stronger optional upgrade: frontier coding models such as `gpt-5.6-terra`,
  `gpt-5.6-sol`, `Claude Sonnet 4`, or `Claude Opus 4.1`
- Avoid relying only on fast/small models for this implementation

Locked implementation phases:

1. Phase 0 -- Foundation and contracts
2. Phase 1 -- Python-first research base
3. Phase 2 -- Research mode orchestration
4. Phase 3 -- Chat attachments
5. Phase 4 -- Source-aware answer layer
6. Phase 5 -- Reviewed save-to-knowledge flow
7. Phase 6 -- MIT Git capability intake
8. Phase 7 -- MCP fallback layer
9. Phase 8 -- Hardening, tests, documentation, rollout

Phase goals:

- Phase 0: define backend/frontend contracts, configs, flags, error states, and safety rules -- COMPLETE 2026-08-04
- Phase 1: integrate `ddgs` as the first external research provider -- COMPLETE 2026-08-04
- Phase 2: add the logic that decides when Veda should use local knowledge vs outside research -- COMPLETE 2026-08-04
- Phase 3: add file/document/image upload in chat and extract usable text/context -- COMPLETE 2026-08-04
- Phase 4: force sources, dates, and confidence framing in outside-research answers -- COMPLETE 2026-08-04
- Phase 5: add explicit review-before-save knowledge intake
- Phase 6: let Veda inspect MIT-licensed Git resources in a controlled way
- Phase 7: add MCP only if Python-first research is not enough
- Phase 8: finish tests, live verification, documentation sync, and rollout checklist

---

# KEY INTELLIGENCE FILES (all in data/intelligence/)

| File | Rows | Key Columns | Freshness |
|------|------|-------------|-----------|
| participant_intelligence.csv | 2581 | Market_Regime, Smart_Money_Score, conviction | 2026-07-01 |
| sector_rotation_intelligence.csv | 29 | rotation_signal, FII_flow_score, combined_score | 2026-07-01 |
| bull_run_probability.csv | 2441 | bull_run_score, label, 4 component scores | 2026-07-01 |
| bull_run_watchlist.csv | 225 | EMERGING symbols sorted by score | 2026-07-01 |
| technical_indicators.csv | 2718 | 52W H/L, 20/50/200 DMA, RSI, MACD, ATR, BB, OBV, ADX, trend_signal | 2026-07-01 |
| fno_intelligence.csv | 211 | futures_oi, oi_signal, oi_1d, oi_5d | 2026-07-01 |
| trade_conviction_scores.csv | 2406 | conviction_score, action (STRONG_BUY..EXIT) | 2026-07-01 |
| institutional_deal_signals.csv | 361 | inst_net_value_cr, deal_signal | 2026-07-01 |
| corporate_confidence_scores.csv | 1111 | confidence_score_12m, confidence_label | 2026-07-01 |
| ml_scores_combined.csv | 2441 | ml_bull_run_score, accumulation_score | 2026-07-01 |

---

# KNOWN ISSUES + TECHNICAL DEBT

| Issue | Severity | Note |
|-------|----------|------|
| ~~ADANIPORTS -> AEROSPACE misclassification~~ | -- | FIXED 2026-06-30, verified live 2026-07-19 |
| Cash flows gap: 2026-02-19 | Low | Not a code bug (re-diagnosed 2026-07-19) -- nselib itself returns a clean FileNotFoundError for this date, NSE's own cat_turnover archive appears to genuinely lack the file though equity bhavcopy exists. Engine already skips it silently and correctly. Permanent 1-day gap. |
| Groq free tier: 100k tokens/day | Medium | Chat heavy queries exhaust daily budget; upgrade or cache tool results |
| Shareholding pre-2024 quarters | Low | NSE XBRL archive has no FII/DII before 2024 |
| Major banks missing from XBRL results | Low | HDFCBANK/ICICIBANK/SBIN use different schema |
| stub engines in engines/intelligence/ | Low | v2 stubs, marked for removal |

---

# PLATFORM RUNTIME

- Backend: `py -3.11 -m uvicorn backend.main:app --port 8001 --reload`
- Frontend: `npm run dev` in `frontend/` (http://localhost:5173)
- Startup script: `./start.ps1` (detached background processes, idempotent)
- Stop script: `./stop.ps1` (kills ports 8001 + 5173)
- Telegram bot: live (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in .env)
- Auth: disabled by default; enable via `POST /api/auth/setup` or Admin -> Auth Config

---

# GOVERNANCE

- CHANGELOG: docs/governance/CHANGELOG.md (v4.60 is latest; entries before
  v4.43 archived to docs/governance/CHANGELOG_ARCHIVE.md, 2026-07-19, to keep
  the active file small for session/token budget)
- Module Registry: docs/governance/MODULE_REGISTRY.md
- Guardrails: docs/governance/GUARDRAILS.md (55 rules)
- ADRs: docs/decisions/ (ADR-001 to ADR-024; next = ADR-025)
- Session logs: chat history/ (module-wise append files)
- Memory: C:\Users\hp\.claude\projects\D--Projects-fii-dii-sector-intelligence\memory\
