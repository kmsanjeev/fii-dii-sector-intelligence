# Post-remediation benchmark

## FII direct cross-layer

Scenario: RELIANCE `STOCK_CONFIRMATION`, three warm-ups and 20 measured calls
after a fresh FII process restart.

| Measure | Result |
|---|---:|
| Cold first request | 855.54 ms |
| Second request | 549.92 ms |
| Warm p50 | 443.61 ms |
| Warm p90 | 546.99 ms |
| Warm p95 | 568.94 ms |
| Warm maximum | 667.54 ms |

Compared with the controlled pre-remediation p50/p90 of `1581.37/1830.65 ms`,
the reduction was `1137.76/1283.66 ms`, or approximately `72.0%/70.1%`.

## FII multi-symbol and modes

| Scenario | p50 | p90/max sample | Samples |
|---|---:|---:|---:|
| HDFCBANK stock confirmation | 351.80 ms | 373.70 ms | 4 |
| TCS stock confirmation | 470.05 ms | 492.30 ms | 4 |
| LT stock confirmation | 448.43 ms | 598.47 ms | 4 |
| INFY stock confirmation | 367.99 ms | 412.60 ms | 4 |
| bounded Market overview, 1 sector/1 stock | 358.14 ms | 383.22 ms | 3 |
| bounded leadership discovery, 2 sectors/1 stock | 671.25 ms | 913.36 ms max | 3 |

Candidate limits remain enforced by the existing `10` sector / `5` stock
maximums; the controlled probes used smaller bounds.

## Formal VEDA provider

The enabled VEDA provider used the same FII endpoint and persistent client.
For 20 warm formal queries, p50 was `431.13 ms`, p90 `615.28 ms`, p95
`673.78 ms`, maximum `816.54 ms`. The adapter/Core overhead was not material
relative to the FII path and varied within normal local-run noise.
