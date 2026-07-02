# FII-DII SECTOR INTELLIGENCE PLATFORM
# MASTER PROJECT STATE
# Version 4.6 | 2026-07-02

---

# PROJECT MISSION

Build India's most advanced institutional-grade market intelligence platform capable of
identifying capital flow (Participant -> Sector -> Theme -> Stock) before broad market recognition.

Core cascade:
  FII/DII/PRO/CLIENT -> Sector Attribution -> Corporate Signals -> Stock Scoring -> Alert/Chatbot/Execution

This project is NOT a screener. It IS a decision intelligence platform.

---

# CURRENT PLATFORM STATE (2026-07-02)

**ALL 25 CORE PHASES + A/B/C/D COMPLETE. Full investment operating system is live.**

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
| 11 | React GUI                  | frontend/             | COMPLETE — 14 pages, Charts, TradingView OHLCV, IST timestamps |
| 12 | ML Intelligence Layer      | engines/ml/           | COMPLETE — XGBoost+LightGBM, 24 features, 4 model outputs |
| 13 | RAG Knowledge Base         | engines/ai/knowledge/ | COMPLETE — FAISS+BM25, 6 domain indexes, hybrid RRF retrieval |
| 14 | Chatbot (Groq API)         | engines/ai/chatbot/   | COMPLETE — Groq llama-3.3-70b, 11 tools, /api/chat |
| 15 | Financial Results + SHP    | engines/fundamentals/ | COMPLETE — 4181 XBRL rows, 7228 shareholding rows |
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
| A | Technical + F&O Intelligence | engines/intelligence/ | COMPLETE — tech_indicators (2717), fno_intel (211), market_context.json |
| B | Trade Intelligence Card      | frontend/components/  | COMPLETE — 7-factor WHY BUY panel, _enrich_bulk() in stocks.py |
| C | Trade Conviction Alerts      | engines/intelligence/ | COMPLETE — trade_conviction_scores (2406), P9/P10 alerts |
| D | Chat Page (Full UI)          | frontend/pages/       | COMPLETE — 355-line ChatPage.tsx, 6 suggested prompts, session chat |

---

# KEY INTELLIGENCE FILES (all in data/intelligence/)

| File | Rows | Key Columns | Freshness |
|------|------|-------------|-----------|
| participant_intelligence.csv | 2581 | Market_Regime, Smart_Money_Score, conviction | 2026-07-01 |
| sector_rotation_intelligence.csv | 29 | rotation_signal, FII_flow_score, combined_score | 2026-07-01 |
| bull_run_probability.csv | 2441 | bull_run_score, label, 4 component scores | 2026-07-01 |
| bull_run_watchlist.csv | 225 | EMERGING symbols sorted by score | 2026-07-01 |
| technical_indicators.csv | 2717 | 52W H/L, 20/50/200 DMA, trend_signal | 2026-07-01 |
| fno_intelligence.csv | 211 | futures_oi, oi_signal, oi_1d, oi_5d | 2026-07-01 |
| trade_conviction_scores.csv | 2406 | conviction_score, action (STRONG_BUY..EXIT) | 2026-07-01 |
| institutional_deal_signals.csv | 361 | inst_net_value_cr, deal_signal | 2026-07-01 |
| corporate_confidence_scores.csv | 1111 | confidence_score_12m, confidence_label | 2026-07-01 |
| ml_scores_combined.csv | 2441 | ml_bull_run_score, accumulation_score | 2026-07-01 |

---

# KNOWN ISSUES + TECHNICAL DEBT

| Issue | Severity | Note |
|-------|----------|------|
| ADANIPORTS -> AEROSPACE misclassification | Low | industry_master override coverage |
| Cash flows gap: 2026-02-19 | Low | tz-aware/naive mixing in NSE API response |
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

- CHANGELOG: docs/governance/CHANGELOG.md (v4.6 is latest)
- Module Registry: docs/governance/MODULE_REGISTRY.md
- Guardrails: docs/governance/GUARDRAILS.md (55 rules)
- ADRs: docs/decisions/ (ADR-001 to ADR-021; next = ADR-022)
- Session logs: chat history/ (module-wise append files)
- Memory: C:\Users\hp\.claude\projects\D--Projects-fii-dii-sector-intelligence\memory\
