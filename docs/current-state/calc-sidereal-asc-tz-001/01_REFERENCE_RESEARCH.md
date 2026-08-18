# Independent Reference Research

## Official source inspected

The Indian Astronomical Ephemeris 2026 was downloaded from the official Positional Astronomy Centre, India Meteorological Department route on 2026-08-18. The PDF was inspected locally at pages 4, 387, 389, 391, 393, 395 and 397. Only derived ayanamsha values and provenance metadata are retained in this repository; the publication is not committed.

- Source: Positional Astronomy Centre, IMD, *Indian Astronomical Ephemeris for the Year 2026*.
- Download route: <https://packolkata.imd.gov.in/download/IAE2026.zip>
- Edition PDF SHA-256: `58A16722E98F3E9DD23E8E188C39B577E24135306F20674B52FBBB172DB2E25A`
- Edition preface: reference epoch `J2000.0`; ephemeris argument `Terrestrial Time (TT)`.
- Indian Calendar tables: IST or local mean time of the 82.5°E meridian, as stated in the inspected calendar pages.
- The edition includes Nirayana calendar entries, Nakshatra names and “Ayanamsa on 1st” values.

The IMD overview page describes the annual IAE and currently displays a J2000.5 note, while the inspected 2026 edition preface says J2000.0. This is recorded as a source-version/HTML-to-edition discrepancy, not silently resolved. The edition-level statement governs the bounded 2026 comparison, but full VEDA frame and time-scale equivalence remains only partially resolved.

## Reference conclusion

IMD supplies an independent official bounded check for calendar/Nirayana conventions and ayanamsha values. It does not supply a complete per-body modern Lahiri longitude oracle in the exact VEDA geometric/apparent and epoch configuration. Therefore the result is `REFERENCE_STANDARD_PARTIALLY_RESOLVED`, not full independent sidereal validation.

## Secondary technical standard

Swiss Ephemeris documentation was used only to confirm the meaning and configuration surface of `SIDM_LAHIRI`, `houses_ex` and sidereal flags. It is not treated as an independent oracle against VEDA because VEDA uses the same library family.
