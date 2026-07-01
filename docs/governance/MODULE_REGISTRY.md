# MODULE REGISTRY

## Project

Capital Flow Intelligence Platform

---

# Purpose

The Module Registry serves as the master inventory of all platform modules.

It provides:

* Module Ownership
* Module Scope
* Module Status
* Completion Percentage
* Dependencies
* Development Priority
* Roadmap Visibility

This document acts as the authoritative reference for platform development planning.

---

# Module Classification Framework

---

## ADVANCED

Completion:

75% – 100%

Production-grade foundation completed.

---

## ACTIVE DEVELOPMENT

Completion:

40% – 74%

Core functionality exists and is expanding.

---

## FOUNDATION COMPLETE

Completion:

10% – 39%

Architecture and documentation complete.

Implementation largely pending.

---

## PLANNED

Completion:

0% – 9%

Research and planning stage.

---

# Core Intelligence Modules

---

# Module 01

Participant Intelligence

---

## Category

Core Intelligence

---

## Status

ACTIVE — PHASE 6 COMPLETE

---

## Completion

100%

---

## Priority

Very High

---

## Purpose

Analyze behavior of:

* FII
* DII
* PRO
* CLIENT

and identify:

* Participation
* Conviction
* Divergence
* Smart Money Activity
* Retail Sentiment

---

## Outputs

Participant Flow Scores (data/intelligence/participant_flow_scores.csv)

Participant Intelligence (data/intelligence/participant_intelligence.csv)

Cash Market Flows History (data/historical/institutional/cash_market_flows_history.csv)

---

## Engines (Phase 5 + Phase 6 — COMPLETE)

participant_acquisition_engine.py — 5A: incremental downloader for F&O + cash market data

participant_flow_engine.py — 5B: OI delta, rolling 5D/20D/60D sums, z-score flow scores

participant_intelligence_engine.py — 5C: conviction, smart money, divergence, market opportunity, regime

sector_capital_flow_engine.py — 6A: weight-allocate FII/DII/PRO/CLIENT flows to 29 sectors via bhavcopy turnover weights

sector_flow_score_engine.py — 6B: rolling 5D/20D/60D sums + z-score scores per sector per participant

sector_rotation_intelligence_engine.py — 6C: rotation signal, capital flow alignment, combined rank (snapshot + history)

---

## Dependencies

Institutional Intelligence

---

# Module 02

Institutional Intelligence

---

## Category

Core Intelligence

---

## Status

COMPLETE — Phase 5 (2026-06-30)

---

## Completion

100%

---

## Priority

Very High

---

## Purpose

Generate institutional positioning intelligence.

---

## Existing Engines

Historical Engine

Backfill Engine

Integrity Engine

Regime Engine

Trend Engine

---

## Future Engines

Flow Engine

Conviction Engine

Participant Integration Layer

---

# Module 03

Sector Intelligence

---

## Category

Core Intelligence

---

## Status

COMPLETE — Phase 6 (2026-06-30)

---

## Completion

100%

---

## Priority

Very High

---

## Purpose

Identify sector-level capital movement.

---

## Completed Engines (Phase 6)

sector_capital_flow_engine.py — 6A: turnover-weighted FII/DII attribution to 29 sectors, 74269 rows 2016-2026

sector_flow_score_engine.py — 6B: rolling 5D/20D/60D scores per sector

sector_rotation_intelligence_engine.py — 6C: rotation_signal, combined_score, capital_flow_alignment

---

## Earlier Engines

Sector Heatmap, Sector Persistence, Sector Conviction, Leadership Duration

---

## Dependencies

Participant Intelligence

Institutional Intelligence

---

# Module 04

Theme Intelligence

---

## Category

Core Intelligence

---

## Status

FOUNDATION COMPLETE

---

## Completion

35%

---

## Priority

High

---

## Purpose

Identify thematic capital movement.

---

## Existing Engines

Theme Heatmap

Theme Persistence

---

## Planned Engines

Theme Rotation Engine

Theme Capital Flow Engine

Theme Momentum Engine

Theme Leadership Engine

Theme Opportunity Engine

---

## Dependencies

