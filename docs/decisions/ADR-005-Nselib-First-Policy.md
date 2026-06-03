# ADR-005

## Title

nselib First Data Acquisition Policy

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

The platform requires reliable market data acquisition.

Multiple sources are available.

A standard acquisition hierarchy is required.

---

# Decision

Preferred source order:

1. nselib
2. NSE API
3. Alternative Sources
4. yFinance

---

# Rationale

nselib provides:

* Structured Data
* NSE-backed Information
* Easier Maintenance
* Better Consistency

---

# Fallback Policy

Higher priority source must fail before lower priority source is used.

---

# Example

```text
Try nselib
      ↓
Fail
      ↓
Try NSE API
      ↓
Fail
      ↓
Try Alternative Source
      ↓
Fail
      ↓
Try yFinance
```

---

# Benefits

* Data Consistency
* Lower Maintenance
* Better Reliability

---

# Long-Term Outcome

Platform remains independent of any single external source.
