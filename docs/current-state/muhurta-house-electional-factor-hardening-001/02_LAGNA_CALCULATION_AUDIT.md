# Lagna Calculation Audit

The canonical reusable path is
`engines/intelligence/kundli_engine.py::KundliEngine._ascendant`. It calls
Swiss Ephemeris `houses(..., b'W')`, subtracts the explicitly configured
Lahiri ayanamsha, and returns a sidereal Ascendant longitude. Downstream D1
sign assignment uses the existing canonical Rashi order and whole-sign house
mapping.

Maturity: `COMPLETE_WITH_CONDITION` / `VALIDATED_WITH_CONDITIONS`.

The calculation is reusable, but not an unconditional electional dependency:

- the current W-plus-ayanamsha path is the frozen runtime standard;
- a known near-boundary difference can change the Rashi sign;
- timezone and historical civil-time edge conditions remain explicit;
- no new electional Ascendant calculation was created.

The diagnostic factor is `MUHURTA_LAGNA_SIGN`, with the canonical 12-sign
enum. Hard electional rules must abstain when the boundary status is ambiguous
or when the source predicate itself is unresolved.
