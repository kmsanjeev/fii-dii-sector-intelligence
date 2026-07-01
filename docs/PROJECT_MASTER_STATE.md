# FII-DII SECTOR INTELLIGENCE PLATFORM
# MASTER PROJECT STATE
# Version 3.12 | 2026-07-02

---

# PROJECT MISSION

Build India's most advanced institutional-grade market intelligence platform capable of
identifying capital flow (Participant -> Sector -> Theme -> Stock) before broad market recognition.

Core cascade:
  FII/DII/PRO/CLIENT -> Sector Attribution -> Corporate Signals -> Stock Scoring -> Alert/Chatbot

This project is NOT a screener. It IS a decision intelligence platform.

---

# CURRENT PLATFORM STATE (2026-06-30)

## Intelligence Cascade: COMPLETE
All four core intelligence layers are operational and producing daily outputs.

```
Layer 1: Participant Intelligence  (5A/5B/5C)  LIVE through 2026-06-29
Layer 2: Sector Rotation           (6A/6B/6C)  LIVE through 2026-06-02
Layer 3: Corporate Intelligence    (7A/7B/7C)  LIVE through 2026-06-29
Layer 4: Stock Scoring             (8A/8B)     LIVE through 2026-06-10
```

## Market Snapshot (as of 2026-06-29)
- Market Regime: NEUTRAL (x0.90 multiplier)
- Smart Money Score: -4.7 | FII conviction: 40% (8/20 sessions)
- DII conviction: 65% | Smart/Retail divergence: -14.0
- Bull run watchlist: 225 EMERGING symbols
- Top EMERGING: ADANIENSOL (62), ADANIENT (57), GMRAIRPORT (56)
- Sector rotation leaders: CAPITAL_GOODS, DEFENCE, HEALTHCARE (EARLY_ROTATION)

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
| 5A | Participant Acquisition | cash_market_flows_history.csv | 609 | COMPLETE |
| 5B | Participant Flow Engine | participant_flow_scores.csv | 2581 | COMPLETE |
| 5C | Participant Intelligence | participant_intelligence.csv | 2581 | COMPLETE |
| 6A | Sector Capital Flow | sector_capital_flows.csv | 74269 | COMPLETE |
| 6B | Sector Flow Scores | sector_flow_scores.csv | 74269 | COMPLETE |
| 6C | Sector Rotation Intel | sector_rotation_intelligence.csv | 29 | COMPLETE |
| 7A | Block/Bulk Deals | institutional_deal_signals.csv | 361 signals | COMPLETE |
| 7B | Event Calendar | event_calendar.csv + upcoming_catalysts.csv | 33851 | COMPLETE |
| 7C | Corporate Actions | corporate_confidence_scores.csv | 1111 | COMPLETE |
| 8A | Price Momentum | price_momentum.csv | 2441 | COMPLETE |
| 8B | Bull Run Probability | bull_run_probability.csv + watchlist | 2441 | COMPLETE |

## Application Layer (COMPLETE)
| Phase | What | Location | Status |
|-------|------|----------|--------|
| 9  | Alert System (Telegram)    | alerts/               | COMPLETE (7 alert types, APScheduler, 118 alerts on first run) |
| 10 | FastAPI Backend            | backend/              | COMPLETE (16 endpoints, port 8001, WebSocket live ticker) |
| 11 | React GUI + Charts         | frontend/             | COMPLETE (10 pages + Charts page, TradingView OHLCV, IST timestamps) |
| 12 | ML Intelligence Layer      | engines/ml/           | COMPLETE (XGBoost+LightGBM, 24 features, 4 model outputs) |
| 13 | RAG Knowledge Base         | engines/ai/knowledge/ | COMPLETE (FAISS+BM25, 6 domain indexes, hybrid RRF) |
| 14 | Chatbot (Claude API)       | engines/ai/chatbot/   | COMPLETE (4 agents, tool registry, /api/chat) |
| 15 | Financial Results + SHP    | engines/fundamentals/ | COMPLETE (4181 XBRL rows, 4 quarters shareholding) |
| 16 | Management Intelligence    | engines/management/   | COMPLETE (holding trends, announcements, Claude sentiment) |

