# Validation

Focused validation on 2026-08-21:

- Ruff: passed for the changed service and focused test module;
- compileall: passed;
- focused contract/cross-layer suite: `11 passed`;
- duplicate source fields produce stable IDs and deterministic deduplication;
- cadence-aware freshness tests passed;
- no raw external provider data was added;
- real HTTP probes: `/api/stocks/PAYTM` and
  `/api/market/intelligence/cross-layer?mode=STOCK_CONFIRMATION&symbol=PAYTM`
  returned 200 and exposed contract 1.1;
- ten warm HTTP samples: stock min/p50/p90/max `510.57/576.36/907.88/1268.03`
  ms; cross-layer `948.46/1029.64/1246.52/1387.61` ms;
- FII full suite: `1324 passed, 1 warning` in `765.74s`;
- standalone VEDA platform suite: `76 passed, 2 warnings`;
- git diff check: passed.

The required direct daily stock and sector sources remain unavailable in a
complete governed form. This is an operational condition, not a test failure.
