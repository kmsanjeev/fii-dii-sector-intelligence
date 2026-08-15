# P027 Existing-Capability Audit

## Existing

- `engines/ai/orchestration/contracts.py` already provides governed reasoning evidence, trust zones, method variants, and request modes.
- `engines/ai/orchestration/reasoning.py` provides a reusable convergence summary and double-counting signal.
- `engines/intelligence/jyotisha_runtime.py` owns deterministic chart facts and stable chart IDs.
- P020-P026 domain aggregators already preserve supporting, opposing, conditional, blocked, and explainability patterns.
- PRED-001..003 provide prediction handoff contracts; COMM/LANG/GROUP/EMO remain presentation and context layers.

## Reuse / Extend / New

| Area | Reuse | Extend | New required | Why |
|---|---|---|---|---|
| Evidence | `ReasoningEvidence`, domain evidence records | P027 canonical fields/roles | `SynthesisEvidence` adapter | Existing records have different domain shapes; P027 must retain provenance without replacing them. |
| Reasoning | `convergence_summary` | lineage-aware clusters and authority | `P027SynthesisEngine` | One deterministic cross-domain owner is needed. |
| Calculations | `JyotishaRuntime`, D1/Varga/Dasha/Transit engines | none | none | P027 must not recalculate facts. |
| Response | existing ChatEngine and COMM-002 | synthesis summary handoff | none | ChatEngine remains response owner. |
| Multi-chart | existing chart IDs and request subjects | safe comparative contract | limited `compare_charts` contract | Full compatibility is explicitly out of scope. |

No parallel Jyotisha engine, RAG corpus, provider path, or conversation store was created.
