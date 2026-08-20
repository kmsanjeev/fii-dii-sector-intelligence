# Data inventory

| Dataset | Observed coverage | Latest observed | Rows | Relevant fields | Status |
|---|---:|---:|---:|---|---|
| `institutional_positioning_history.csv` | 2016-01-01 to 2026-08-19 | 2026-08-19 | 2,618 | participant aggregate futures OI/volume, FII futures statistics | supported aggregate contract |
| `participant_flow_scores.csv` | 2016-01-01 to 2026-08-19 | 2026-08-19 | 2,618 | daily OI delta and 1/3/5/10/20/60D derived windows | supported internal derivation |
| `participant_intelligence.csv` | 2016-01-01 to 2026-08-19 | 2026-08-19 | 2,618 | scores, conviction, existing divergences | supported descriptive derivation |
| `cash_market_flows_history.csv` | 2024-01-01 to 2026-08-18 | 2026-08-18 | 647 | cash category buy/sell/net crore | separate, lagged/partial |
| `index_options.csv` | observed through 2026-08-05 | 2026-08-05 | provider-local file | index PCR/spot only | not participant options |
| `fno_intelligence.csv` | provider-local stock-futures file | 2026-08-14 in current snapshot | provider-local | symbol-level futures OI | not participant-wise; not merged |

Participant coverage in the NSE participant source is FII, DII, Pro and Client
plus a TOTAL row. The current persisted participant history stores four
participant rows conceptually; it does not retain raw source rows or raw option
buckets. Raw provider files remain local/ignored and are not committed.

Observed source-level instrument buckets include future index, future stock,
index call/put options and stock call/put options. The runtime contract only
publishes the aggregate futures result because that is the persisted, tested
history available to downstream consumers.
