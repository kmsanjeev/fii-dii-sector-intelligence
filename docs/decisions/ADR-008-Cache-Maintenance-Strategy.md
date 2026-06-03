# ADR-008

## Title

Cache Maintenance Strategy

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

The platform uses on-demand cache generation.

Without maintenance policies, cache can become stale, inconsistent, or oversized.

---

# Decision

Cache shall be maintained separately from intelligence generation.

---

# Rules

Market Hours:

Read Only

---

After Market:

Cache Refresh Allowed

---

Weekends:

Heavy Rebuilds Allowed

---

# Cache Types

Stock Cache

Sector Cache

Theme Cache

Portfolio Cache

---

# Benefits

* Faster Runtime
* Lower Latency
* Better User Experience

---

# Long-Term Outcome

Cache remains optimized without impacting market-hour performance.
