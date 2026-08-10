# VEDA-P004 Executive Summary

Date baseline: `2026-08-10`

VEDA-P004 validated the current deterministic kundli foundation without altering production astrology behavior. The strongest confirmed assets are Lahiri sidereal configuration, deterministic planetary longitude calculation, whole-sign downstream house assignment, exact Rahu/Ketu handling through `TRUE_NODE`, and reproducible Nakshatra/Pada mapping across sampled fixtures.

The validation did not end in a clean PASS. The main conditions are foundational rather than cosmetic:

- the active local runtime resolves to `SEFLG_MOSEPH` because the code does not explicitly pin an ephemeris path or `FLG_SWIEPH`;
- non-India stock exchange paths use hardcoded offsets and materially drift under DST;
- historical country-chart civil-time provenance remains weak outside the sampled post-standard cases;
- the current sidereal Ascendant derivation stays numerically close to `houses_ex(..., FLG_SIDEREAL)` but flips sign on a boundary fixture.

Core counts:

- Reference fixtures: `25`
- Validation records: `650`
- Divergences classified: `11`
- Calculation issues registered: `5`

Representative fixture sample:

| Fixture ID | Label | Timezone | Offset | Lagna |
| --- | --- | --- | ---: | --- |
| `VEDA-FIX-CALC-000001` | `mumbai_1984_baseline` | `Asia/Kolkata` | `5.5` | `Libra` |
| `VEDA-FIX-CALC-000002` | `london_2001_baseline` | `Europe/London` | `1.0` | `Gemini` |
| `VEDA-FIX-CALC-000003` | `sydney_1990_baseline` | `Australia/Sydney` | `11.0` | `Gemini` |
| `VEDA-FIX-CALC-000004` | `newyork_1975_baseline` | `America/New_York` | `-4.0` | `Taurus` |
| `VEDA-FIX-CALC-000005` | `newyork_1975_lagna_boundary` | `America/New_York` | `-4.0` | `Virgo` |
| `VEDA-FIX-CALC-000006` | `sydney_1990_lagna_boundary` | `Australia/Sydney` | `11.0` | `Leo` |
| `VEDA-FIX-CALC-000007` | `newyork_1975_nakshatra_boundary` | `America/New_York` | `-4.0` | `Taurus` |
| `VEDA-FIX-CALC-000008` | `kathmandu_1988_nakshatra_boundary` | `Asia/Kathmandu` | `5.75` | `Aries` |
| `VEDA-FIX-CALC-000009` | `santiago_2012_nakshatra_boundary` | `America/Santiago` | `-3.0` | `Libra` |
| `VEDA-FIX-CALC-000010` | `auckland_1999_nakshatra_boundary` | `Pacific/Auckland` | `12.0` | `Sagittarius` |
| `VEDA-FIX-CALC-000011` | `delhi_1947_midnight` | `Asia/Kolkata` | `5.5` | `Taurus` |
| `VEDA-FIX-CALC-000012` | `karachi_1947_offset_check` | `Asia/Karachi` | `5.5` | `Virgo` |
