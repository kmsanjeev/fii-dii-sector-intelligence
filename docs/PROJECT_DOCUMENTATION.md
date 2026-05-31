# FII-DII Sector Intelligence Engine

## Project Documentation

### Version: 1.0

### Date: 31-May-2026

---

# 1. Project Overview

The FII-DII Sector Intelligence Engine is an institutional-grade market intelligence platform focused on identifying:

* Sector rotation
* Theme rotation
* Institutional accumulation
* Institutional distribution
* Leadership persistence
* Conviction strength
* Smart money positioning

The platform combines:

* NSE sector data
* NSE thematic data
* FII/DII cash activity
* FII derivatives activity
* Participant-wise Open Interest
* Participant-wise Trading Volume

to generate actionable market intelligence.

---

# 2. Project Objectives

Primary objectives:

1. Detect leadership sectors early
2. Measure persistence of leadership
3. Measure conviction behind moves
4. Detect institutional accumulation
5. Detect institutional distribution
6. Track smart-money positioning
7. Generate Telegram intelligence reports
8. Maintain historical intelligence databases
9. Build a future sector allocation framework

---

# 3. Current Architecture

Project Structure

```text
fetchers/
storage/
utils/
sheets/
telegram/
config/

data/
 ├─ historical/
 └─ intelligence/
```

---

# 4. Engine Registry

## Historical Data Engine

File:

```text
fetchers/historical_data_engine.py
```

Purpose:

Maintains historical sector and thematic databases.

Outputs:

```text
sector_history.csv
thematic_history.csv
```

---

## Sector Fetcher

File:

```text
fetchers/sector_fetcher.py
```

Purpose:

Fetches official NSE sector indices.

Current sectors:

* NIFTY AUTO
* NIFTY BANK
* NIFTY FMCG
* NIFTY IT
* NIFTY MEDIA
* NIFTY METAL
* NIFTY PHARMA
* NIFTY PSU BANK
* NIFTY REALTY
* NIFTY HEALTHCARE

---

## Sector History Fetcher

File:

```text
fetchers/sector_history_fetcher.py
```

Purpose:

Maintains long-term sector historical database.

Output:

```text
data/historical/sectors/sector_history.csv
```

---

## Thematic History Fetcher

File:

```text
fetchers/thematic_history_fetcher.py
```

Purpose:

Maintains historical thematic index database.

Output:

```text
data/historical/thematic/thematic_history.csv
```

---

## Movers Fetcher

File:

```text
fetchers/movers_fetcher.py
```

Purpose:

Identifies strongest stocks.

Current Logic:

1. NSE API
2. Yahoo Finance fallback

Current Issue:

```text
NSE movers endpoint deprecated
```

Future:

Replace with stable NSE endpoint.

---

# 5. Intelligence Engines

## Aggregation Engine

File:

```text
fetchers/aggregation_engine.py
```

Purpose:

Combines historical datasets.

Produces:

* Weekly Heatmaps
* Biweekly Heatmaps
* Monthly Heatmaps

Outputs:

```text
sector_weekly_heatmap.csv
sector_biweekly_heatmap.csv
sector_monthly_heatmap.csv

theme_weekly_heatmap.csv
theme_biweekly_heatmap.csv
theme_monthly_heatmap.csv
```

---

## Persistence Engine

File:

```text
fetchers/persistence_engine.py
```

Purpose:

Measures consistency of leadership.

Outputs:

```text
sector_persistence_scores.csv
theme_persistence_scores.csv
```

---

## Conviction Engine

File:

```text
fetchers/conviction_engine.py
```

Purpose:

Measures strength behind leadership.

Output:

```text
sector_conviction_scores.csv
theme_conviction_scores.csv
```

---

## Leadership Duration Engine

File:

```text
fetchers/leadership_duration_engine.py
```

Purpose:

Tracks duration of leadership.

Output:

```text
sector_leadership_duration.csv
```

---

# 6. FII/DII Layer

## Daily FII/DII Fetcher

File:

```text
fetchers/daily_fii_dii_fetcher.py
```

Purpose:

Downloads:

* FII Buy

* FII Sell

* FII Net

* DII Buy

* DII Sell

* DII Net

Output:

```text
Raw_FII_DII Google Sheet
```

---

## Historical Archive

File:

```text
storage/fii_dii_history_manager.py
```

Output:

```text
data/historical/fii_dii/fii_dii_history.csv
```

Purpose:

Maintain long-term institutional cash flow database.

---

## Flow Regime Engine

File:

```text
fetchers/flow_regime_engine.py
```

Purpose:

Classifies market flow:

```text
ACCUMULATION
DISTRIBUTION
SIDEWAYS
```

Output:

```text
institutional_flow_regime.csv
```

---

# 7. Institutional Positioning Layer

Introduced in Version 1.1 roadmap.

---

## Institutional Positioning Engine

File:

```text
fetchers/institutional_positioning_engine.py
```

