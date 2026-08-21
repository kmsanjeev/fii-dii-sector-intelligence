# Before / after coverage

| Capability | Before RX1 | After RX1 |
|---|---|---|
| Daily stage inclusion | Present | Preserved |
| Official event refresh | nselib Brotli failure | Shared NSE client, bounded official endpoint |
| Source failure visibility | Empty result; ignored return | Explicit refresh state and non-zero module exit |
| Last valid dataset | Preserved incidentally | Preserved and documented by contract |
| Row retrieval time | Absent | New rows have UTC `retrieved_at`; legacy null |
| Dataset build time | Implicit file mtime | Explicit `dataset_build_at` |
| Lifecycle state | Mostly static status | Explicit source-language states |
| Lineage | No additive fields | Parent/related/group/version/method/confidence fields |
| Result freshness | Ambiguous filing-date selection | Valid-date basis and filing coverage disclosed |
| Fuzzy inference | Not used | Still prohibited |
| Contract version | `corporate-intelligence-1.0` | Unchanged |

RX1 is operational with conditions because historical rows do not have
row-level retrieval timestamps, historical filing dates remain partially
malformed, and source access remains external/source-dependent.
