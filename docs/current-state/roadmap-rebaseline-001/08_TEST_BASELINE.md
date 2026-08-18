# Test Baseline

The full repository suite has a known history of bounded 15-minute timeouts.
This programme established a split baseline rather than treating a monolithic
timeout as a pass.

| Group | Collected | Passed | Failed | Skipped | Timeout | Duration |
|---|---:|---:|---:|---:|---:|---:|
| Calculation / D20 / Muhurta | 57 | 57 | 0 | 0 | 0 | 9.04s |
| Language / knowledge / spirituality | 46 | 46 | 0 | 0 | 0 | 24.55s |
| Evidence source-diversity / adjudication | 13 | 13 | 0 | 0 | 0 | 111.27s |
| Evidence corpus / ADB / external readiness | 41 | 41 | 0 | 0 | 0 | 95.65s |
| Combined language + evidence attempt | not usable | not aggregated | not aggregated | not aggregated | 1 | 180s bound |
| **Reliable split aggregate** | **157** | **157** | **0** | **0** | **0** | bounded groups |

The combined attempt is retained as `TIMEOUT`, not `PASS`. The slowest split
group is source-diversity/adjudication; its cost is dominated by deterministic
corpus processing and is not treated as an anomalous production regression.
No unrelated performance refactor was made.
