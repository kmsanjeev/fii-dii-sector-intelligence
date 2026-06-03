# MASTER ARCHITECTURE

## Project

Capital Flow Intelligence Platform

---

# Architecture Overview

The Capital Flow Intelligence Platform is designed as a multi-layer intelligence architecture capable of transforming raw market data into actionable investment decisions.

The architecture follows a strict separation of responsibilities between:

* Data Acquisition
* Data Storage
* Intelligence Generation
* Research
* AI Analysis
* Visualization
* Portfolio Management
* Execution

This separation ensures scalability, maintainability, auditability, and future extensibility.

---

# Core Philosophy

The platform is built around a single principle:

```text
Follow the Money
```

The objective is to identify how capital moves through:

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
    ↓
Fundamental Validation
    ↓
Portfolio
    ↓
Execution
```

before broad market recognition.

---

# Architectural Layers

```text
RAW DATA LAYER
        ↓
DATA PROCESSING LAYER
        ↓
PARTICIPANT INTELLIGENCE LAYER
        ↓
SECTOR INTELLIGENCE LAYER
        ↓
THEME INTELLIGENCE LAYER
        ↓
STOCK INTELLIGENCE LAYER
        ↓
FUNDAMENTAL INTELLIGENCE LAYER
        ↓
AI PLATFORM
        ↓
GUI PLATFORM
        ↓
EXECUTION PLATFORM
```

---

# Layer 1

Raw Data Layer

---

## Purpose

Store original market data.

This layer represents the permanent source of truth.

---

## Rules

Raw data may be:

* Downloaded
* Archived
* Validated

Raw data may not be:

* Modified
* Overwritten
* Recalculated

---

## Data Sources

NSE Bhavcopy

F&O Bhavcopy

Institutional Data

Corporate Actions

Results

Shareholding

Announcements

Concall Data

Investor Presentations

AGM Documents

---

## Architecture Decision

ADR-001

Raw Data Never Modified

---

# Layer 2

Data Processing Layer

---

## Purpose

Transform raw data into usable datasets.

---

## Responsibilities

Validation

Normalization

Mapping

Aggregation

Cache Generation

---

## Outputs

Clean Datasets

Cache Files

Master Datasets

Reference Datasets

---

# Layer 3

Participant Intelligence Layer

---

## Purpose

Analyze participant behavior.

---

## Participants

FII

DII

PRO

CLIENT

---

## Responsibilities

Participation Analysis

Conviction Analysis

Flow Analysis

Position Analysis

Divergence Analysis

Smart Money Analysis

Retail Sentiment Analysis

---

## Outputs

Participant Scores

Conviction Scores

Participation Scores

Divergence Scores

Smart Money Scores

Retail Sentiment Scores

---

## Future Engines

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

# Layer 4

Sector Intelligence Layer

---

## Purpose

Identify sector-level capital movement.

---

## Responsibilities

Sector Leadership

Sector Rotation

Sector Conviction

Sector Momentum

Sector Capital Flow

---

## Outputs

Sector Rankings

Sector Opportunities

Sector Rotation Reports

Sector Capital Flow Reports

---

# Layer 5

Theme Intelligence Layer

---

## Purpose

Identify thematic capital movement.

---

## Responsibilities

Theme Leadership

Theme Rotation

Theme Conviction

Theme Momentum

Theme Capital Flow

---

## Outputs

Theme Rankings

Theme Opportunities

Theme Rotation Reports

Theme Capital Flow Reports

---

# Layer 6

Stock Intelligence Layer

---

## Purpose

Identify stock-level beneficiaries.

---

## Responsibilities

Relative Strength

Accumulation Detection

Distribution Detection

Delivery Intelligence

F&O Intelligence

Leadership Analysis

Opportunity Discovery

---

## Outputs

Stock Rankings

Accumulation Rankings

Distribution Rankings

Opportunity Rankings

Leadership Rankings

---

# Layer 7

Fundamental Intelligence Layer

---

## Purpose

Explain why capital is flowing.

---

## Responsibilities

Results Analysis

Corporate Actions Analysis

Management Analysis

Shareholding Analysis

Order Book Analysis

Valuation Analysis

---

## Outputs

Fundamental Scores

Growth Scores

Quality Scores

Valuation Scores

Research Reports

---

# Layer 8

AI Platform

---

## Purpose

Act as the intelligence orchestration layer.

---

## AI Agents

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

## Outputs

Reports

Recommendations

Research Summaries

Portfolio Reviews

Opportunity Analysis

---

# Layer 9

GUI Platform

---

## Purpose

Provide user interaction and visualization.

---

## Components

Dashboards

Heatmaps

Infographics

Capital Flow Maps

Reports

Alerts

Watchlists

AI Chat Interface

---

## Design Principles

AI First

Visualization First

Three Second Understanding Rule

Progressive Disclosure

---

# Layer 10

Execution Platform

---

## Purpose

Transform intelligence into action.

---

## Components

Portfolio Management

Risk Management

Order Management

Trade Journal

Performance Analytics

Broker Integration

---

## Supported Brokers

Zerodha

Dhan

Upstox

Angel One

Fyers

---

# Cross-Cutting Systems

The following systems interact with all layers.

---

## Research Platform

Stores:

Research Notes

Research Reports

Investment Theses

Validation Studies

---

## Documentation Platform

Stores:

Architecture

Governance

ADR

Module Documentation

Development Records

---

## Alert Platform

Provides:

Telegram Alerts

Email Alerts

Application Alerts

Mobile Notifications

---

## Reporting Platform

Provides:

Daily Reports

Weekly Reports

Monthly Reports

Research Reports

---

# Data Flow Architecture

```text
Raw Data
    ↓
Processing
    ↓
Participant Intelligence
    ↓
Sector Intelligence
    ↓
Theme Intelligence
    ↓
Stock Intelligence
    ↓
Fundamental Intelligence
    ↓
AI Analysis
    ↓
GUI Presentation
    ↓
Execution
```

---

# Technology Philosophy

The platform shall prioritize:

Reliability

Auditability

Scalability

Modularity

Broker Independence

AI Integration

Research Driven Development

---

# Future Expansion Areas

Portfolio Intelligence

Risk Intelligence

Strategy Intelligence

Options Intelligence

Global Markets Intelligence

Commodity Intelligence

Currency Intelligence

Macro Intelligence

Alternative Data Intelligence

---

# Architecture Principles

Principle 1

Raw Data Never Modified

---

Principle 2

nselib First Data Acquisition

---

Principle 3

On Demand Cache Generation

---

Principle 4

Listing Date Aware Processing

---

Principle 5

Participant Driven Capital Flow Analysis

---

Principle 6

AI First User Experience

---

Principle 7

Documentation Before Release

---

# Long-Term Vision

Create a complete Investment Operating System capable of:

Tracking Capital Flow

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

through a unified AI-powered ecosystem.

The Master Architecture serves as the blueprint for all future development within the Capital Flow Intelligence Platform.
