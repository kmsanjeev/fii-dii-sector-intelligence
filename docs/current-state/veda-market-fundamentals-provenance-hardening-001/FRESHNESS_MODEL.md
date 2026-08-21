# Freshness model

Freshness is frequency-aware and based on reporting `period_end`, not local
file modification time. The bounded thresholds are quarterly 150 days, TTM
210 days, annual aggregate 450 days and master data 90 days. States are
`CURRENT`, `STALE`, `VERY_STALE`, `QUALITY_WARNING` or `UNKNOWN`.

This is evidence freshness, not predictive confidence. A stale observation is
reported rather than silently removed or relabeled as current.
