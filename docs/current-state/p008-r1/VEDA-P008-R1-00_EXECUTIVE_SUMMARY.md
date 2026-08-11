# VEDA-P008-R1 Executive Summary

Date: August 11, 2026

VEDA-P008-R1 reconciled the pre-existing `tests/test_veda_chat_engine.py` failure block against the post-P008 chat/retrieval architecture. The authoritative contract is now explicit: chat distinguishes local approved evidence from temporary external research, prefers unified retrieval when enabled, supports audited shadow comparison, keeps provider hard-failure cooldowns, and bounds conversation history.

Key outcomes:

- all eight chat-engine failures were reproduced, classified, and resolved without skip/xfail;
- `ChatEngine` now populates the router-facing `last_local_evidence` and `last_retrieval_audit` metadata that P008 Admin and API contracts already expect;
- unified retrieval, legacy fallback, shadow mode, temporary research handling, conflict signalling, ML/evidence separation, and `voice_mode` invocation are documented as the authoritative post-P008 contract;
- `requirements.txt` now declares `jsonschema`, which was required by committed governance/ontology/research tests but was previously missing from the manifest;
- the full Python suite is now green: `408 passed, 0 failed, 1 warning`.

Protected boundaries preserved:

- production astrology calculations: unchanged;
- approved core knowledge: unchanged;
- research approval/promotion behavior: unchanged;
- P001-P008 guarded baselines: preserved.

Remaining condition:

- the inherited Windows cleanup defect in `scripts/run_p001_smoke.py` still causes the official smoke command to exit non-zero after the checks complete; the underlying `run_smoke()` result itself passed on August 11, 2026.
