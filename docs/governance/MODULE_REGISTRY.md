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

FOUNDATION COMPLETE

---

## Completion

5%

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

25%

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