Data Source:

nselib

---

Uses:

### Participant Wise Open Interest

```text
FII
DII
PRO
CLIENT
```

---

### Participant Wise Trading Volume

```text
FII
DII
PRO
CLIENT
```

---

### FII Derivatives Statistics

```text
Index Futures
Stock Futures
Index Options
Stock Options
```

---

Output:

```text
data/intelligence/institutional_positioning.csv
```

---

Fields:

```text
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
```

---

Regimes:

```text
ACCUMULATION
DISTRIBUTION
NEUTRAL
```

---

# 8. Institutional Historical Database

## Institutional History Manager

File:

```text
storage/institutional_history_manager.py
```

Purpose:

Maintains historical institutional database.

Output:

```text
data/historical/institutional/
institutional_history.csv
```

---

## Institutional Backfill Engine

File:

```text
fetchers/institutional_backfill_engine.py
```

Purpose:

Backfills historical institutional positioning.

Uses:

```text
Participant OI
Participant Volume
FII Derivatives
```

Backfill Start:

```text
2016
```

Current Status:

In Progress

---

# 9. NSE Holiday Engine

File:

```text
fetchers/nse_holiday_engine.py
```

Purpose:

Downloads official NSE Equity Holidays.

Output:

```text
data/reference/nse_holidays.csv
```

Current Status:

Operational

---

Future Use:

```text
Backfill Optimization
Missing Data Validation
Trading Day Validation
```

---

# 10. Telegram Layer

Purpose:

Daily intelligence reporting.

Current Status:

Operational

Provides:

```text
Sector Leadership

Theme Leadership

Persistence

Conviction

Flow Regime

Institutional Regime

Momentum Signals
```

---

# 11. Google Sheet Layer

Purpose:

Cloud storage.

Current Sheets:

```text
Raw_FII_DII
Momentum_Signals
```

Status:

Operational

---

# 12. Historical Databases

Current Databases

```text
data/historical/fii_dii/
```

Contains:

```text
fii_dii_history.csv
```

---

```text
data/historical/sectors/
```

Contains:

```text
sector_history.csv
```

---

```text
data/historical/thematic/
```

Contains:

```text
thematic_history.csv
```

---

Future:

```text
data/historical/institutional/
```

Contains:

```text
institutional_history.csv
```

---

# 13. Technical Debt

Current Issues

### 1

NSE Movers endpoint deprecated.

Priority:

HIGH

---

### 2

Institutional unavailable-date cache not implemented.

Priority:

MEDIUM

---

### 3

Holiday-aware backfill not integrated.

Priority:

HIGH

---

### 4

Institutional historical database incomplete.

Priority:

HIGH

---

# 14. Roadmap

## Phase A (Completed)

✓ Historical Data Layer

✓ Heatmaps

✓ Persistence

✓ Conviction

✓ Leadership Duration

✓ Flow Regime

✓ Telegram Reporting

---

## Phase B (In Progress)

✓ Institutional Positioning Engine

✓ Institutional Historical Backfill

✓ NSE Holiday Engine

□ Holiday-aware Backfill

□ Missing Date Cache

---

## Phase C

Sector Rotation Engine

Inputs:

```text
Persistence
Conviction
Leadership Duration
Institutional Positioning
```

Outputs:

```text
Sector Rotation Score
```

---

## Phase D

Smart Money Engine

Inputs:

```text
FII
DII
PRO
CLIENT
```

Outputs:

```text
Smart Money Participation Score
```

---

## Phase E

Portfolio Allocation Engine

Outputs:

```text
Recommended Sector Weights
```

---

# 15. Current Project Status

Overall Completion Estimate

```text
Core Data Layer        100%
Intelligence Layer     100%
Institutional Layer     70%
Backfill Layer          40%
Smart Money Layer        0%
Allocation Layer         0%
```

Estimated Overall Completion

```text
≈ 65%
```

---

---

# PROJECT STATUS UPDATE V1.1

**Date:** 2026-06-01

## Executive Summary

The project has successfully evolved from a Sector & Theme Intelligence Engine into a broader Institutional Intelligence Platform.

The most significant achievement during this phase was the successful construction of a 10+ year institutional positioning database using NSE participant data.

The platform now maintains historical institutional activity, market flow intelligence, sector intelligence, thematic intelligence, and holiday-aware historical reconstruction capabilities.

---

# Current Platform Components

## Sector Intelligence Layer

Purpose:

Identify sector leadership, persistence, conviction, and momentum.

Implemented Components:

* Sector History Engine
* Sector Heatmap Engine
* Persistence Engine
* Conviction Engine
* Leadership Duration Engine

Outputs:

* Weekly Heatmaps
* Biweekly Heatmaps
* Monthly Heatmaps
* Conviction Scores
* Leadership Rankings

Status:

Production Ready

---

## Theme Intelligence Layer

Purpose:

Track thematic market leadership and thematic rotation.

