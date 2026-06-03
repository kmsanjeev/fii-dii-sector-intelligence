# DATA ARCHITECTURE

## Project

FII/DII Capital Flow Intelligence Platform

---

# Purpose

This document defines the complete data architecture of the platform.

It governs:

* Data Sources
* Data Storage
* Data Lifecycle
* Cache Management
* Validation Framework
* Update Framework
* Processing Strategy

All future data engines must comply with this architecture.

---

# Data Philosophy

## Principle 1

Raw Data Never Modified

Raw datasets are the permanent source of truth.

---

## Principle 2

Everything Must Be Rebuildable

Derived outputs must always be capable of regeneration.

---

## Principle 3

Process Only What Is Required

Avoid unnecessary processing.

---

## Principle 4

Cache Only What Is Valuable

Do not pre-build datasets without a business need.

---

## Principle 5

Storage Is Cheap

Processing Time Is Expensive

Optimize for reduced processing time.

---

# Data Layers

```text
RAW DATA
    ↓
CACHE
    ↓
INTELLIGENCE
    ↓
SIGNALS
    ↓
REPORTS
```

---

# Layer 1

## Raw Data Layer

### Purpose

Permanent storage of source data.

---

## Location

```text
data/NSE Data/
```

---

## Folder Structure

```text
data/

└── NSE Data/

    ├── institutional/

    ├── bhavcopy/

    │   ├── equity/
    │   │
    │   │   ├── 1995/
    │   │   ├── 1996/
    │   │   └── ...
    │   │
    │   └── f&o/
    │
    ├── corporate_actions/

    ├── equity_master/

    ├── holidays/

    ├── results/

    ├── shareholding/

    └── announcements/
```

---

# Equity Bhavcopy Architecture

## Structure

```text
data/NSE Data/bhavcopy/equity/

    2025/
        bhavcopy_20250101.csv
        bhavcopy_20250102.csv

    2026/
        bhavcopy_20260101.csv
        bhavcopy_20260102.csv
```

---

## Naming Standard

```text
bhavcopy_YYYYMMDD.csv
```

Mandatory.

---

## Source Policy

Primary:

nselib

Fallback:

NSE API

Secondary Fallback:

Alternative Sources

Last Resort:

yFinance

---

# F&O Architecture

## Structure

```text
data/NSE Data/bhavcopy/f&o/

    2025/
    2026/
```

---

## Contents

* Futures
* Options
* Open Interest
* Contract Data

---

# Institutional Architecture

## Structure

```text
data/NSE Data/institutional/
```

---

## Contents

* FII/DII Cash Flow
* Participant OI
* Participant Volume
* FII Derivatives

---

# Equity Master Architecture

## Structure

```text
data/NSE Data/equity_master/
```

---

## Master Dataset

```text
equity_master.csv
```

---

## Critical Fields

Symbol

Company Name

Series

Industry

Sector

Theme

Listing Date

Status

---

## Importance

The Equity Master becomes the authoritative source for:

* Listing Dates
* Active Symbols
* Delisted Symbols
* Sector Mapping
* Theme Mapping

---

# Listing-Date-Aware Processing

## Rule

Never process data before a stock was listed.

---

## Workflow

```text
Symbol Request
        ↓
Equity Master
        ↓
Fetch Listing Date
        ↓
Process Only Relevant Files
```

---

## Example

KPIT

Listing Date:

2019

Processing:

2019+
Only

Not:

1995+
Present

---

# Company Universe

## Estimated Size

Approximately:

4500+ Listed Companies

---

## Design Implication

All engines must assume:

4500+
symbols

and optimize accordingly.

---

# Cache Layer

## Purpose

Reduce repetitive processing.

---

## Location

```text
data/cache/
```

---

# Cache Philosophy

Generate only when required.

Do not pre-build all company datasets.

---

# Stock Cache Architecture

## Example

```text
data/cache/stock_history/

    KPIT.csv

    TCS.csv

    RELIANCE.csv
```

---

## Workflow

```text
Request Stock
      ↓
Cache Exists?
      ↓
YES
      ↓
Load Cache

NO
      ↓
Build Cache
      ↓
Save Cache
      ↓
Return Data
```

---

# Cache Refresh Policy

## Market Hours

Read Only

No heavy processing.

---

## After Market Hours

Allowed:

* Cache Creation
* Cache Refresh
* Rebuilding

---

## Weekends

Preferred For:

* Large Rebuilds
* Integrity Validation
* Historical Reprocessing

---

# Maintenance Engines

## Purpose

Background optimization.

---

## Examples

Stock Cache Maintenance

Sector Cache Maintenance

Theme Cache Maintenance

Portfolio Cache Maintenance

---

# Intelligence Layer

## Location

```text
data/intelligence/
```

---

## Characteristics

Derived

Rebuildable

Version Independent

---

## Examples

Institutional Regime

Sector Rotation

Theme Rotation

Stock Accumulation

Fundamental Intelligence

---

# Signals Layer

## Location

```text
data/signals/
```

---

## Examples

Watchlists

Trade Candidates

Alerts

Opportunity Rankings

---

# Reports Layer

## Location

```text
data/reports/
```

---

## Outputs

Daily Reports

Weekly Reports

Monthly Reports

Research Reports

Infographics

---

# Validation Framework

Every data engine must implement:

---

## Schema Validation

Verify columns.

---

## Data Type Validation

Verify datatypes.

---

## Completeness Validation

Verify missing data.

---

## Integrity Validation

Verify expected record counts.

---

## Historical Validation

Verify continuity.

---

# Data Lifecycle

## Raw Data

Retain Permanently

---

## Cache

Rebuild Anytime

---

## Intelligence

Regenerate Anytime

---

## Signals

Regenerate Anytime

---

## Reports

Archive Permanently

---

# Performance Strategy

## Rule 1

Avoid full-universe scans whenever possible.

---

## Rule 2

Use listing-date-aware processing.

---

## Rule 3

Prefer cached access.

---

## Rule 4

Perform heavy workloads after market hours.

---

## Rule 5

Optimize for 4500+ listed companies.

---

# Future Scalability

The architecture must support:

* 30+ Years Historical Data
* 4500+ Companies
* AI Agents
* Broker Integrations
* Portfolio Analytics
* Backtesting
* Mobile Applications

without requiring redesign.

---

# Long-Term Objective

Create a scalable, efficient, and maintainable market data ecosystem capable of powering:

Capital Flow Intelligence

Fundamental Intelligence

Artificial Intelligence

Portfolio Intelligence

Execution Intelligence

while preserving data integrity and minimizing processing overhead.