Sector Intelligence

---

# Module 05

Stock Intelligence

---

## Category

Core Intelligence

---

## Status

ACTIVE — PHASE 8 COMPLETE

---

## Completion

40%

---

## Priority

Very High

---

## Purpose

Identify stock-level beneficiaries of capital flow.

---

## Completed Engines (Phase 8 — 2026-06-30)

price_momentum_engine.py — 8A: per-symbol returns (30D/60D/90D/365D), volume ratio, sector-relative strength, percentile-ranked price_score (0-100), 2441 symbols

bull_run_probability_engine.py — 8B: multi-factor bull run score combining price (30%) + sector flow (25%) + institutional deal (25%) + corporate confidence (20%); market regime multiplier; STRONG_CANDIDATE / EMERGING / WATCHLIST / NEUTRAL / AVOID labels

---

## Outputs (Phase 8)

data/intelligence/price_momentum.csv — 2441 symbols, price_score + returns + vol_ratio + sector_rel

data/intelligence/bull_run_probability.csv — 2441 symbols, bull_run_score + component scores + label

data/intelligence/bull_run_watchlist.csv — STRONG_CANDIDATE + EMERGING symbols only

---

## Remaining Engines

Relative Strength Engine

Accumulation / Distribution Engine

Delivery Intelligence Engine

F&O Intelligence Engine

Leadership Engine (within-sector)

---

## Dependencies

Fundamental Intelligence (Phase 4 — complete)

Participant Intelligence (Phase 5 — complete)

Sector Rotation Intelligence (Phase 6 — complete)

Corporate Intelligence (Phase 7 — complete)

---

# Module 06

Fundamental Intelligence

---

## Category

Core Intelligence

---

## Status

COMPLETE (Phases 15+16, 2026-07-01)

---

## Completion

85%

---

## Priority

High

---

## Purpose

Explain why capital is moving.

---

## Completed Engines (Phase 15+16)

financial_results_engine.py -- Phase 15A: 4181 rows NSE XBRL P&L, 2084 symbols
valuation_engine.py -- Phase 15B: P/E, ROE, valuation_label scoring
shareholding_engine.py -- Phase 15C: quarterly_shp.csv, 4 quarters, 98.9% FII coverage
holding_trend_engine.py -- Phase 16: QoQ deltas, 7 conviction signals
announcement_fetcher.py -- Phase 16: 527 board announcements, 8-type classification
management_sentiment_engine.py -- Phase 16: Claude API tone scoring, 471 symbols

## Remaining (15%)

Order Book Intelligence (future)
Extended shareholding backfill (pre-2024 limited by NSE XBRL archive availability)

---

## Dependencies

Stock Intelligence

---

# Platform Modules

---

# Module 07

AI Platform

---

## Category

Platform

---

## Status

FOUNDATION COMPLETE

---

## Completion

15%

---

## Priority

High

---

## Purpose

Provide AI-powered analysis and interaction.

---

## Planned Agents

AI Market Analyst

AI Participant Analyst

AI Sector Analyst

AI Theme Analyst

AI Stock Analyst

AI Fundamental Analyst

AI Portfolio Manager

AI Research Assistant

AI Development CTO

---

# Module 08

GUI Platform

---

## Category

Platform

---

## Status

ACTIVE DEVELOPMENT

---

## Completion

25%

---

## Priority

Medium

---

## Purpose

Provide visualization and user interaction.

---

## Architecture

Full spec: `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` (2026-06-29)

Stack: React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query + Zustand + React Router v6
Charts: Recharts + TradingView Lightweight Charts
Backend: FastAPI + Uvicorn
Real-time: WebSocket live flow ticker

Build phases: GUI-1 (AppShell) through GUI-13 (Auth). Start with GUI-1.
Dependency: GUI-4 requires Phase 4A (Company Fundamentals Master Engine) to be complete first.

---

## Planned Components

Dashboard Framework (Capital Flow Cascade, Regime Card, Flow Cards)

Heatmap Framework (Sector Treemap, Theme Heatmap)

OHLCV Charts (TradingView Lightweight Charts with overlay panes)