Implemented Components:

* Thematic History Engine
* Theme Heatmap Engine
* Theme Persistence Engine
* Theme Conviction Engine

Outputs:

* Theme Heatmaps
* Theme Persistence Scores
* Theme Conviction Scores

Status:

Production Ready

---

## Institutional Intelligence Layer

Purpose:

Measure institutional market participation and positioning using NSE participant statistics.

Implemented Components:

### Participant Open Interest Analysis

Captures:

* FII Open Interest Positioning
* DII Open Interest Positioning
* Proprietary Trader Positioning
* Client Positioning

---

### Participant Trading Volume Analysis

Captures:

* FII Trading Activity
* DII Trading Activity
* Proprietary Trading Activity
* Client Trading Activity

---

### FII Derivatives Statistics

Captures:

* Futures Buying
* Futures Selling
* Net Futures Exposure

---

### Institutional Scoring Framework

Generates:

* Institutional Score
* Institutional Regime

Regimes:

* ACCUMULATION
* DISTRIBUTION
* NEUTRAL

Status:

Production Ready

---

# Historical Intelligence Infrastructure

## Institutional Historical Database

Purpose:

Maintain historical institutional positioning data for long-term analysis.

Storage Location:

data/historical/institutional/institutional_positioning_history.csv

Coverage:

2016-01-01 → 2026-05-29

Current Records:

2560+

Features:

* Historical Persistence
* Duplicate Protection
* Incremental Updates
* Historical Analytics Support

Status:

Production Ready

---

## Historical Backfill Engine

Purpose:

Reconstruct missing historical institutional data.

Capabilities:

* Historical Recovery
* Incremental Reconstruction
* Gap Detection
* Integrity Validation
* Batch Processing

Results Achieved:

Complete institutional database coverage from 2016 onward.

Status:

Production Ready

---

# Holiday Intelligence Framework

## NSE Holiday Database

Purpose:

Maintain a centralized reference database of official NSE trading holidays.

Storage Location:

data/reference/nse_holidays.csv

Coverage:

2000 → 2026

Current Records:

372

Fields:

* Date
* Year
* Holiday

---

## Holiday Database Repair Initiative

Completed Repairs:

* 2003
* 2019
* 2023
* 2024

Benefits:

* Reduced unnecessary API requests
* Improved historical integrity validation
* Improved backfill accuracy

Status:

Operational

---

## Trading Calendar Utility

Purpose:

Provide fast holiday validation services.

Primary Function:

is_nse_holiday()

Current Usage:

* Institutional Backfill Engine
* Historical Integrity Validation

Future Usage:

* Availability Cache
* Data Quality Dashboard
* Historical Auditing Tools

Status:

Production Ready

---

# Reporting Infrastructure

Current Outputs:

## CSV Intelligence Outputs

Generated Files:

* institutional_positioning.csv
* institutional_flow_regime.csv
* sector_conviction_scores.csv
* theme_conviction_scores.csv
* leadership_tracking.csv

---

## Telegram Intelligence Reports

Capabilities:

* Daily Automated Delivery
* Momentum Reporting
* Sector Leadership Reporting
* Institutional Regime Reporting

Status:

Operational

---

# Data Quality Controls

Implemented Controls:

* Weekend Exclusion
* Holiday Exclusion
* Duplicate Prevention
* Historical Integrity Validation
* Incremental Updates
* Historical Persistence

Result:

Stable long-term data collection architecture.

---

# Documentation Framework

Structure:

docs/

* PROJECT_DOCUMENTATION.md
* ROADMAP.md
* ARCHITECTURE.md
* CHANGELOG.md

ENGINES/

* Conviction_Engine.md
* Leadership_Duration_Engine.md
* Institutional_Positioning_Engine.md
* Institutional_Backfill_Engine.md
* NSE_Holiday_Engine.md

Purpose:

* Technical Reference
* Architecture Reference
* Development Tracking
* Knowledge Preservation

---

# Current Project Maturity

Sector Intelligence:
Production Ready

Theme Intelligence:
Production Ready

Institutional Intelligence:
Production Ready

Historical Reconstruction:
Production Ready

Holiday Intelligence:
Production Ready

Documentation:
Actively Expanding

---

# Next Planned Development

## Institutional Availability Cache V1

Purpose:

Cache known unavailable institutional dates.

Expected Benefits:

* Faster Historical Audits
* Reduced NSE Requests
* Cleaner Logs
* Self-Learning Infrastructure

Priority:

High

---

## Data Quality Dashboard V1

Purpose:

Provide visibility into:

* Historical Coverage
* Missing Dates
* Holiday Coverage
* Data Availability

Priority:

Medium

---

# Strategic Objective

Continue evolving the platform into a comprehensive Institutional Market Intelligence System capable of maintaining long-term market memory, identifying institutional accumulation and distribution behavior, monitoring sector and thematic rotation, and generating actionable market intelligence with minimal manual intervention.

