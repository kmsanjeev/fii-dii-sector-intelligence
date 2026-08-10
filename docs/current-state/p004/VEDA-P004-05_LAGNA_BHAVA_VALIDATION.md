# VEDA-P004 Lagna & Bhava Validation

House method observed in runtime:

- Ascendant is derived from Swiss house calculations using house system `W`.
- Downstream planetary house assignment is whole-sign from the Lagna sign index.
- Full Bhava cusp outputs are not surfaced by the runtime.

Validation outcome:

- Whole-sign house assignment itself reproduced exactly from the current runtime formula.
- The runtime Ascendant stays very close to `houses_ex(..., FLG_SIDEREAL)` on sampled charts.
- A boundary fixture (`newyork_1975_lagna_boundary`) flips sign between the two sidereal Ascendant derivations and is therefore registered as a condition-bearing discrepancy.
