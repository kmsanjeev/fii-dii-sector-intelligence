# VEDA-P003-08 Validation Report

## P003-Specific Validation

### Schema / Data Export Consistency

- command:
  - `py -3.11 -m pytest tests/test_veda_astrology_ontology.py -q`
- result:
  - `5 passed / 0 failed`

### Protected Python Baseline + Governance Validation

- command:
  - `py -3.11 -m pytest tests/test_veda_astrology_golden.py tests/test_api_contract_baseline.py tests/test_auth_governance.py tests/test_broker_security.py tests/guardrails/test_secret_governance.py tests/test_veda_astrology_governance.py tests/test_veda_astrology_ontology.py -q`
- result:
  - `31 passed / 0 failed`

### P002 Registry Validator

- command:
  - `py -3.11 scripts/validate_p002_astrology_registry.py`
- result:
  - `PASS`

### P003 Ontology Validator

- command:
  - `py -3.11 scripts/validate_p003_astrology_ontology.py`
- result:
  - `PASS`
  - `131` entities
  - `34` relations
  - `4` rules
  - `3` legacy mappings
  - `0` broken references
  - `0` duplicate IDs

## Frontend Validation

### Frontend Tests

- command:
  - `cmd /c npx vitest run --pool=threads --maxWorkers=1`
- result:
  - `21 passed / 0 failed`

### Frontend Build

- command:
  - `cmd /c npm run build`
- result:
  - `PASS`
- note:
  - Vite reported a chunk-size warning for a large production bundle, but the build completed successfully.

## Runtime Smoke

- command:
  - `py -3.11 scripts/run_p001_smoke.py`
- result:
  - `PASS`
- notable runtime details:
  - backend `/health`: `200`
  - datasets loaded: `41 / 43`
  - auth runtime: `local`, disabled in smoke mode
  - kundli smoke lagna sign: `Libra`
  - frontend startup: `200`

## Full Python Suite

- command:
  - `py -3.11 -m pytest -q`
- result:
  - `362 passed / 8 failed`
- failure scope:
  - all `8` failures remain in `tests/test_veda_chat_engine.py`
- current failing tests:
  - `test_chat_engine_attachment_prompt_explains_reviewed_save_flow`
  - `test_chat_engine_cools_down_provider_after_auth_failure`
  - `test_chat_engine_bounds_history_and_message_size`
  - `test_chat_engine_prefers_unified_retrieval`
  - `test_chat_engine_shadow_mode_compares_unified_and_legacy`
  - `test_chat_engine_shadow_mode_can_keep_legacy_primary`
  - `test_chat_engine_tracks_local_evidence_and_instructs_ml_separation`
  - `test_chat_engine_marks_research_as_temporary_and_flags_memory_conflict`

## Interpretation

P003 did not introduce new protected-baseline failures.

The inherited chat-engine failure block remains a carried condition, consistent with the prior governed baseline.
