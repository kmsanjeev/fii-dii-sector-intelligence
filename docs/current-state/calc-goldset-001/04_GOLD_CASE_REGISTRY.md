# GOLD Case Registry

The registry is machine-readable at `artifacts/04_GOLD_CASE_REGISTRY.json`. It contains the 25 existing P004 fixture cases, their input hashes, compact expected values and reference metadata.

All cases are `GOLD_C`. No case is `GOLD_A` or `GOLD_B`: the reference and runtime both use pyswisseph. The registry therefore records reproducible diagnostic agreement only. Planetary longitude, D9, D10, D20 and Dasha checks pass for the reproducible cases. Two cases remain unresolved because the known Ascendant sign boundary differs between the runtime `houses()` path and P004's sidereal `houses_ex` diagnostic path.

No life-event outcome, predictive label, user identity or raw ADB/OGDB record is included.

