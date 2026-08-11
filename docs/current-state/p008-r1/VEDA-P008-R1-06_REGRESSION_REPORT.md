# VEDA-P008-R1 Regression Report

Date executed: August 11, 2026

## Chat Reconciliation

```text
py -3.11 -m pytest tests/test_veda_chat_engine.py -q
```

Result:

- `8 passed`

## Router Contract

```text
py -3.11 -m pytest tests/test_veda_chat_router.py -q
```

Result:

- `12 passed`
- `1 warning` (`StarletteDeprecationWarning` from `fastapi.testclient`)

## Full Python Suite

```text
py -3.11 -m pytest -q
```

Result:

- `408 passed`
- `0 failed`
- `1 warning`

## Phase Validators

```text
py -3.11 scripts/validate_p002_astrology_registry.py
```

- `is_valid=true`
- `source_count=7`, `passage_count=6`, `claim_count=6`, `conflict_count=1`

```text
py -3.11 scripts/validate_p003_astrology_ontology.py
```

- `is_valid=true`
- `entity_count=131`, `rule_count=4`, `legacy_mapping_count=3`

```text
py -3.11 scripts/validate_p004_calculation_foundation.py
```

- `is_valid=true`
- `reference_fixture_count=25`, `validation_record_count=650`, `divergence_count=11`

```text
py -3.11 scripts/validate_p005_interpretation_validation.py
```

- `is_valid=true`
- `surface_count=14`, `legacy_rule_count=32`, `high_stakes_count=5`

```text
py -3.11 scripts/validate_p006_research_platform.py
```

- `is_valid=true`
- `domain_count=1`, `mission_count=2`, `candidate_count=4`, `ledger_event_count=92`

## Frontend Gate

```text
cmd /c npx vitest run --pool=threads --maxWorkers=1
```

- `7 files passed`
- `25 tests passed`

```text
cmd /c npm run build
```

- build passed
- inherited warning remains: large production chunks over `500 kB`

## Runtime Smoke

Official command:

```text
py -3.11 scripts/run_p001_smoke.py
```

Result:

- checks completed, but the process exited non-zero due to the inherited Windows temporary-directory cleanup defect involving `frontend.stderr.log`

Operational smoke result via `run_smoke()` with cleanup errors suppressed at invocation time:

- `status=PASS`
- backend `/health`: `200`
- datasets loaded: `41 / 43`
- auth config: `enabled=false`, `runtime_env=local`
- chat capability: `PASS`
- retrieval capability: `PASS`
- kundli calculation: `PASS` (`lagna_sign=Libra`, `planet_count=11`)
- pipeline status: `PASS`
- broker status: `PASS`
- frontend startup: `PASS`
