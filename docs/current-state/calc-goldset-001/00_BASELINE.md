# VEDA-CALC-GOLDSET-001 — Baseline

Execution date: 2026-08-18. The expected specification commit was not the repository HEAD; the actual starting commit was `23e8856af2eca3b886b63be98d195fddf9212563` on `main`. The pre-existing tracked edit to `data/reference/city_coords_cache.csv` was preserved and excluded from this activity.

The calculation baseline reuses the current `KundliEngine`, P004 reference fixtures, P015/P015-RX/P015-RX2 Varga governance, P016 Dasha, P019 transit, and existing ADB/OGDB governed input artifacts. No predictive outcome, feature score, ML model, PRED-M4 change, production prediction, RAG rebuild, or Approved Core promotion was performed.

Local raw ADB XML/zip and OGDB source population files remain ignored. Only derived counts, hashes, manifests, discrepancy metadata, and calculation results are eligible for tracked artifacts.

## Scope result

- GOLD: 25 P004 fixtures, all classified `GOLD_C` because the direct Swiss reference path and runtime share pyswisseph; 23 pass and 2 remain unresolved at known Ascendant sign boundaries.
- SILVER: 109 adjudicated A/B ADB records (32 Tier A, 77 Tier B), all 109 calculations complete with no invariant failures.
- STRESS: 7,022 calculation-ready inputs: 6,022 ADB plus 1,000 OGDB; all complete with no invariant failures.
- The one excluded ADB record has a malformed BCE year that the current engine input contract cannot represent. The 13 records with unknown documentary place are excluded from chart-ready counts, consistent with the established evidence policy.
- Boundary suite: PASS. Two pre-existing Ascendant/reference limitations remain open and are not silently repaired.

