# ADR-009

## Title

Intelligence Layer Separation

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

Mixing raw data, intelligence calculations, and signals creates maintenance complexity.

---

# Decision

The platform shall separate:

Raw Data

↓

Intelligence

↓

Signals

↓

Reports

---

# Responsibilities

Raw Data

Stores facts.

---

Intelligence

Creates insights.

---

Signals

Creates opportunities.

---

Reports

Creates communication.

---

# Benefits

* Easier Testing
* Easier Maintenance
* Cleaner Architecture
* Better AI Integration

---

# Long-Term Outcome

Each layer remains independently rebuildable.
