# Baseline benchmark

## Reference measurements

The predecessor record reported stock p50/p95 approximately `436/568 ms` and
cross-layer p50/p95 approximately `4161/4377 ms`; the earlier cross-layer
record reported approximately `800-1030 ms`. Those historical samples were not
assumed to be comparable without reproduction.

## Controlled pre-remediation run

Host: Windows repository runtime, Python 3.11.9, local FII HTTP on port 8001.
Scenario: `GET /api/market/intelligence/cross-layer?mode=STOCK_CONFIRMATION&symbol=RELIANCE`.
Three warm-up calls preceded 20 measured calls.

| Surface | p50 | p90 | p95 | Notes |
|---|---:|---:|---:|---|
| Direct cross-layer | 1581.37 ms | 1830.65 ms | 1893.37 ms | 20 warm calls |
| Direct institutional | 1003.52 ms | 1148.55 ms | 1355.74 ms | 20 warm calls |
| Direct stock | 864.09 ms | 1034.90 ms | 1062.69 ms | 20 warm calls |
| Direct corporate summary | 59.00 ms | 80.77 ms | 95.13 ms | 20 warm calls |

The 4.1s condition was not reproduced in this run. The cross-layer path was
nevertheless materially slower than its component contract boundaries and the
profiler identified duplicated institutional rolling work.
