# Data inventory

Audit date: 2026-08-21. Counts are read-only observations of the current
working tree; generated/data files were not staged by this activity.

| Dataset | Rows | Date range | Role | Limitation |
|---|---:|---|---|---|
| `data/historical/institutional/institutional_positioning_history.csv` | 2,618 | 2016-01-01 to 2026-08-19 | F&O participant OI, volume and FII derivatives net | No nulls or duplicate dates observed |
| `data/historical/institutional/cash_market_flows_history.csv` | 647 | 2024-01-01 to 2026-08-18 | Cash category buy/sell/net in ₹ crore | FPI has 12 null rows; RETAIL/OTHERS have 65 null rows |
| `data/intelligence/participant_flow_scores.csv` | 2,618 | 2016-01-01 to 2026-08-19 | Rolling flow metrics and normalized scores | Cash score history is unavailable before cash coverage |
| `data/intelligence/participant_intelligence.csv` | 2,618 | 2016-01-01 to 2026-08-19 | Conviction, divergence and regime | Cash-derived fields are unavailable where cash evidence is unavailable |
| `data/intelligence/institutional_trend.csv` | 2,615 | 2016-01-01 to 2026-08-14 | Legacy trend output | Stale relative to current participant history |

The public contract is derived from participant flow and intelligence outputs.
It reports F&O and cash source dates separately and never treats a missing
numeric observation as zero.
