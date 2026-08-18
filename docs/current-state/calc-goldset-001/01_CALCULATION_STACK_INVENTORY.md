# Calculation Stack Inventory

| Surface | Reused component | Validation state | Boundary |
|---|---|---|---|
| Input normalization | Goldset parser plus existing case contracts | `INTERNAL_INVARIANT_VALIDATED` | Raw ADB/OGDB remains local and ignored |
| Planetary positions | `engines/intelligence/kundli_engine.py` / pyswisseph | `DETERMINISTIC_REGRESSION_ONLY` | No independent astronomical oracle in this phase |
| Sidereal mode | Lahiri / Chitrapaksha | `DETERMINISTIC_REGRESSION_ONLY` | Explicit in standard freeze |
| Ascendant | Current `houses()` plus Lahiri adjustment | `UNVALIDATED` | P004 records a houses()/houses_ex boundary sign discrepancy |
| Nakshatra/pada | Existing engine method | `INTERNAL_INVARIANT_VALIDATED` | Boundary set exercised |
| D1 | Existing chart payload | `DETERMINISTIC_REGRESSION_ONLY` | No predictive interpretation |
| D9/D10 | P015 methods plus independent agreement in gold fixtures | `INDEPENDENT_IMPLEMENTATION_AGREEMENT` | Not an external oracle |
| D20 | P015-RX2 BPHS category-start routing | `DETERMINISTIC_REGRESSION_ONLY` | Calculation remains partially validated; interpretation gated |
| Dasha/Antardasha | Existing Vimshottari implementation | `INTERNAL_INVARIANT_VALIDATED` | Dates are checked for ordered, non-overlapping intervals |
| Transit | Existing KundliEngine surface | `DETERMINISTIC_REGRESSION_ONLY` | No predictive timing validation |
| Ashtakavarga | Existing surface not independently benchmarked here | `UNVALIDATED` | Deferred |
| Yoga/rule payload | Existing rule engine | `DETERMINISTIC_REGRESSION_ONLY` | Output ordering was made hash-seed stable |

The only production calculation correction made in this phase is deterministic ordering of set-derived yoga combinations. The personal-path golden test now supplies an explicit snapshot date for a time-dependent Dasha assertion; normal runtime remains current-date driven.

