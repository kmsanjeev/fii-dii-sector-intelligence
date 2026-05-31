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

End of Changelog
