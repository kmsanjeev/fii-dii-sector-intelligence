# Component Maturity

| Component | Status | Evidence boundary |
|---|---|---|
| Tropical planetary calculation | `EXTERNAL_VALIDATED` | Parent JPL oracle, 504/504, inherited unchanged |
| Lahiri / ayanamsha | `REFERENCE_STANDARD_PARTIALLY_RESOLVED` | Official IMD bounded 2026 check; no full all-body independent oracle |
| Nirayana longitudes | `DETERMINISTIC_REGRESSION_ONLY` | Same-engine decomposition plus IMD bounded ayanamsha |
| Rashi/Nakshatra/Pada classification | `INTERNAL_INVARIANT_VALIDATED` | Explicit boundary corpus and endpoint tests |
| Tropical Ascendant | `INDEPENDENTLY_VALIDATED_WITH_CONDITION` | 120 cases, 120/120 within 0.05° |
| Sidereal Ascendant | `BOUNDARY_POLICY_REQUIRED` | Same-engine sidereal comparison plus independent tropical path |
| Historical timezone | `DETERMINISTIC_REGRESSION_ONLY` | 64 fixed cases, version captured, gap/fold/LMT explicit |
| D20 calculation | `CALCULATION_PARTIALLY_VALIDATED` | Existing P015-RX2 state preserved |
| D20 interpretation | `NOT_VALIDATED` | Remains gated |

Overall calculation maturity remains `CALC-M5_PARTIAL_EXTERNAL_VALIDATION`.
