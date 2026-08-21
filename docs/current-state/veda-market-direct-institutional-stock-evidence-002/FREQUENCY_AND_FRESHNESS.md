# Frequency and freshness

Frequency is component-specific:

| Component | Frequency | Freshness thresholds |
|---|---|---|
| disclosed deal reports | `DAILY` | current <=3 days; delayed <=10; stale >10 |
| ownership snapshots | `QUARTERLY` | current <=120 days; delayed <=240; stale >240 |
| derived deal signal | `DAILY` as-of | same cadence thresholds; interpretation remains derived |

Future dates are `QUALITY_WARNING`; missing/unparseable dates are
`UNKNOWN_FREQUENCY`. The reference date is UTC today unless a deterministic
test reference date is supplied. Freshness is not proof of semantic
completeness.
