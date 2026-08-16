# Acceptance Register

| Area | Result | Evidence |
|---|---|---|
| Baseline and parent history | PASS | `00_BASELINE.md`; parent artifacts preserved |
| Unknown universe freeze | PASS | `01_UNKNOWN_UNIVERSE_FREEZE.json`; 1,358; fixed hash/policies |
| Denominator correction | PASS | `00_BASELINE.md`; full and identified denominators explicit |
| Multi-level provenance | PASS_WITH_CONDITION | `02_PROVENANCE_MODEL.md`, `FINAL_MANIFEST.json` |
| Unknown resolution | PASS_WITH_CONDITION | `03_UNKNOWN_SOURCE_RESOLUTION.json`; unresolved cases retained |
| Sample design/freeze | PASS | `04_SOURCE_DIVERSITY_SAMPLE_PLAN.md`, `05_SAMPLE_FREEZE.json` |
| Blind adjudication | PASS | `06_ADJUDICATION_RESULTS.json`; frozen rubric reused |
| Source-diverse yield | PASS_WITH_CONDITION | 0/240; negligible; no threshold relaxation |
| Verified pool update | PASS | `08_VERIFIED_POOL_UPDATE.json`; 114 unchanged |
| Effective information bound | PASS_WITH_CONDITION | outcome-blind bound 27; raw N not independent N |
| DAY event boundary | PASS | discovery-only join after freeze |
| India inclusion | PASS_WITH_CONDITION | 18 adjudicated, 0 A/B |
| Formal access | PASS_WITH_CONDITION | high-value, prepared, unsent; human action retained |
| Stop/go | PASS_WITH_CONDITION | no further generic free-sample adjudication |
| Safety/governance | PASS | no astrology, ML, PRED, production, recruitment, raw/RAG ingestion |
| Reproducibility | PASS | focused tests, deterministic rerun, diff check |
| Git hygiene | PASS | selective staging only; ignored raw artifact preserved |