Capital Flow Cascade (Sankey: Market→Sector→Theme→Stock)

AI Chat Interface (AI Analyst modes)

Mobile Platform (bottom nav, card-based layouts)

Portfolio Dashboard (sector/theme exposure, risk matrix)

Report Center (daily/weekly/monthly reports)

---

# Module 09A

Symbol Change History (Phase 17)

---

## Category

Platform — Foundation

---

## Status

PLANNED — Phase 17 (NEXT BUILD)

---

## Completion

0%

---

## Priority

Very High (data integrity prerequisite for all backtesting)

---

## Purpose

Download and maintain NSE historical symbol rename records. 1038 renames on file
(e.g., IIFLWAM -> 360ONE, BIRLA3M -> 3MINDIA). Without this, historical bhavcopy
lookups for renamed symbols return empty data, causing silent errors in backtesting.

---

## Files

engines/foundation/symbol_change_engine.py
data/NSE/equity_master/symbol_change_history.csv (company_name, old_symbol, new_symbol, change_date)

## Source

NSE archives open endpoint — no auth required. ~1038 records.

---

# Module 09B

Corporate Announcements Intelligence (Phase 18)

---

## Category

Platform — Corporate Intelligence

---

## Status

PLANNED — Phase 18 (after Phase 17)

---

## Completion

0%

---

## Priority

Very High

---

## Purpose

Download and classify NSE corporate announcements (entirely separate from corporate actions).
Provides qualitative management signals: Press Releases, Analyst/FII Meet outcomes,
Board Meeting outcomes, SEBI Takeover + Insider Trading disclosures, Trading Window closures.
Scale: RELIANCE=3313, TCS=3321, HDFCBANK=2306 announcements each.

---

## Files

engines/corporate/announcement_intelligence_engine.py
data/intelligence/company_announcements.csv (50,000+ rows expected)
data/intelligence/announcement_signals.csv (per-symbol scores)

## Source

NSE API: GET /api/corporate-announcements?index=equities&symbol={symbol}

---

# Module 09

Daily Intelligence Refresh (Phase 19)

---

## Category

Platform — Orchestration

---

## Status

PLANNED — Phase 19 (after Phases 1-18)

---

## Completion

0%

---

## Priority

Very High (blocker for all Gen4 portfolio/backtest modules)

---

## Purpose

Run all intelligence engines automatically every market day after 18:00 IST.
Transforms the platform from a static report into a live capital flow radar.

---

## Engine Pipeline (in order)

5A participant_acquisition -> 6A/6B/6C sector flows -> 7A block/bulk deals
-> 18 announcement_intelligence -> 8A price_momentum -> 8B bull_run_probability
-> 12 ml_scorer -> 13 RAG index_updater -> 9 alert_engine

## Files

engines/orchestration/daily_refresh.py -- ordered pipeline, per-stage error isolation
engines/orchestration/refresh_scheduler.py -- APScheduler 18:00 IST weekday trigger
engines/orchestration/refresh_monitor.py -- staleness checker, refresh_log.csv output

---

# Generation 4 Modules

---

# Module 10

Portfolio Engine (Phase 20)

---

## Category

Platform — Investment

---

## Status

PLANNED — Phase 20 (after Phase 19)

---

## Completion

0%

---

## Priority

High

---

## Purpose

Track real positions against intelligence signals. Sector/theme exposure analysis
and unrealised P&L from bhavcopy parquet cache prices.

---

## Files

engines/portfolio/position_engine.py
engines/portfolio/exposure_engine.py
engines/portfolio/pnl_engine.py
backend/routers/portfolio.py
data/portfolio/positions.csv, portfolio_snapshot.csv
Frontend Portfolio page

---

# Module 11

Backtesting Framework (Phase 21)

---

## Category

Platform — Validation

---

## Status

PLANNED — Phase 21 (after Phase 20)

---

## Completion

0%

---

## Priority

High (gate before live execution)

---

## Purpose

Replay historical bull_run signals against actual returns. Quantify signal quality
before any real capital is deployed. Hard prerequisite for Phase 22.

---

## Files

