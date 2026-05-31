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

End of Document
