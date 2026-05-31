# System Architecture

Version: 1.1

Last Updated: 31-May-2026

---

# Architecture Overview

The FII-DII Sector Intelligence Engine follows a layered architecture.

```text
External Data Sources
        │
        ▼
Fetch Layer
        │
        ▼
Historical Storage Layer
        │
        ▼
Intelligence Layer
        │
        ▼
Institutional Intelligence Layer
        │
        ▼
Reporting Layer
        │
        ▼
Delivery Layer
```

---

# Layer 1 — External Data Sources

## NSE India

Used For:

* Sector Indices
* Thematic Indices
* Market Breadth
* Holidays

---

## NSELib

Used For:

* Participant Wise Open Interest
* Participant Wise Trading Volume
* FII Derivatives Statistics
* Historical Index Data
* Holiday Data

---

## Yahoo Finance

Fallback Source

Used For:

* Movers
* Stock Performance

---

# Layer 2 — Fetch Layer

Location:

```text
fetchers/
```

---

## sector_fetcher.py

Purpose:

Fetch NSE sectors.

Output:

DataFrame

---

## sector_history_fetcher.py

Purpose:

Maintain historical sector database.

Output:

sector_history.csv

---

## thematic_history_fetcher.py

Purpose:

Maintain historical thematic database.

Output:

thematic_history.csv

---

## daily_fii_dii_fetcher.py

Purpose:

Fetch daily institutional cash activity.

Output:

Raw_FII_DII

---

## movers_fetcher.py

Purpose:

Identify strongest stocks.

Output:

Momentum candidates

---

# Layer 3 — Historical Storage Layer

Location:

```text
storage/
```

---

## fii_dii_history_manager.py

Maintains:

```text
data/historical/fii_dii/fii_dii_history.csv
```

---

## institutional_history_manager.py

Maintains:

```text
data/historical/institutional/institutional_history.csv
```

---

# Layer 4 — Intelligence Layer

---

## aggregation_engine.py

Generates:

* Weekly Heatmap
* Biweekly Heatmap
* Monthly Heatmap

---

## persistence_engine.py

Measures:

Leadership consistency.

Outputs:

Persistence scores.

---

## conviction_engine.py

Measures:

Leadership strength.

Outputs:

Conviction scores.

---

## leadership_duration_engine.py

Measures:

Leadership longevity.

Outputs:

Duration scores.

---

## flow_regime_engine.py

Measures:

Institutional cash flow trend.

Outputs:

Accumulation
Distribution
Sideways

---

# Layer 5 — Institutional Intelligence

---

## institutional_positioning_engine.py

Inputs:

Participant OI

Participant Volume

FII Derivatives

Outputs:

Institutional Score

Institutional Regime

---

Current Score Components

```text
FII OI
DII OI
PRO OI
CLIENT OI

FII Volume
DII Volume
PRO Volume

FII Derivatives
```

---

Regimes

```text
ACCUMULATION
DISTRIBUTION
NEUTRAL
```

---

## institutional_backfill_engine.py

Purpose:

Build historical institutional database.

Backfill Start:

2016

Backfill Mode:

Incremental

---

## nse_holiday_engine.py

Purpose:

Maintain holiday database.

Output:

```text
data/reference/nse_holidays.csv
```

Used For:

* Trading day validation
* Backfill optimization

---

# Layer 6 — Reporting Layer

Generated Outputs

Location:

```text
data/intelligence/
```

Files:

```text
institutional_flow_regime.csv

institutional_positioning.csv

sector_conviction_scores.csv

theme_conviction_scores.csv

sector_persistence_scores.csv

theme_persistence_scores.csv

sector_leadership_duration.csv

leadership_tracking.csv
```

---

# Layer 7 — Delivery Layer

---

## Telegram

Daily intelligence reports.

---

## Google Sheets

Cloud persistence.

Current Sheets:

```text
Raw_FII_DII

Momentum_Signals
```

---

# Future Architecture

Planned Layers

```text
Smart Money Layer

Sector Rotation Layer

Portfolio Allocation Layer

Dashboard Layer

AI Layer
```

---

---

# ARCHITECTURE UPDATE V1.1

**Date:** 2026-06-01

# High-Level Architecture

The platform is organized into six primary layers:

```text
Market Data Layer
        │
        ▼
Historical Data Layer
        │
        ▼
Intelligence Layer
        │
        ▼
Persistence Layer
        │
        ▼
Reporting Layer
        │
        ▼
Documentation Layer
```

---

# 1. Market Data Layer

Purpose:

Acquire raw market data from external sources.

Primary Sources:

### NSE