engines/backtest/signal_backtester.py
engines/backtest/strategy_engine.py
engines/backtest/performance_engine.py
data/intelligence/backtest_results.csv, strategy_performance.csv
Frontend Backtest page

---

# Module 12

Broker Adapter — Read-Only (Phase 22)

---

## Category

Platform — Integration

---

## Status

PLANNED — Phase 22 (after Phase 20)

---

## Completion

0%

---

## Priority

High

---

## Purpose

Sync live Zerodha positions into portfolio engine. Abstract adapter interface
(BrokerAdapter base class) ensures Dhan/Upstox can plug in later.

---

## Files

engines/broker/base_adapter.py
engines/broker/zerodha_adapter.py (Kite Connect)
engines/broker/position_sync.py
Env: ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_ACCESS_TOKEN

---

# Module 13

Research Platform (Phase 23)

---

## Category

Platform — Research

---

## Status

PLANNED — Phase 23 (after Phase 20 + 21)

---

## Completion

0%

---

## Priority

Medium

---

## Purpose

Investment thesis library. Record reasoning per position, auto-validate quarterly
against financial results, shareholding changes, and management signals.

---

## Files

engines/research/thesis_engine.py
engines/research/thesis_validator.py
engines/research/report_engine.py (weekly Telegram digest + PDF)
data/research/theses.csv, thesis_scores.csv
Frontend Research page

---

# Module 14 (was Execution Platform — renamed for Gen4)

Execution Platform — Live Trading (Phase 24)

---

## Category

Platform — Execution

---

## Status

PLANNED — Phase 24 (after Phase 21 + 22, paper-trade gate required)

---

## Completion

0%

---

## Priority

Medium

---

## Purpose

Place real orders via broker adapter. Paper mode must run 4 weeks (Sharpe > 0.8)
before live_trader.py is enabled by LIVE_TRADE_MODE=true.

---

## Files

engines/execution/paper_trader.py
engines/execution/order_manager.py (state machine)
engines/execution/risk_engine.py (limits, concentration, drawdown stop)
engines/execution/live_trader.py (gate: LIVE_TRADE_MODE=true)
Frontend Execution page (order blotter, risk dashboard)

---

# Module 15 (was Commercial Platform — renumbered for Gen4)

Commercial Platform (Phase 25)

---

## Category

Platform — Commercial

---

## Status

PLANNED — Phase 25 (after Phases 19-24 stable)

---

## Completion

0%

---

## Priority

Low (last phase)

---

## Purpose

Multi-user productization: JWT auth, plan tiers, per-user data isolation, payments.

---

## Files

backend/auth/ (JWT, bcrypt, user CRUD)
backend/subscriptions/ (Free/Pro/Institutional tiers, feature gates)
frontend/auth/ (login, subscription management)
Stripe or equivalent payment integration

---

# Module 14

ML Intelligence Layer

---

## Category

AI / ML

---

## Status

COMPLETE (Phase 12, 2026-06-30)

---

## Completion

100%

---

## Priority

High

---

## Purpose

Replace heuristic scoring with trained ML models for accumulation detection, sector rotation prediction, bull run probability, company classification, and anomaly detection.

---

## Planned Models

Accumulation Detection Model (XGBoost + LightGBM ensemble)

Sector Rotation Prediction Model (LightGBM multi-class, 29 sectors)

Bull Run Probability Model (Ensemble: XGBoost + LightGBM + Logistic)

Anomaly Detection Model (Isolation Forest + Z-Score)

Company Classification Model (NLP via sentence-transformers + cosine similarity)

Feature Engineering Pipeline (shared across all models)

---

## Key Features (Accumulation Model)

volume_ratio_20d, delivery_pct, fii_net_5d, dii_net_5d, pro_net_5d, rsi_14, rs_vs_nifty50_20d, oi_change_pct, pcr

Target: price_up_10pct_in_20d (binary)

---

## Planned Engines

engines/ml/accumulation_model.py

engines/ml/sector_rotation_model.py

engines/ml/bull_run_model.py

engines/ml/anomaly_detector.py

engines/ml/classification_model.py

engines/ml/feature_engineering.py

engines/ml/model_registry.py

---

## Build Phases

