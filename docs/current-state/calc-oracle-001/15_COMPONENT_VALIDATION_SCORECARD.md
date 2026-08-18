# Component validation scorecard

| Component | State | Boundary |
|---|---|---|
| Tropical planetary positions | `EXTERNAL_REFERENCE_VALIDATED` | 504/504 against configured JPL Horizons vectors |
| Runtime ephemeris selection | `INTERNAL_CONFIGURATION_VALIDATED` | explicit MOSEPH, unauthorized backend rejected |
| Lahiri ayanamsha | `INTERNAL_CONFIGURATION_VALIDATED` | no independent sidereal oracle |
| Tropical Ascendant | `INDEPENDENT_IMPLEMENTATION_AGREEMENT` | two frozen cases within 0.01° |
| Sidereal Ascendant | `REFERENCE_REPRODUCED_WITH_CONDITION` | known numerical boundary remains |
| Timezone classification | `INTERNAL_INVARIANT_VALIDATED` | gaps/folds preserved, no false precision |
| D1/D9/D10 | `DETERMINISTIC_REGRESSION_ONLY` | parent Goldset scope |
| D20 calculation | `CALCULATION_PARTIALLY_VALIDATED` | governed P015-RX2 method; no interpretation |
| D20 interpretation | `NOT_VALIDATED` | remains gated |
| Dasha/Transit | `DETERMINISTIC_REGRESSION_ONLY` | no predictive claim |

