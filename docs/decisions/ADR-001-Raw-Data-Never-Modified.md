# ADR-001

## Title

Raw Data Never Modified

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

The platform consumes large amounts of market data from NSE and other sources.

Examples:

* Bhavcopy
* F&O Bhavcopy
* Institutional Data
* Corporate Actions
* Equity Master

A decision was required regarding whether source datasets should be altered after download.

---

# Decision

Raw datasets shall never be modified.

Raw data shall remain the permanent source of truth.

---

# Rules

Raw data may be:

* Downloaded
* Validated
* Archived

Raw data may not be:

* Edited
* Overwritten
* Recalculated

---

# Benefits

* Auditability
* Reproducibility
* Historical Accuracy
* Easier Recovery

---

# Consequences

All calculations must occur in:

* Cache Layer
* Intelligence Layer
* Signal Layer

Never in Raw Layer.

---

# Long-Term Outcome

Every intelligence output can always be regenerated from source data.
