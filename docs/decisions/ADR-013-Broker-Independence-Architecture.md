# ADR-013

## Title

Broker Independence Architecture

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

Broker APIs evolve frequently.

Vendor lock-in creates platform risk.

---

# Decision

Execution layer shall remain broker-independent.

---

# Architecture

Execution Engine

↓

Broker Adapter

↓

Broker API

---

# Supported Brokers

Zerodha

Dhan

Upstox

Angel One

Fyers

---

# Benefits

* Flexibility
* Reduced Dependency Risk
* Easier Expansion

---

# Long-Term Outcome

Users can change brokers without affecting platform intelligence.
