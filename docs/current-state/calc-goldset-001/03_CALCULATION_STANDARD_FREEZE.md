# Calculation Standard Freeze

Machine-readable copy: `artifacts/03_CALCULATION_STANDARD_FREEZE.json`.

- Standard: `VEDA-CALC-STANDARD-001`, version `1.0.0`, snapshot `2026-08-18`.
- Sidereal: Lahiri/Chitrapaksha through pyswisseph.
- Ephemeris: pyswisseph; the installed local run observes MOSEPH because an explicit Swiss ephemeris path/files are not pinned.
- Coordinates: geocentric planetary positions; geographic latitude/longitude for Ascendant.
- Houses: current `W` Ascendant path, with whole-sign downstream house assignment.
- Nodes: TRUE_NODE; Ketu is the 180-degree opposite of Rahu.
- Time: UTC Julian Day; REST/personal callers use fixed numeric offsets, while ADB uses its source `jd_ut`-derived local offset.
- Divisions: current KundliEngine/P015 methods; D20 uses the versioned P015-RX2 category-start method and remains calculation-partially-validated.
- Dasha: existing Vimshottari implementation with Moon nakshatra and 120-year proportions.
- Transits: existing KundliEngine historical/current surface, calculation-only in this activity.
- Rounding: raw floats for comparisons; canonical JSON for artifacts; runtime durations are excluded from canonical hashes.
- Predictive policy: `PRED-M3_OPERATIONAL_PLUS` unchanged; PRED-M4 unchanged.

This freeze is a benchmark standard, not a claim that every component has an external authoritative oracle.

