# VEDA-P004 Validation Matrix

| Capability | Status | Notes |
| --- | --- | --- |
| TIME_NORMALIZATION | `VALIDATED_WITH_CONDITIONS` | Human paths are correct only when callers supply the historically correct offset; stock and country paths contain hardcoded-offset defects. |
| JULIAN_DAY | `VALIDATED` | Sampled REST Julian Day values matched direct swisseph julday() references. |
| SWISS_EPHEMERIS_INTEGRATION | `VALIDATED_WITH_CONDITIONS` | Runtime is swisseph-based, but the active local ephemeris mode is MOSEPH via implicit fallback rather than an explicit SWIEPH pin. |
| SIDEREAL_MODE_AND_AYANAMSHA | `VALIDATED` | Lahiri sidereal mode is set in runtime code and sampled ayanamsha values matched direct references. |
| GRAHA_POSITIONS | `VALIDATED` | Sampled Sun through Ketu longitudes matched independent direct swisseph calculations within tight tolerance. |
| RAHU_KETU_POLICY | `VALIDATED` | All sampled runtime paths use TRUE_NODE for Rahu and Ketu = Rahu + 180 degrees. |
| RETROGRADE_STATE | `VALIDATED` | Sampled retrograde flags matched direct speed-sign references; nodes are hardcoded retrograde by convention. |
| LAGNA | `VALIDATED_WITH_CONDITIONS` | Runtime Ascendant matches a sidereal-house reference closely on most charts but flips sign on a boundary fixture. |
| RASHI_AND_WHOLE_SIGN_HOUSES | `VALIDATED` | Planet sign placement and whole-sign house mapping matched the current runtime formula. |
| NAKSHATRA_AND_PADA | `VALIDATED` | Sampled Moon Nakshatra and Pada values matched exact 360/27 and 360/108 partitions; one naming divergence is format-only. |
| CURRENT_VARGAS | `VALIDATED_WITH_CONDITIONS` | Sampled active varga formulas reproduced current output, but formula provenance remains unresolved for the broader D11/D16/D20/D30/D60 set. |
| VIMSHOTTARI_FOUNDATIONS | `VALIDATED_WITH_CONDITIONS` | Birth lord and sequence are deterministic; personal and REST paths preserve different output surfaces and date arithmetic models. |
| CROSS_ENGINE_DIVERGENCES | `VALIDATED` | 3 material timezone divergences and multiple surface-level personal/REST differences are now explicitly classified. |
