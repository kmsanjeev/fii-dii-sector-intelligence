# VEDA-P008-R1 Failure Classification

| Test | Primary Class | Diagnosis | Resolution |
| --- | --- | --- | --- |
| `test_chat_engine_attachment_prompt_explains_reviewed_save_flow` | `B` | production prompt no longer explained the reviewed-save boundary; test double also used a stale `_run_turn` signature | restored attachment/save-flow guidance in the system prompt and updated the mock to accept `voice_mode` |
| `test_chat_engine_cools_down_provider_after_auth_failure` | `B` | hard auth failures were not cooling providers despite the governed cooldown config; test double also used a stale `_run_turn` signature | added hard-failure cooldown handling for auth-style provider errors and updated the mock signature |
| `test_chat_engine_bounds_history_and_message_size` | `B` | bounded-history behavior had drifted out of `ChatEngine` | added production `_bounded_history()` and used it inside `chat()` |
| `test_chat_engine_prefers_unified_retrieval` | `B` | chat still used the old legacy retriever path even though unified retrieval existed and was enabled by config | made unified retrieval the primary chat path when enabled |
| `test_chat_engine_shadow_mode_compares_unified_and_legacy` | `B` | chat was not emitting retrieval audit metadata or shadow comparisons | added shadow retrieval audit construction and shadow-log support |
| `test_chat_engine_shadow_mode_can_keep_legacy_primary` | `B` | legacy-primary operation and unified-shadow audit were not wired into chat | restored legacy-primary mode with unified shadow audit when unified retrieval is disabled |
| `test_chat_engine_tracks_local_evidence_and_instructs_ml_separation` | `B` | chat did not preserve local evidence metadata or explicit ML/evidence separation guidance; test double also used a stale `_run_turn` signature | propagated unified summary into `last_local_evidence`, added ML separation prompt guidance, and updated the mock signature |
| `test_chat_engine_marks_research_as_temporary_and_flags_memory_conflict` | `D` | temporary research framing existed, but the older chat expectation for explicit memory-vs-external conflict signalling was no longer surfaced at the chat boundary | kept the temporary-research architecture and added a compatibility-layer conflict note derived from current local evidence when governed research metadata does not provide one |

Stale test doubles updated:

- `test_chat_engine_attachment_prompt_explains_reviewed_save_flow`
- `test_chat_engine_cools_down_provider_after_auth_failure`
- `test_chat_engine_tracks_local_evidence_and_instructs_ml_separation`

Implementation defects corrected:

- provider hard-failure cooldown drift;
- missing history bounding;
- unified/legacy/shadow retrieval contract drift;
- missing local evidence metadata propagation;
- missing per-turn research conflict note compatibility.
