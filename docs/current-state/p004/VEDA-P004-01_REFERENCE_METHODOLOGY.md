# VEDA-P004 Reference Methodology

Reference hierarchy used in this phase:

1. Direct `swisseph` calculations with explicit sidereal Lahiri settings.
2. `zoneinfo`-based UTC normalization for timezone and DST validation.
3. Independent mathematical reproductions for Nakshatra, Pada, whole-sign houses, active Vargas, and Vimshottari sequence logic.
4. Runtime path comparison under a frozen evaluation date of `2026-08-10`.

Important methodological notes:

- Planetary references were calculated through direct `swisseph.calc_ut()` calls.
- Current runtime behavior was frozen to `2026-08-10T00:00:00Z` for dasha validation.
- The Lagna reference uses `houses_ex(..., FLG_SIDEREAL)` while the runtime currently uses `houses(..., b'W')` plus ayanamsha subtraction.
- Varga formulas were reproduced independently from the observed runtime algorithms; this validates implementation consistency, not classical source provenance.
