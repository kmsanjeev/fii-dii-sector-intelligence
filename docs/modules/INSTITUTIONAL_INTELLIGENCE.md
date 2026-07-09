# INSTITUTIONAL INTELLIGENCE

## Project

FII/DII Capital Flow Intelligence Platform

---

# Module Overview

Institutional Intelligence is the foundation module of the platform.

Its purpose is to track the behavior of institutional participants and identify:

* Capital Flow
* Positioning Changes
* Accumulation
* Distribution
* Market Regimes

before they become visible through price action.

---

# Objective

Answer the following questions:

1. What are institutions doing?
2. Are institutions accumulating or distributing?
3. Is institutional conviction increasing or decreasing?
4. What market regime is emerging?
5. How is institutional behavior changing over time?

---

# Market Participants

The module tracks the following participant categories.

---

## FII

Foreign Institutional Investors

Examples:

* Foreign Funds
* Sovereign Funds
* Pension Funds
* Global Asset Managers

---

## DII

Domestic Institutional Investors

Examples:

* Mutual Funds
* Insurance Companies
* Domestic Asset Managers

---

## PRO

Proprietary Traders

Examples:

* Broker Proprietary Desks
* Trading Firms

---

## CLIENT

Retail and Non-Institutional Participants

---

# Data Sources

Primary Source:

nselib

---

# Data Categories

## Category 1

Cash Market Flow

Tracks:

* FII Buy
* FII Sell
* DII Buy
* DII Sell

---

## Category 2

Participant Open Interest

Tracks:

* Long Positions
* Short Positions
* Net Open Interest

for:

FII

DII

PRO

CLIENT

---

## Category 3

Participant Trading Volume

Tracks:

* Long Contracts
* Short Contracts
* Trading Activity

for:

FII

DII

PRO

CLIENT

---

## Category 4

FII Derivatives Statistics

Tracks:

* Buy Contracts
* Sell Contracts
* Open Contracts
* Open Interest Value

---

# Historical Coverage

Current Coverage:

2016 → Present

---

# Core Datasets

## Dataset 01

Historical Positioning

Location:

```text
data/historical/institutional/
institutional_positioning_history.csv
```

---

## Purpose

Master historical institutional dataset.

---

## Contents

Date

FII_OI_Net

DII_OI_Net

PRO_OI_Net

CLIENT_OI_Net

FII_Volume_Net

DII_Volume_Net

PRO_Volume_Net

CLIENT_Volume_Net

FII_Derivatives_Net

Institutional_Score

Regime

---

# Engines

---

## Engine 01

Institutional Historical Engine

---

### Purpose

Build and maintain institutional history.

---

### Responsibilities

Historical Downloads

Daily Updates

Data Normalization

Historical Storage

---

### Status

Complete

---

## Engine 02

Institutional Backfill Engine

---

### Purpose

Fill missing historical dates.

---

### Responsibilities

Gap Detection

Gap Recovery

Data Validation

---

### Status

Complete

---

## Engine 03

Institutional Integrity Engine

---

### Purpose

Validate historical completeness.

---

### Responsibilities

Expected Trading Days

Actual Records

Missing Dates

Unavailable Dates

Integrity %

Coverage %

---

### Status

Complete

---

### Current Result

Coverage:

100%

Integrity:

100%

---

## Engine 04

Institutional Regime Engine

---

### Purpose

Classify market conditions.

---

### Example Regimes

Accumulation

Distribution

Neutral

Strong Accumulation

Strong Distribution

---

### Status

Complete

---

## Engine 05

Institutional Trend Engine

---

### Purpose

Measure institutional momentum.

---

### Trend Horizons

Daily

Weekly

BiWeekly

Monthly

Quarterly

HalfYearly

Yearly

---

### Outputs

Trend Direction

Trend Strength

Trend Acceleration

Trend State

---

### Status

Complete

---

# Institutional Score

## Purpose

Create a composite institutional signal.

---

## Components

FII Open Interest

DII Open Interest

PRO Open Interest

CLIENT Open Interest

FII Volume

DII Volume

PRO Volume

CLIENT Volume

FII Derivatives

---

## Output

Institutional_Score

---

# Current Limitations

---

## Limitation 1

Cash Flow Data

Current implementation primarily focuses on net institutional positioning.

Future versions should preserve:

Gross Buying

Gross Selling

Net Flow

independently.

---

## Limitation 2

No Stock-Level Institutional Visibility

Current data provides participant-level market positioning.

It does not reveal exact stock allocations.

---

## Limitation 3

No Sector Attribution

Institutional positioning is currently market-wide.

Sector attribution must be inferred through Sector Intelligence.

---

# Planned Enhancements

---

## Version 1.1

Gross Flow Preservation

Store:

Buy

Sell

Net

separately.

---

## Version 1.2

Institutional Dashboard

Market Overview

Institutional Trend

Regime Monitoring

---

## Version 1.3

Institutional Infographics

Capital Flow Maps

Regime Maps

Trend Maps

---

## Version 1.4

Institutional AI Analyst

Natural Language Analysis

---

# Dependencies

Market Foundation

Trading Calendar

NSE Holidays

---

# Downstream Consumers

Sector Intelligence

Theme Intelligence

Stock Intelligence

AI Analyst

Portfolio Intelligence

Reporting Platform

---

# Relationship To Capital Flow Framework

Institutional Intelligence provides:

Market Level Capital Flow

↓

Sector Intelligence provides:

Sector Level Capital Flow

↓

Theme Intelligence provides:

Theme Level Capital Flow

↓

Stock Intelligence provides:

Stock Level Capital Flow

---

# Success Criteria

The module successfully identifies:

Institutional Accumulation

Institutional Distribution

Regime Changes

Trend Changes

Capital Flow Shifts

before they become fully visible through market prices.

---

# Current Completion

Estimated Completion: 100% (COMPLETE — superseded by Participant Intelligence Module, Phase 5)

All institutional data has been integrated into:
- participant_acquisition_engine.py (Phase 5A)
- participant_flow_engine.py (Phase 5B)
- participant_intelligence_engine.py (Phase 5C)

Gross Buy/Sell preserved in institutional_positioning_history.csv.
Institutional Dashboard live via React GUI (Participant Intelligence page).
AI Institutional Analyst delivered via Phase 14 chatbot (MarketAgent).

---

# Long-Term Vision

Create the most comprehensive institutional behavior monitoring system capable of detecting:

Who is buying?

Who is selling?

How conviction is changing?

What regime is emerging?

and provide those answers before price fully reflects the information.
