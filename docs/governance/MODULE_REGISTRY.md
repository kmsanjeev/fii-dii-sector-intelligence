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

# Module 09

Execution Platform

---

## Category

Platform

---

## Status

FOUNDATION COMPLETE

---

## Completion

5%

---

## Priority

Medium

---

## Purpose

Portfolio management and broker-independent execution.

---

## Planned Components

Portfolio Engine

Risk Engine

Order Management

Trade Journal

Performance Analytics

Broker Adapter Framework

---

# Future Intelligence Modules

---

# Module 10

Portfolio Intelligence

---

## Category

Future Intelligence

---

## Status

PLANNED

---

## Completion

0%

---

## Priority

Medium

---

## Purpose

Analyze portfolio construction, allocation, exposure, and performance.

---

# Module 11

Risk Intelligence

---

## Category

Future Intelligence

---

## Status

PLANNED

---

## Completion

0%

---

## Priority

Medium

---

## Purpose

Monitor portfolio and market risk.

---

# Module 12

Options Intelligence

---

## Category

Future Intelligence

---

## Status

PLANNED

---

## Completion

0%

---

## Priority

Medium

---

## Purpose

Advanced derivatives and options analytics.

---

# Module 13

Research Platform

---

## Category

Research

---

## Status

PLANNED

---

## Completion

0%

---

## Priority

High

---

## Purpose

Manage research, validation, investment theses, and idea tracking.

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

ALL PHASES 9-16 COMPLETE. Platform operational.

Next focus: Generation 4 (portfolio engine, execution platform, research platform).

---

# Current Platform Completion

Estimated Overall Completion:

Intelligence Cascade: 100% (Phases 1-8 all complete)

Application + AI Layer: 100% (Phases 9-16 all complete)

Platform Overall: ~75% (Generation 4 portfolio/execution/commercial pending)

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
