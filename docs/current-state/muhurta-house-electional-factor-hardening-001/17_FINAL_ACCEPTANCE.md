# Final Acceptance

| Criterion | Result |
|---|---|
| Starting commit verified | PASS |
| T2 contracts preserved and hashes verified | PASS |
| Existing Ascendant calculation reused | PASS_WITH_CONDITION |
| Canonical diagnostic Lagna factor documented | PASS_WITH_CONDITION |
| 12-sign synthetic coverage | PASS |
| Lagna boundary policy preserved | PASS_WITH_CONDITION |
| Planetary calculation inventory | PASS_WITH_CONDITION |
| Planetary source semantics | SOURCE_PARTIAL; machine binding blocked |
| Benefic/malefic, dignity and aspect assumptions | Rejected as ungoverned |
| Griha Pravesha context schema | PASS_WITH_CONDITION |
| Missing context abstention / invalid fail-closed policy | PASS |
| Focused calculation/Muhurta/source-witness regression suite | PASS: 113 passed in 8.40s |
| Deterministic bundle rerun | PASS |
| JSON artifact parsing | PASS |
| `git diff --check` | PASS |
| New immutable machine-ready versions | NOT CREATED; not justified |
| Engine handoff | NOT GENERATED; zero machine-ready activities |
| Production House Construction runtime | INACTIVE |
| Production Griha Pravesha runtime | INACTIVE |
| Existing Business/Education/Vehicle/Consecration runtime | UNCHANGED |
| P032 / Personal Bala / RAG / prediction / ML | UNCHANGED |
| Approved Core | 17 → 17 |

Decision: `MUHURTA_HOUSE_ELECTIONAL_FACTORS_MACHINE_PARTIAL`.

The remaining blocker is evidence quality, not a missing generic calculator:
the reusable calculation paths exist with conditions, but a primary,
lineage-complete electional Lagna and planetary predicate contract was not
verified. The next engine expansion must not start automatically.
