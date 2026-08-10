# VEDA-P002-09 Final Acceptance

## Acceptance Target

P002 passes only if:

1. source registry exists
2. authority rubric exists
3. provenance model exists
4. passage schema exists
5. claim schema exists
6. conflict schema exists
7. approval workflow exists
8. versioning policy exists
9. pilot sources are registered
10. one pilot domain completes the governance lifecycle
11. existing runtime remains unchanged
12. P001 protections remain intact

## Current Artifact Check

- source registry: present
- authority rubric: present
- citation / provenance standard: present
- contradiction policy: present
- approval workflow: present
- versioning standard: present
- pilot data: present
- legacy rule strategy: present

## Validation Evidence

### Targeted Validation

- `py -3.11 -m pytest tests/test_veda_astrology_golden.py tests/test_api_contract_baseline.py tests/test_auth_governance.py tests/test_broker_security.py tests/guardrails/test_secret_governance.py tests/test_veda_astrology_governance.py -q`
  - result: `26 passed / 0 failed`
- `py -3.11 scripts/validate_p002_astrology_registry.py`
  - result: `PASS`
- `cmd /c npm run build`
  - result: `PASS`
- `py -3.11 scripts/run_p001_smoke.py`
  - result: `PASS`

### Frontend Tests

- `cmd /c npm test`
  - result: worker startup timeouts under the parallel validation run; no assertion failures were reported in the tests that executed
- `cmd /c npx vitest run --pool=threads --maxWorkers=1`
  - result: `21 passed / 0 failed`

### Full Python Regression Check

- `py -3.11 -m pytest -q`
  - result: `357 passed / 8 failed`
  - finding: failure count and failure scope match the known P001 chat-engine baseline condition

### Known Conditions Carried Forward

1. The eight known failures remain confined to `tests/test_veda_chat_engine.py`.
2. They are unchanged from the P001 baseline and were not introduced by P002.
3. The default frontend Vitest worker pool showed startup instability during one parallel run, but the complete frontend suite passed when rerun in single-worker mode.

## Acceptance Decision

`PASS WITH CONDITIONS`

## Basis

- the astrology source registry, passage layer, claim layer, contradiction layer, approval layer, policy layer, and legacy register now exist in machine-readable form
- the pilot domain completed the governance lifecycle through `VEDA-APR-000001`
- P001 kundli, API, auth, broker, build, and smoke protections still pass
- no production astrology behavior was intentionally changed