ML-1: Feature engineering pipeline (after Phase 4A)

ML-2: Accumulation detection model

ML-3: Company classification model (NLP)

ML-4: Sector rotation prediction model

ML-5: Bull run probability model (ensemble)

ML-6: Anomaly detection model

---

## Data Paths

data/intelligence/ml_features/ — pre-computed features (Parquet, date-partitioned)

data/intelligence/ml_models/ — trained model artifacts (.pkl)

data/intelligence/scores/ — daily ML scores per symbol

---

## Dependencies

Fundamental Intelligence (Module 06)

Stock Intelligence (Module 05)

Phase 4A must be complete before ML-1 can start

---

## Architecture Reference

docs/architecture/ML_AI_CHATBOT_ARCHITECTURE.md (Section 2)

---

# Module 15

AI Knowledge Base (RAG)

---

## Category

AI / ML

---

## Status

COMPLETE (Phase 13, 2026-06-30)

---

## Completion

100%

---

## Priority

High

---

## Purpose

Index all platform intelligence outputs into a FAISS vector store with hybrid retrieval (dense + BM25) so AI agents can retrieve verified, platform-specific context before generating answers.

---

## Planned Components

FAISS Vector Indexer (6 domain indexes: market, sectors, themes, stocks, fundamentals, research)

Sentence-transformers Embedder

Hybrid Retriever (Dense + BM25 → Reciprocal Rank Fusion)

Context Builder (assembles retrieved chunks into LLM prompts)

Document Chunker (splits intelligence outputs by type and frequency)

---

## Indexed Sources

Daily institutional flow summaries

Sector / theme heatmaps and scores

Stock accumulation scores

Quarterly financial results

Corporate action events

Market regime history (rolling 90-day window)

Research reports

---

## Build Phases

RAG-1: FAISS indexer + embedder

RAG-2: Hybrid retriever (dense + BM25)

RAG-3: Context builder + prompt assembly

---

## Data Paths

data/intelligence/rag/ — FAISS indexes (market.faiss, sectors.faiss, themes.faiss, stocks.faiss, fundamentals.faiss, research.faiss)

---

## Dependencies

All intelligence engines (Modules 01–06)

ML Intelligence (Module 14) — ML scores indexed here

RAG-1 can start after Phase 3B outputs exist (available now)

---

## Engines Directory

engines/ai/knowledge/

---

## Architecture Reference

docs/architecture/ML_AI_CHATBOT_ARCHITECTURE.md (Section 3)

---

# Module 16

Chatbot Platform

---

## Category

AI / ML

---

## Status

COMPLETE (Phase 14, 2026-06-30)

---

## Completion

100%

---

## Priority

High

---

## Purpose

Conversational AI interface that routes user queries to 7 specialized agents backed by live data tools, platform RAG, and Claude API (claude-sonnet-4-6).

---

## Planned Components

Intent Router (regex + LLM-based classification → agent mapping)

7 Specialized Agents (Market, Sector, Theme, Stock, Portfolio, Research, Dev CTO)

Tool Registry (live data access mid-conversation: sector flows, stock scores, market regime)

Conversation Memory (short-term: last 20 turns; long-term: user preferences)

WebSocket Session Management (/ws/chat/{session_id})

React Chat UI (GUI-9 in GUI plan)

Claude API Integration (claude-sonnet-4-6 / claude-opus-4-8 for deep analysis)

---

## Example Interactions

"Which sectors are seeing FII accumulation this week?" → sector_agent → RAG + live tool call

"Why is RELIANCE moving up?" → stock_agent → accumulation score + FII flow + corporate events

"Review my portfolio: RELIANCE×100, HDFCBANK×200, TCS×50" → portfolio_agent → exposure analysis

---

## Build Phases

CB-1: Intent router + base agent

CB-2: All 7 specialized agents

CB-3: Tool registry (live data)

CB-4: Conversation memory

CB-5: WebSocket session management

CB-6: React chat UI integration (GUI-9)

---

## Dependencies

AI Knowledge Base (Module 15)

GUI Platform (Module 08, GUI-9)

ANTHROPIC_API_KEY env var (never hardcoded)

