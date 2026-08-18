# VEDA-CALC-SIDEREAL-ASC-TZ-001 — Acceptance Register

| Criterion | Status | Evidence |
|---|---|---|
| Baseline and parent history preserved | PASS | `00_BASELINE_RECONCILIATION.md` |
| Official IMD/PAC source inspected at page level | PASS | `01_REFERENCE_RESEARCH.md` |
| Reference standard uncertainty tracked | PASS_WITH_CONDITION | `01_REFERENCE_RESEARCH.md`, `01_IAE_REFERENCE.json` |
| No fake citation or redistributed PDF | PASS | Metadata only; no PDF tracked |
| Lahiri/Nirayana decomposition recorded | PASS_WITH_CONDITION | `02_LAHIRI_REFERENCE_STANDARD.md`, `02_NIRAYANA_REGRESSION.json` |
| Rashi/Nakshatra/Pada boundaries covered | PASS | `03_NIRAYANA_BOUNDARIES.md`, focused tests |
| Independent Ascendant corpus >=100 | PASS | 120 cases, `05_ASCENDANT_RESULTS.json` |
| Ascendant boundary decision explicit | PASS_WITH_CONDITION | `04_ASCENDANT_VALIDATION.md` |
| Historical timezone corpus/version/gap/fold policy | PASS | `05_TIMEZONE_VALIDATION.md`, `07_TIMEZONE_RESULTS.json` |
| Gold/Silver/Stress/predictive boundaries preserved | PASS | `06_DOWNSTREAM_IMPACT.md` |
| No D20 interpretation or prediction activation | PASS | governance assertions |
| Canonical API snapshot repair only | PASS | generator output, focused API tests |
| Focused/regression/full-suite checks | PASS | `08_FULL_SUITE_BASELINE.md`; focused 50 passed; full 956 passed |
| Generated baseline repairs bounded and validated | PASS_WITH_CONDITION | P013 canonical export refreshed; ignored P005 export refreshed locally; no production astrology logic changed |
| Unified RAG rebuild policy | PASS | Existing unified corpus rebuilt twice; 1,205 records; both rebuilds wrote no changes and hashes were identical |
| Approved Core / D20 / prediction boundaries | PASS | Approved Core unchanged; D20 interpretation remains gated; no prediction/ML/production activation |
| Selective staging, commit, push and tag | PASS | Completed after final diff review; preserved unrelated city-cache edit unstaged |

Overall acceptance: `PASS_WITH_CONDITION` if all executable validations pass, because independent all-body Lahiri/Nirayana authority remains partial and Ascendant boundary policy remains required.