Provides:

* Sector Data
* Participant Open Interest
* Participant Trading Volume
* FII Derivatives Statistics
* Holiday Calendar

---

### Yahoo Finance

Provides:

* Fallback Market Movers
* Price Validation
* Backup Market Data

---

# 2. Historical Data Layer

Purpose:

Maintain long-term historical market memory.

---

## Sector History

Storage:

```text
data/historical/sectors/
```

File:

```text
sector_history.csv
```

---

## Theme History

Storage:

```text
data/historical/thematic/
```

File:

```text
thematic_history.csv
```

---

## FII/DII Flow History

Storage:

```text
data/historical/fii_dii/
```

File:

```text
fii_dii_history.csv
```

---

## Institutional Positioning History

Storage:

```text
data/historical/institutional/
```

File:

```text
institutional_positioning_history.csv
```

Coverage:

```text
2016-01-01
→
2026-05-29
```

Records:

```text
2560+
```

---

# 3. Intelligence Layer

Purpose:

Convert raw market data into actionable intelligence.

---

## Sector Intelligence

Engines:

* Conviction Engine
* Persistence Engine
* Leadership Duration Engine

Outputs:

* Sector Scores
* Leadership Rankings
* Heatmaps

---

## Theme Intelligence

Engines:

* Theme Conviction Engine
* Theme Persistence Engine

Outputs:

* Theme Scores
* Theme Heatmaps

---

## Institutional Intelligence

Engine:

```text
Institutional Positioning Engine
```

Inputs:

* Participant OI Data
* Participant Volume Data
* FII Derivatives Statistics

Outputs:

* Institutional Score
* Institutional Regime

Regimes:

* ACCUMULATION
* DISTRIBUTION
* NEUTRAL

---

## Flow Intelligence

Engine:

```text
Flow Regime Engine
```

Outputs:

* FII/DII Flow Regime
* Market Participation Signals

---

# 4. Reference Data Layer

Purpose:

Provide reusable supporting datasets.

---

## Holiday Database

File:

```text
data/reference/nse_holidays.csv
```

Coverage:

```text
2000
→
2026
```

Records:

```text
372
```

Fields:

* Date
* Year
* Holiday

---

## Trading Calendar Utility

File:

```text
utils/trading_calendar.py
```

Function:

```python
is_nse_holiday()
```

Purpose:

* Holiday Validation
* Historical Integrity Checks
* Backfill Filtering

---

# 5. Persistence Layer

Purpose:

Store intelligence outputs for historical analysis.

Generated Files:

```text
data/intelligence/
```

Includes:

* institutional_positioning.csv
* institutional_flow_regime.csv
* sector_conviction_scores.csv
* theme_conviction_scores.csv
* leadership_tracking.csv

---

# 6. Backfill Infrastructure

Purpose:

Reconstruct historical intelligence datasets.

---

## Institutional Backfill Engine

Responsibilities:

* Historical Recovery
* Missing Date Detection
* Batch Processing
* Integrity Validation
* Historical Reconstruction

Features:

* Weekend Skip Logic
* Holiday Skip Logic
* Duplicate Protection

Current Status:

Production Ready

---

# 7. Reporting Layer

Purpose:

Deliver intelligence to end users.

---

## Telegram Reporting

Capabilities:

* Automated Daily Reports
* Sector Intelligence Reporting
* Institutional Regime Reporting
* Momentum Signal Reporting

Status:

Operational

---

# 8. Documentation Layer

Purpose:

Preserve project knowledge and architecture decisions.

Structure:

```text
docs/
│
├── PROJECT_DOCUMENTATION.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── CHANGELOG.md
│
└── ENGINES/
```

Benefits:

* Knowledge Retention
* Faster Development
* Easier Maintenance
* Historical Tracking

---

# Planned Architectural Enhancements

## Institutional Availability Cache V1

Planned Storage:

```text
data/reference/
institutional_unavailable_dates.csv
```

Purpose:

Track confirmed unavailable institutional dates.

Benefits:

* Reduced API Calls
* Faster Integrity Scans
* Cleaner Logs

Priority:

High

---

## Data Quality Dashboard V1

Purpose:

Provide visibility into:

* Historical Coverage
* Missing Dates
* Holiday Coverage
* Availability Cache Coverage

Priority:

Medium

---

# Architecture Status

Market Data Layer:
Operational

Historical Data Layer:
Operational

Intelligence Layer:
Operational

Reference Data Layer:
Operational

Persistence Layer:
Operational

Reporting Layer:
Operational

Documentation Layer:
Operational

Overall Architecture Maturity:

Production Ready Foundation

