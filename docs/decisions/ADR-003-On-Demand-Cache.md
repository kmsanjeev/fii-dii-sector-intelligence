# ADR-003

## Title

On-Demand Cache Architecture

---

# Status

Accepted

---

# Date

2026-06-03

---

# Context

The platform may eventually support:

4500+ listed companies

Creating caches for every stock would create unnecessary processing and storage overhead.

---

# Decision

Caches shall be generated only when required.

---

# Workflow

```text
User Request
      ↓
Cache Exists?
      ↓
YES → Load
NO → Build
      ↓
Save Cache
      ↓
Return Data
```

---

# Example

```text
KPIT Requested

KPIT.csv Missing

Build KPIT.csv

Save KPIT.csv

Return Data
```

---

# Benefits

* Reduced Storage
* Faster Development
* Lower Maintenance
* Better Scalability

---

# Long-Term Outcome

Only frequently accessed datasets consume cache resources.
