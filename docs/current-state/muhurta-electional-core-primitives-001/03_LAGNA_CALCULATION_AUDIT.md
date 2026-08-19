# Lagna Calculation Audit

{
  "factor_id": "MUHURTA_LAGNA_SIGN",
  "calculation_location": "engines/intelligence/kundli_engine.py::KundliEngine._ascendant",
  "algorithm": [
    "Swiss Ephemeris swe.houses(jd, latitude, longitude, b'W')",
    "read tropical ascmc[0]",
    "subtract swe.get_ayanamsa_ut(jd) with SIDM_LAHIRI",
    "normalize to [0,360)",
    "map floor(longitude/30) to canonical RASHIS",
    "derive downstream whole-sign houses from Lagna sign index"
  ],
  "ayanamsha": "SIDM_LAHIRI via Swiss Ephemeris get_ayanamsa_ut",
  "coordinates": "explicit decimal latitude/longitude; no city lookup in factor contract",
  "timezone": "aware input normalized to UTC before Julian-day calculation by existing callers",
  "mapping": "0 inclusive, 360 exclusive; canonical Kundli SIGNS/RASHIS order",
  "validation": {
    "12_sign_mapping": "INTERNAL_INVARIANT_VALIDATED",
    "tropical_formula": "INDEPENDENT_DIAGNOSTIC_VALIDATED_IN_PARENT_ASC_TZ_ACTIVITY",
    "sidereal_oracle": "SAME_ENGINE_REFERENCE_LIMITATION",
    "near_boundary": "KNOWN_W_PLUS_LAHIRI_HOUSES_EX_DIFFERENCE"
  },
  "production_policy": "reuse canonical path; no new Ascendant engine; abstain when sign boundary is ambiguous"
}
