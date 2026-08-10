# VEDA-P001-06 Baseline Manifest

## Baseline Metadata

| Field | Value |
| --- | --- |
| `BASELINE_ID` | `VEDA-P001` |
| `DATE` | `2026-08-10` |
| `BRANCH` | `main` |
| `GOVERNING_SOURCE_HEAD` | `70643c9a2389729b5c73fe84f6ae2d2b7441ea85` |
| `PYTHON_VERSION` | `3.11.0` |
| `NODE_VERSION` | `24.16.0` |
| `NPM_VERSION` | `11.13.0` |
| `BACKEND_DEPENDENCY_MANIFEST` | `requirements.txt` |
| `FRONTEND_DEPENDENCY_MANIFEST` | `frontend/package.json`, `frontend/package-lock.json` |
| `ENDPOINT_COUNT` | `137` operations (`125` OpenAPI paths) |
| `ASTROLOGY_FIXTURE_COUNT` | `11` golden cases + `10` divergence rows |
| `SECURITY_POSTURE` | `MATERIALLY_CONTROLLED_WITH_LOCAL_ENV_POLICY` |
| `KNOWN_DIVERGENCES` | `10` personal-vs-REST rows |

## Validation Summary

| Validation | Result |
| --- | --- |
| Python test suite | `352 passed / 8 failed / 0 skipped` |
| Frontend test suite | `21 passed / 0 failed` |
| Frontend build | `PASS` |
| Runtime smoke | `PASS` |
| Kundli golden fixtures | `PASS` |
| API contract baseline | `PASS` |

## Known Failure Register

All eight remaining Python failures are contained in `tests/test_veda_chat_engine.py`.

| Test | Classification | Evidence | P001 Action |
| --- | --- | --- | --- |
| `test_chat_engine_attachment_prompt_explains_reviewed_save_flow` | `STALE_TEST` | monkeypatched `_run_turn` does not accept current `voice_mode` argument | documented only |
| `test_chat_engine_cools_down_provider_after_auth_failure` | `STALE_TEST` | same signature drift against current `_run_turn` call site | documented only |
| `test_chat_engine_bounds_history_and_message_size` | `STALE_TEST` | test expects removed/nonexistent private helper `_bounded_history` | documented only |
| `test_chat_engine_prefers_unified_retrieval` | `STALE_TEST` | current `ChatEngine._get_rag_context()` still calls legacy `.retrieve()` path and does not use unified bundle flow | documented only |
| `test_chat_engine_shadow_mode_compares_unified_and_legacy` | `STALE_TEST` | current `ChatEngine` does not wire `last_retrieval_audit` shadow logic into `_get_rag_context()` | documented only |
| `test_chat_engine_shadow_mode_can_keep_legacy_primary` | `STALE_TEST` | same retrieval-shadow contract drift | documented only |
| `test_chat_engine_tracks_local_evidence_and_instructs_ml_separation` | `STALE_TEST` | same `_run_turn(..., voice_mode=...)` stub mismatch and missing local-evidence wiring | documented only |
| `test_chat_engine_marks_research_as_temporary_and_flags_memory_conflict` | `STALE_TEST` | current `_get_external_research_context()` returns external research prompt text without the tested conflict-note merge | documented only |

## Why These Failures Remain

- They pre-date P001 completion and were reproduced unchanged during the full-suite run.
- They concern chat/retrieval feature drift, not the P001 security/regression mission.
- Fixing them would require chat-engine behavior decisions outside the authorised P001 scope.
