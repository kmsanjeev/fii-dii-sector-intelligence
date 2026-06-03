# ADR-004

## Title

Listing-Date-Aware Processing

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

Many NSE companies were listed recently.

Processing historical files before listing dates wastes resources.

---

# Decision

All stock-level processing shall begin from listing date.

---

# Source

```text
data/NSE Data/equity_master/equity_master.csv
```

---

# Workflow

```text
Symbol
   ↓
Equity Master
   ↓
Listing Date
   ↓
Process Relevant Years Only
```

---

# Example

KPIT

Listing Date:

2019

Process:

2019+
Only

Not:

1995+

```

---

# Benefits

- Faster Processing
- Lower Memory Usage
- Better Scalability

---

# Long-Term Outcome

Platform scales efficiently across 4500+ companies.
```
