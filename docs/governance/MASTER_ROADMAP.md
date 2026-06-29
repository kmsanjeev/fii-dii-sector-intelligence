# MASTER ROADMAP
## Capital Flow Intelligence Platform | Updated 2026-06-30

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

## Generation 3 — Application Layer (CURRENT FOCUS 2026)
Alert delivery, GUI, ML models, conversational AI.
Phases 9-16.

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

## PHASE 9 — Alert System | NEXT (Priority 1)
Telegram bot with 7 alert types: regime change, STRONG_CANDIDATE, block deal,
sector rotation, upcoming catalyst, smart money divergence, daily digest.
Location: alerts/
Stack: python-telegram-bot v21, APScheduler 3

## PHASE 10 — FastAPI Backend | Priority 2
REST API + WebSocket for all intelligence data. Enables GUI.
12 routes covering market, sectors, stocks, participant, corporate, chat.
Location: backend/
Stack: FastAPI, Uvicorn, Pydantic

## PHASE 11 — React GUI | Priority 3 (needs Phase 10)
10-page dark terminal UI. Score-first layout.
Location: frontend/
Stack: React 18 + TypeScript + Vite, Tailwind, TanStack Query, Recharts

## PHASE 12 — ML Intelligence Layer | Priority 4 (independent)
4 models: Accumulation Detector (XGBoost), Bull Run Model (LGB+XGB ensemble),
Sector Rotation Predictor (LightGBM multi-class), Anomaly Detector (Isolation Forest).
Location: engines/ml/
Stack: XGBoost, LightGBM, scikit-learn, SHAP, PyArrow

## PHASE 13 — RAG Knowledge Base | Priority 5 (independent)
FAISS + BM25 hybrid retrieval over 6 domain indexes.
Location: engines/ai/knowledge/
Stack: faiss-cpu, sentence-transformers, rank-bm25

## PHASE 14 — Chatbot (Claude API) | Priority 6 (needs Phase 10 + 13)
5 specialized agents + tool registry for live data access.
Location: engines/ai/chatbot/
Stack: anthropic SDK, FastAPI WebSocket

## PHASE 15 — Financial Results Engine | Priority 7 (data enrichment)
Quarterly revenue, PAT, EPS, P/E via yfinance (XBRL workaround).
Location: engines/fundamentals/
Stack: yfinance, pandas

## PHASE 16 — Management Intelligence | Priority 8 (needs Phase 14)
Promoter/FII/DII holding trends + Claude API tone scoring on announcements.
Location: engines/management/
Stack: anthropic SDK, nselib announcements

---

# LONG-TERM VISION (Generation 4)

After Phases 9-16:
- Portfolio engine: position sizing, exposure tracking
- Execution platform: Zerodha / Dhan / Upstox broker adapters
- Research platform: investment thesis library, validation framework
- Commercial platform: auth, subscriptions, multi-user

---

# CURRENT SPRINT (2026-06-30)

Active target: Phase 9 — Alert System
Next: Phase 10 — FastAPI Backend
After: Phase 11 — React GUI

Intelligence cascade complete. Now building the delivery and interaction layers.
