# Validation

## Tests

- FII cross-layer/upstream focused suite: `32 passed`.
- FII Ruff on changed code/tests: passed.
- FII compile/import checks: passed.
- VEDA platform suite: `68 passed`, existing Authlib/Starlette deprecation
  warnings only.
- VEDA compileall: passed.
- VEDA Ruff: pre-existing import-order failure in
  `platform/migrations/versions/0001_identity_platform.py`.
- VEDA mypy: three pre-existing errors in
  `platform/tests/test_market_provider.py`; no VEDA code changed in this RX.

The full FII suite is the final regression gate and its actual result is
recorded in the acceptance register after completion.

## Semantic and safety checks

- Baseline and post-remediation institutional canonical JSON hashes are both
  `5c438c0e1a01ffd910013f74386289ac4a1ad6288738dee0edba60025bf87ee2`.
- Two identical live FII cross-layer responses produced the same canonical
  JSON SHA-256: `4b1685f4f721a57019478efed22004858455a981458a5b19a2d2f8e3fcc882ee`.
- Cross-layer response contract remains `cross-layer-1.0`.
- Market, institutional-flow, sector-rotation, stock-intelligence and
  fundamental-evidence contracts remain unchanged.
- Alignment, conflicts, source dates, freshness, quality and limitations remain
  present.
- Failure-isolation fixtures continue to preserve explicit insufficient data.
- No prediction, recommendation, target price, ML, RAG, EMP, Jyotish, identity,
  subscription, Personal Vault or BEBOS behavior changed.
- No direct institutional-source stream was opened.
