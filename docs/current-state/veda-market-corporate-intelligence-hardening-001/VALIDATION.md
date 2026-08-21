# Validation

Focused FII-DII validation:

- Corporate, stock, cross-layer, fundamentals, institutional flow, freshness
  and API baseline: **31 passed**;
- Full FII-DII suite: **1340 passed**, one existing deprecation warning;
- Ruff on changed FII-DII modules: **passed**;
- live `/api/corporate/summary`, symbol summary, stock and cross-layer routes:
  **HTTP 200** after the controlled fixes;
- live five-symbol sample: **5/5 HTTP 200**, canonical identity resolved;
- live warm benchmark samples: Corporate global p50 **433.79 ms** (p90
  509.76 ms), Corporate symbol p50 **93.58 ms** (p90 97.10 ms), stock p50
  **501.31 ms** (p90 548.07 ms), cross-layer p50 **526.93 ms** (p90 550.47
  ms). The initial pre-bounded global request was ~40 s and was corrected
  before acceptance.

Focused VEDA validation:

- `platform/tests/test_market_provider.py`: **25 passed**;
- Full VEDA platform suite: **exit 0**;
- Ruff on changed VEDA provider/tests: **passed**;
- Corporate contract version and required fields are enforced at the provider
  boundary; invalid symbol/days/limit metadata is rejected.

Live VEDA adapter validation:

- `/api/v1/health`, `/api/v1/readiness` and `/api/v1/capabilities`: **HTTP 200**;
- `/api/v1/query` with `market.corporate.intelligence` and RELIANCE: **HTTP
  200 / SUCCEEDED**;
- returned `corporate-intelligence-1.0`, identified NSE identity, explicit
  source summary, freshness state and non-predictive interpretation.

Known repository-level conditions inherited from the predecessor remain
separate: unrelated VEDA Ruff import-order and mypy test-typing issues were
already present. They are not introduced by this programme and did not cause
the VEDA platform suite to fail.
