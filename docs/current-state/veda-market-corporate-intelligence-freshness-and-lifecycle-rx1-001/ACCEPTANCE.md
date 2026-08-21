# Acceptance register

| ID | Criterion | Status |
|---|---|---|
| AC01 | Existing Corporate contract preserved | PASS |
| AC02 | Root cause established from source and code evidence | PASS |
| AC03 | Scheduler stage 7B preserved | PASS |
| AC04 | Official source path repaired without new provider | PASS |
| AC05 | Source failure preserves last valid dataset | PASS_WITH_CONDITION |
| AC06 | Failure state and truthful exit status exposed | PASS |
| AC07 | New row retrieval timestamps added | PASS |
| AC08 | Legacy timestamps remain null | PASS |
| AC09 | Dataset build time is separate | PASS |
| AC10 | Lifecycle state requires explicit language | PASS |
| AC11 | Completion is not inferred from dates | PASS |
| AC12 | Additive lineage fields present | PASS |
| AC13 | Fuzzy lineage is prohibited | PASS |
| AC14 | Result-event and fundamental freshness separated | PASS |
| AC15 | Malformed legacy years rejected | PASS |
| AC16 | Quarterly freshness basis disclosed | PASS_WITH_CONDITION |
| AC17 | Idempotent event-key merge preserved | PASS |
| AC18 | Focused tests pass | PASS |
| AC19 | No RAG/ML/PRED/EMP/Jyotish/BEBOS change | PASS |
| AC20 | Full/regression/live/performance validation | PASS_WITH_CONDITION |
| AC21 | Governance synchronized | PASS |
| AC22 | Selective Git staging and clean tree | PASS_WITH_CONDITION |

AC20 is conditional only because the pre-existing `data_loader.py` lint
findings and dependency deprecation warnings remain outside RX1 scope. AC22 is
conditional because the repository contains pre-existing tracked/generated and
ignored Market/RAG/runtime changes that were deliberately not staged.

Final decision:
`VEDA_MARKET_CORPORATE_INTELLIGENCE_FRESHNESS_AND_LIFECYCLE_RX1_OPERATIONAL_WITH_CONDITIONS`
