# VEDA-P005-R1 Regression Report

Date baseline: `2026-08-10`

## Targeted R1 Tests

- `py -3.11 -m pytest tests/test_veda_interpretation_safety_remediation.py -q`
  - result: `4 passed`
- `npx vitest run src/test/AstroSafetyPresentation.test.tsx --pool=threads --maxWorkers=1`
  - result: `1 passed`

## Protected Phase Baselines

- `py -3.11 -m pytest tests/test_veda_astrology_golden.py -q`
  - result: `6 passed`
- `py -3.11 -m pytest tests/test_veda_astrology_governance.py -q`
  - result: `5 passed`
- `py -3.11 -m pytest tests/test_veda_astrology_ontology.py -q`
  - result: `5 passed`
- `py -3.11 -m pytest tests/test_veda_calculation_validation.py -q`
  - result: `5 passed`
- `py -3.11 -m pytest tests/test_veda_interpretation_validation.py -q`
  - result: `5 passed`
- `py -3.11 -m pytest tests/test_api_contract_baseline.py -q`
  - result: `3 passed`
- `py -3.11 -m pytest tests/test_auth_governance.py -q`
  - result: `6 passed`
- `py -3.11 -m pytest tests/test_broker_security.py -q`
  - result: `3 passed`

## Governance / Validation Scripts

- `py -3.11 scripts/validate_p002_astrology_registry.py`
  - result: `PASS`
- `py -3.11 scripts/validate_p003_astrology_ontology.py`
  - result: `PASS`
- `py -3.11 scripts/validate_p004_calculation_foundation.py`
  - result: `PASS`

## Frontend Validation

- `npx vitest run --pool=threads --maxWorkers=1`
  - result: `22 passed`
- `npm run build`
  - result: `PASS`
  - note: existing Vite large-chunk warning remains informational only

## Runtime Smoke

Manual smoke execution equivalent to `scripts/run_p001_smoke.py` passed:

- backend startup and `/health`
- auth configuration
- chat capability
- retrieval capability
- kundli calculation
- pipeline status
- broker status
- frontend startup

Harness note:

- `scripts/run_p001_smoke.py` still fails on Windows during temporary-directory cleanup after the checks; this is treated as smoke-harness tooling debt, not as an application runtime failure.

## Full Python Suite

- `py -3.11 -m pytest -q`
  - result: `376 passed, 8 failed`
  - inherited baseline condition: all `8` failures remain in `tests/test_veda_chat_engine.py`
  - no new R1-caused failures observed
