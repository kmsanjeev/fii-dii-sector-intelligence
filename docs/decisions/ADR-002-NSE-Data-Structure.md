# ADR-002

## Title

NSE Data Folder Structure

---

# Status

Accepted

---

# Date

2026-06-03

---

# Decision

The platform shall standardize all exchange data under:

```text
data/NSE Data/
```

---

# Structure

```text
data/NSE Data/

bhavcopy/
institutional/
corporate_actions/
equity_master/
holidays/
results/
shareholding/
announcements/
```

---

# Equity Bhavcopy Standard

```text
data/NSE Data/bhavcopy/equity/<YEAR>/

bhavcopy_YYYYMMDD.csv
```

---

# F&O Standard

```text
data/NSE Data/bhavcopy/f&o/<YEAR>/
```

---

# Benefits

* Consistency
* Backward Compatibility
* Easier Automation
* Easier Maintenance

---

# Long-Term Outcome

All future engines consume a standardized data structure.
