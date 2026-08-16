# Acceptance register

| ID | Requirement | Result |
|---|---|---|
| AC01 | Parent history preserved | PASS |
| AC02 | Official schema fields verified | PASS |
| AC03 | `ctimetype` separated from birth precision | PASS |
| AC04 | `itimeacc`/`stimeacc` parsed exactly | PASS |
| AC05 | `time_unknown` placeholder safeguard | PASS |
| AC06 | `bdata_alt` and source-note conflicts retained | PASS |
| AC07 | Official `dsc` classes and unknown values preserved | PASS |
| AC08 | Rodden rating not auto-mapped to VEDA tier | PASS |
| AC09 | Structured candidates and adjudication state reported | PASS_WITH_CONDITION |
| AC10 | Cross-tabs and DAY-event overlap aggregate-only | PASS |
| AC11 | No new event corroboration | PASS |
| AC12 | India reassessment completed | PASS |
| AC13 | Power planner reused without doctrine change | PASS |
| AC14 | Astrology/features/ML/RAG/PRED/production/recruitment locked | PASS |
| AC15 | Raw provider data excluded from Git | PASS |
| AC16 | Parent regression suite | PASS (35 passed) |
| AC17 | Corrective focused suite | PASS (8 passed) |
| AC18 | Initial combined suite | PASS_WITH_CONDITION (timeout; rerun split suites passed) |
| AC19 | Determinism | PASS |
| AC20 | Selective staging, commit, push, tag | PENDING_FINAL_GIT |

Overall acceptance: `PASS_WITH_CONDITION`. The condition is authorized source-note adjudication before any birth tier is promoted or event corroboration is expanded.