## Generation 4 — Investment Operating System (CURRENT FOCUS)
| Phase | What | Location | Depends On | Status |
|-------|------|----------|------------|--------|
| 17 | Daily Intelligence Refresh | engines/orchestration/ | Phases 1-16 | NOT STARTED <- NEXT |
| 18 | Portfolio Engine           | engines/portfolio/     | Phase 17   | NOT STARTED |
| 19 | Backtesting Framework      | engines/backtest/      | Phase 18   | NOT STARTED |
| 20 | Broker Adapter (R/O)       | engines/broker/        | Phase 18   | NOT STARTED |
| 21 | Research Platform          | engines/research/      | 18 + 19    | NOT STARTED |
| 22 | Execution Platform         | engines/execution/     | 19 + 20    | NOT STARTED |
| 23 | Commercial Platform        | backend/auth/          | 17-22 done | NOT STARTED |

---

# KEY INTELLIGENCE FILES (all in data/intelligence/)

| File | Rows | Key Columns | Freshness |
|------|------|-------------|-----------|
| participant_intelligence.csv | 2581 | Market_Regime, Smart_Money_Score, conviction | 2026-06-29 |
| sector_rotation_intelligence.csv | 29 | rotation_signal, FII_flow_score, combined_score | 2026-06-02 |
| bull_run_probability.csv | 2441 | bull_run_score, label, 4 component scores | 2026-06-10 |
| bull_run_watchlist.csv | 225 | EMERGING symbols sorted by score | 2026-06-10 |
| institutional_deal_signals.csv | 361 | inst_net_value_cr, deal_signal | 2026-06-29 |
| corporate_confidence_scores.csv | 1111 | confidence_score_12m, confidence_label | 2026-06-29 |
| upcoming_catalysts.csv | 12 | next 60D events with catalyst_score | 2026-06-29 |

---

# KNOWN ISSUES + TECHNICAL DEBT

| Issue | Severity | Owner | Note |
|-------|----------|-------|------|
| ADANIPORTS -> AEROSPACE misclassification | Low | Industry master | Low priority |
| Cash flows gap: 2026-02-19 | Low | participant_acquisition_engine.py | tz-aware fix needed |
| Sector rotation intel stale (2026-06-02) | Medium | Run sector_capital_flow_engine.py | bhavcopy latest = 2026-06-10 |
| XBRL financial results endpoint 404 | Medium | Phase 15 | Use yfinance workaround |
| stub engines in engines/intelligence/ | Low | Cleanup | v2 stubs, marked for removal |

---

# PLATFORM RUNTIME

- Backend: `py -3.11 -m uvicorn backend.main:app --port 8001 --reload`
- Frontend: `cd frontend && npm run dev` (http://localhost:5173)
- Startup script: `./start.ps1` (detached background processes, idempotent)
- Stop script: `./stop.ps1` (kills ports 8001 + 5173)
- Telegram bot: live (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in .env)

# KNOWN ISSUES + TECHNICAL DEBT

| Issue | Severity | Note |
|-------|----------|------|
| ADANIPORTS -> AEROSPACE misclassification | Low | industry_master override coverage |
| Cash flows gap: 2026-02-19 | Low | tz-aware/naive mixing in NSE API response |
| Shareholding pre-2024 quarters | Low | NSE XBRL archive has no FII/DII before 2024 |
| Major banks missing from XBRL results | Low | HDFCBANK/ICICIBANK/SBIN use different schema |

# GOVERNANCE

- CHANGELOG: docs/governance/CHANGELOG.md (v3.12 is latest)
- Module Registry: docs/governance/MODULE_REGISTRY.md
- Guardrails: docs/governance/GUARDRAILS.md (55 rules)
- ADRs: docs/decisions/ (ADR-001 to ADR-021; next = ADR-022)
- Session logs: chat history/ (module-wise append files)
- Memory: C:/Users/hp/.claude/projects/*/memory/ (auto-loaded)
