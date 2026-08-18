# Panchanga Standard

P032 exposes deterministic facts for five limbs at a timezone-aware local
instant:

1. Vara: local civil weekday.
2. Tithi: normalized Moon minus Sun sidereal longitude, 12 degrees per tithi,
   30 half-open segments.
3. Nakshatra: normalized Moon sidereal longitude, 27 equal segments and four
   padas per segment, reusing the P016 boundary convention.
4. Yoga: normalized Sun plus Moon sidereal longitude, 27 equal segments.
5. Karana: normalized Moon minus Sun elongation, 6 degrees per half-tithi,
   with the 60-position sequence and fixed/movable labels.

Boundary policy is deterministic: `[start, end)`, exact boundaries move to the
next segment, and 360 degrees wraps to zero. Input longitudes are converted
through decimal text conversion to avoid introducing an avoidable binary-float
boundary change. This module does not determine auspiciousness.

Solar-day facts continue to use the pre-existing
`MUHURTA_FOUNDATION_SOLAR_DAY_NOAA_APPROX_V1` method, with explicit timezone
conversion and no silent DST assumption. Historical timezone and civil-time
uncertainty remains a caller responsibility and is surfaced as a limitation.
