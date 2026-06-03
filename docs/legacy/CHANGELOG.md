# Changelog

Version: 1.1

Last Updated: 31-May-2026

---

# 2026-05-31

Documentation Framework Introduced

Added:

* PROJECT_DOCUMENTATION.md
* ROADMAP.md
* ARCHITECTURE.md
* CHANGELOG.md

Created:

```text
docs/
docs/ENGINES/
docs/DATA/
docs/REPORTS/
```

---

# 2026-05-30

NSE Holiday Engine

Added:

```text
fetchers/nse_holiday_engine.py
```

Features:

* NSE Equity Holidays
* Holiday CSV generation
* Trading day reference framework

Output:

```text
data/reference/nse_holidays.csv
```

---

# 2026-05-30

Institutional Historical Backfill

Added:

```text
fetchers/institutional_backfill_engine.py

storage/institutional_history_manager.py
```

Features:

* Historical participant OI
* Historical participant volume
* Historical derivatives

Database:

```text
institutional_history.csv
```

Status:

Active

---

# 2026-05-30

Institutional Positioning Engine

Added:

```text
fetchers/institutional_positioning_engine.py
```

Features:

* FII OI Analysis

* DII OI Analysis

* PRO OI Analysis

* Client OI Analysis

* FII Volume Analysis

* DII Volume Analysis

* PRO Volume Analysis

* Client Volume Analysis

* FII Derivatives Analysis

Outputs:

* Institutional Score
* Institutional Regime

---

# 2026-05-29

Leadership Duration Engine

Added:

```text
fetchers/leadership_duration_engine.py
```

Output:

```text
sector_leadership_duration.csv
```

---

# 2026-05-29

Conviction Engine

Added:

```text
fetchers/conviction_engine.py
```

Outputs:

```text
sector_conviction_scores.csv

theme_conviction_scores.csv
```

---

# 2026-05-28

Persistence Engine

Added:

```text
fetchers/persistence_engine.py
```

Outputs:

```text
sector_persistence_scores.csv

theme_persistence_scores.csv
```

---

# 2026-05-28

Heatmap Framework

Added:

```text
fetchers/aggregation_engine.py
```

Outputs:

* Weekly Heatmaps
* Biweekly Heatmaps
* Monthly Heatmaps

Sector & Theme

---

# 2026-05-27

Historical Intelligence Layer

Added:

* Historical Sector Database
* Historical Thematic Database

Files:

```text
sector_history.csv

thematic_history.csv
```

---

# 2026-05-27

Flow Regime Engine

Added:

```text
fetchers/flow_regime_engine.py
```

Outputs:

```text
ACCUMULATION

DISTRIBUTION

SIDEWAYS
```

---

# 2026-05-27

FII/DII Historical Archive

Added:

```text
storage/fii_dii_history_manager.py
```

Output:

```text
fii_dii_history.csv
```

---

# 2026-05-27

Foundation Layer

Added:

* Sector Fetcher
* Movers Fetcher
* Daily FII/DII Fetcher
* Telegram Integration
* Google Sheets Integration
* Momentum Signals

Status:

Operational

---

# Upcoming

Institutional Availability Cache

Holiday-Aware Backfill

Smart Money Engine

Sector Rotation Engine

Portfolio Allocation Engine

Dashboard Layer

---

# CHANGELOG

## Version 1.1

**Date:** 2026-06-01

---

# Major Milestone: Institutional Intelligence Foundation Completed

This release marks the completion of the Institutional Intelligence data foundation layer, including historical reconstruction, holiday intelligence, institutional positioning analytics, and supporting infrastructure.

---

## Added

### Institutional Positioning Engine

Implemented institutional positioning analysis using NSE participant data.

Features:

* Participant Wise Open Interest Analysis
* Participant Wise Trading Volume Analysis
* FII Derivatives Statistics Integration
* Institutional Score Calculation
* Regime Classification

Outputs:

* ACCUMULATION
* DISTRIBUTION
* NEUTRAL

Generated File:

```text
data/intelligence/institutional_positioning.csv
```

---

### Institutional Historical Storage

Implemented historical storage for institutional positioning data.

Generated File:

```text
data/historical/institutional/
institutional_positioning_history.csv
```

Capabilities:

* Daily persistence
* Duplicate protection
* Incremental updates
* Historical analysis support

---

### Institutional Backfill Engine

Implemented full historical reconstruction engine.

Capabilities:

* Incremental backfill
* Historical gap detection
* Missing date recovery
* Batch processing
* Integrity validation

Coverage Achieved:

```text
2016-01-01
to
2026-05-29
```

Historical Records:

```text
2560 rows
```

Status:

```text
Production Ready
```

---

### NSE Holiday Engine

Implemented NSE holiday intelligence framework.

Initial Version:

* NSE holiday download
* Annual holiday refresh

Enhanced Version:

* Historical holiday database
* Holiday repair workflow
* Year tracking
* Data normalization

Generated File:

```text
data/reference/nse_holidays.csv
```

Coverage:

```text
2000-2026
```

Current Records:

```text
372 holidays
```

---

### Trading Calendar Utility

Added:

```text
utils/trading_calendar.py
```

Capabilities:

* Fast holiday lookup
* Historical holiday validation
* Future holiday validation

Used By:

* Institutional Backfill Engine
* Future Availability Cache
* Future Integrity Engines

---

### Documentation Framework

Added documentation structure:

```text
docs/

PROJECT_DOCUMENTATION.md
ROADMAP.md
ARCHITECTURE.md
CHANGELOG.md

ENGINES/
```

Purpose:

* Technical documentation
* Architecture documentation
* Development tracking
* Future onboarding

---

## Data Quality Improvements

### Holiday Database Repair

Repaired missing or corrupted years:

```text
2003
2019
2023
2024
```

Added verified NSE holiday records.

Reduced unnecessary NSE API requests.

Improved historical backfill accuracy.

---

### Institutional Data Integrity

Implemented:

* Weekend exclusion
* Holiday exclusion
* Historical validation
* Duplicate prevention
* Incremental persistence

---

## Infrastructure Improvements

### Historical Intelligence Layer

Established long-term institutional database.

Current historical depth:

```text
10+ years
```

Supports:

* Regime analysis
* Trend analysis
* Institutional accumulation studies
* Institutional distribution studies

---

## Upcoming (Version 1.2)

Planned:

### Institutional Availability Cache V1

Purpose:

* Cache unavailable NSE participant dates
* Prevent repeated failed requests
* Reduce NSE traffic
* Improve integrity scan speed

Proposed File:

```text
data/reference/
institutional_unavailable_dates.csv
```

---

### Data Quality Dashboard

Future monitoring framework for:

* Holiday coverage
* Missing dates
* Data availability
* Historical completeness

---

## Current Project Status

Institutional Positioning Engine:
COMPLETE

Institutional Historical Database:
COMPLETE

Institutional Backfill Engine:
COMPLETE

NSE Holiday Engine:
COMPLETE

Trading Calendar Utility:
COMPLETE

Availability Cache:
PLANNED

Data Quality Dashboard:
PLANNED

