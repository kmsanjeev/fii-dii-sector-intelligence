# VEDA-P006 Validation Report

Date baseline: `2026-08-10`

## Protected Python Baselines

- command:
  - `py -3.11 -m pytest tests/test_veda_astrology_golden.py tests/test_api_contract_baseline.py tests/test_auth_governance.py tests/test_broker_security.py -q`
- result:
  - `18 passed / 0 failed`

- command:
  - `py -3.11 -m pytest tests/test_veda_astrology_governance.py tests/test_veda_astrology_ontology.py tests/test_veda_calculation_validation.py tests/test_veda_interpretation_validation.py -q`
- result:
  - `20 passed / 0 failed`

- command:
  - `py -3.11 -m pytest tests/test_veda_interpretation_safety_remediation.py tests/test_veda_research_platform_unit.py tests/test_veda_research_platform_integration.py tests/test_veda_research_platform_security.py tests/test_veda_research_platform_api.py tests/test_veda_research_platform_artifacts.py -q`
- result:
  - `15 passed / 0 failed`

## Registry and Ontology Validators

- command:
  - `py -3.11 scripts/validate_p002_astrology_registry.py`
- result:
  - `PASS`

- command:
  - `py -3.11 scripts/validate_p003_astrology_ontology.py`
- result:
  - `PASS`
  - entities: `131`
  - relations: `34`
  - rules: `4`
  - legacy mappings: `3`

- command:
  - `py -3.11 scripts/validate_p006_research_platform.py`
- result:
  - `PASS`
  - domains: `1`
  - core knowledge records: `2`
  - missions: `2`
  - runs: `3`
  - candidates: `4`
  - approvals: `3`
  - ledger events: `92`

## Frontend

- command:
  - `cmd /c npx vitest run --pool=threads --maxWorkers=1`
- result:
  - `22 passed / 0 failed`

- command:
  - `cmd /c npm run build`
- result:
  - `PASS`
- note:
  - inherited large-chunk warning remains present in the production bundle output

## Runtime Smoke

- command:
  - `py -3.11 scripts/run_p001_smoke.py`
- result:
  - `PASS`
- notable checks:
  - backend `/health`: `200`
  - datasets loaded: `41 / 43`
  - auth runtime: `local`
  - kundli smoke lagna sign: `Libra`
  - research universe stats: `PASS`
  - frontend startup: `200`

## Full Python Suite

- command:
  - `py -3.11 -m pytest -q`
- result:
  - `387 passed / 8 failed`
- failure scope:
  - all `8` failures remain confined to `tests/test_veda_chat_engine.py`
- failing tests:
  - `test_chat_engine_attachment_prompt_explains_reviewed_save_flow`
  - `test_chat_engine_cools_down_provider_after_auth_failure`
  - `test_chat_engine_bounds_history_and_message_size`
  - `test_chat_engine_prefers_unified_retrieval`
  - `test_chat_engine_shadow_mode_compares_unified_and_legacy`
  - `test_chat_engine_shadow_mode_can_keep_legacy_primary`
  - `test_chat_engine_tracks_local_evidence_and_instructs_ml_separation`
  - `test_chat_engine_marks_research_as_temporary_and_flags_memory_conflict`

Interpretation:

- P006 did not add new failures outside the inherited eight-test chat-engine block.