---

## Engines Directory

engines/ai/chatbot/

---

## Architecture Reference

docs/architecture/ML_AI_CHATBOT_ARCHITECTURE.md (Section 4)

---

# Current Development Priority (2026-07-02)

Phase 17 (Symbol Change History) — engines/foundation/ — BUILD NOW

Strict build order: 17 -> 18 -> 19 -> 20 -> 21 -> 22 -> 23 -> 24 -> 25

---

# Current Platform Completion

Intelligence Cascade (Phases 1-8):           100%
Application + AI Layer (Phases 9-16):         88%  (Phases 13/14/15/16 have output gaps)
Investment Operating System (Phases 17-25):    0%
Platform Overall: ~48% of full vision complete

---

# Current Focus

The current development objective is:

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

capital flow discovery.

All near-term development efforts should support this objective.

---

# Long-Term Vision

Build a complete Capital Flow Intelligence Platform capable of:

Tracking Capital

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

# Module 17

Alert System

---

## Category

Application Layer

---

## Status

COMPLETE (Phase 9, 2026-06-30)

---

## Completion

100%

---

## Priority

Very High

---

## Purpose

Push distilled intelligence to the user as Telegram notifications without requiring app access.
7 alert types covering regime changes, bull run signals, block deals, sector rotation, catalysts, and daily digest.

---

## Planned Engines

alerts/alert_engine.py — evaluate 7 alert conditions, generate alert objects with priority

alerts/alert_store.py — JSON cooldown tracking, dedup by (symbol, alert_type), 48h cooldown

alerts/telegram_bot.py — send + format messages, handle /mute /watchlist /regime commands

alerts/daily_digest.py — build daily summary at 18:30 IST (regime + sectors + stocks)

alerts/alert_scheduler.py — APScheduler: digest at 18:30, signal checks at 19:00 IST

---

## Alert Types (Priority Order)

P1 CRITICAL: Market regime change (DISTRIBUTION -> NEUTRAL etc.)

P2 HIGH: New STRONG_CANDIDATE (bull_run_score >= 65)

P3 HIGH: Large block/bulk deal (inst_net_value_cr > 100Cr)

P4 MEDIUM: Sector rotation signal (EARLY_ROTATION or STRONG_ACCUMULATION)

P5 MEDIUM: Upcoming catalyst (event within 24h)

P6 MEDIUM: Smart money vs retail divergence (> 40)

P7 LOW: Daily digest (18:30 IST, market days only)

---

## Packages

python-telegram-bot==21.*, APScheduler==3.*

---

## Env Vars

TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

---

# Module 18

FastAPI Backend + React GUI

---

## Category

Application Layer

---

## Status

COMPLETE (Phase 10+11, 2026-07-02)

---

## Completion

100%

---

## Priority

High

---

## Purpose

Serve all intelligence data as REST + WebSocket API. Required before GUI can display real data.
Also exposes tool endpoints for the Chatbot tool registry.

---

## Planned Routes

GET /api/v1/market/regime — latest regime + participant scores

GET /api/v1/market/history?days=30 — regime time series

GET /api/v1/sectors/ — all 29 sectors + rotation signals

GET /api/v1/sectors/{sector}/flow — sector capital flow history

GET /api/v1/stocks/watchlist?label=EMERGING — filtered watchlist

GET /api/v1/stocks/{symbol} — full intelligence snapshot

GET /api/v1/stocks/{symbol}/history — OHLCV from bhavcopy

GET /api/v1/participant/flows?days=90 — FII/DII/PRO/CLIENT flow scores

GET /api/v1/corporate/deals?min_cr=50 — institutional deal signals

GET /api/v1/corporate/events?days=30 — upcoming catalysts

POST /api/v1/chat/ — proxy to chatbot engine

WS /ws/live — push regime/sector changes, new signals

---

## Architecture

FastAPI app + Uvicorn ASGI

In-memory CSV cache reloaded every 60 min via APScheduler

Pydantic v2 response models

No database — intelligence files are the source of truth

---

## Packages

fastapi, uvicorn[standard], pydantic

---

## Directory

backend/
