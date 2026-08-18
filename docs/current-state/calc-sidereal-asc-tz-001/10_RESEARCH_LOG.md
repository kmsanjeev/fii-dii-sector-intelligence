# Research Log

| Date | Query/source | Accessed evidence | Result |
|---|---|---|---|
| 2026-08-18 | IMD Indian Astronomical Ephemeris landing page | Official PAC/IMD publication description | Authority confirmed; page-level epoch note conflicts with edition PDF |
| 2026-08-18 | PAC official IAE 2026 download | PDF pages 4, 387, 389, 391, 393, 395, 397 | J2000.0, TT, IST/calendar convention, Nirayana headings and six ayanamsha values recorded |
| 2026-08-18 | Swiss Ephemeris documentation | Sidereal mode/house API configuration | Technical configuration confirmed; not independent of VEDA runtime |
| 2026-08-18 | Repository implementation audit | `kundli_engine.py`, `jyotisha_runtime.py`, astronomy policy, Oracle artifacts | Current Lahiri/MOSEPH/Ascendant paths reconstructed; no production patch warranted |
| 2026-08-18 | Canonical OpenAPI generator | `scripts/generate_p001_api_baseline.py` | Stale snapshot conclusively regenerated to live 140/153 contract |
| 2026-08-18 | Full-suite P013 export validation | `astrology_capability_framework.export_phase_bundle` and `validate_exported_bundle` | Regenerated the conclusively stale canonical P013 export; 30 files written and validation passed; no production activation changed |
| 2026-08-18 | Full-suite P005 export validation | `astrology_interpretation_validation.export_phase_bundle` and `validate_exported_bundle` | Rebuilt ignored local P005 validation artifacts after hash-seed stability check; validation passed and no production interpretation logic changed |
| 2026-08-18 | Full repository regression | `py -3.11 -m pytest -q` | 956 passed, 1 warning, exit code 0 in 732.68 seconds; earlier 900-second timeout retained as historical evidence, not a pass |

Rejected as authority: generic web astrology pages, unverified Lahiri tables, same-engine “independent” claims, and any source lacking frame/time-scale/rounding metadata.
