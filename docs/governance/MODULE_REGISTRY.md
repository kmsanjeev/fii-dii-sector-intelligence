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

PLANNED

---

## Completion

0%

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

## Future Outputs

Participant Scores

Conviction Scores

Participation Scores

Divergence Scores

Smart Money Scores

Retail Sentiment Scores

---

## Planned Engines

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

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

ADVANCED

---

## Completion

75%

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

ACTIVE DEVELOPMENT

---

## Completion

45%

---

## Priority

Very High

---

## Purpose

Identify sector-level capital movement.

---

## Existing Engines

Sector Heatmap

Sector Persistence

Sector Conviction

Leadership Duration

---

## Planned Engines

Sector Rotation Engine

Sector Capital Flow Engine

Sector Momentum Engine

Sector Opportunity Engine

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

FOUNDATION COMPLETE

---

## Completion

10%

---

## Priority

Very High

---

## Purpose

Identify stock-level beneficiaries of capital flow.

---

## Planned Engines

Relative Strength Engine

Accumulation Engine

Distribution Engine

Delivery Intelligence Engine

F&O Intelligence Engine

Leadership Engine

Opportunity Engine

---

## Dependencies

Theme Intelligence

Fundamental Intelligence

---

# Module 06

Fundamental Intelligence

---

## Category

Core Intelligence

---

## Status

ACTIVE DEVELOPMENT

---

## Completion

55%

---

## Priority

High

---

## Purpose

Explain why capital is moving.

---

## Planned Engines

Results Intelligence

Management Intelligence

Corporate Actions Intelligence

Order Book Intelligence

Shareholding Intelligence

Valuation Intelligence

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

PLANNED

---

## Completion

0%

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

PLANNED

---

## Completion

0%

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

PLANNED

---

## Completion

0%

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

# Current Development Priority

Priority 1

Participant Intelligence

---

Priority 2

Sector Rotation Engine

Sector Capital Flow Engine

---

Priority 3

Theme Rotation Engine

Theme Capital Flow Engine

---

Priority 4

Stock Intelligence Foundation

---

Priority 5

Fundamental Intelligence Foundation

---

# Current Platform Completion

Estimated Overall Completion:

22% (16 modules — 3 new ML/AI modules added 2026-06-29, reducing average)

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
