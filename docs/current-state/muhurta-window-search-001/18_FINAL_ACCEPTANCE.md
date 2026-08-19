# Final acceptance

| Area | Result | Evidence |
|---|---|---|
| Baseline and frozen contracts | PASS | `00_BASELINE.md`, RX1 tests |
| Transition source and factor audit | PASS_WITH_CONDITION | `02_FACTOR_TRANSITION_DEPENDENCIES.json`, `03_TRANSITION_SOURCE_AUDIT.json` |
| Bounded input and timezone safety | PASS | focused tests |
| Segmentation and representative policy | PASS | `04_SEGMENTATION_CONTRACT.md` |
| RX1 composition | PASS | RX1 regression and search tests |
| Categorical comparison/no score | PASS | `06_CANDIDATE_COMPARATOR.md`, focused tests |
| Merge/no-result/scope gates | PASS | `10_WINDOW_MERGE_VALIDATION.json`, `11_NO_RESULT_ABSTENTION.json` |
| API | PASS | `/api/muhurta/search` OpenAPI validation |
| Runtime smoke | PASS_WITH_CONDITION | Business, Education, no-result and not-ready invocations |
| Performance | PASS_WITH_CONDITION | `14_PERFORMANCE.md` |
| Full suite | NOT_PASS / TIMEOUT | prior full-suite timeout remains separately reported; focused inherited suites pass |
| RAG/Approved Core/provider calls | PASS | `15_CONSUMER_AUDIT.json`, `17_PARALLEL_STATE.md` |

Final decision: `MUHURTA_WINDOW_SEARCH_OPERATIONAL_WITH_LIMITATIONS`.
