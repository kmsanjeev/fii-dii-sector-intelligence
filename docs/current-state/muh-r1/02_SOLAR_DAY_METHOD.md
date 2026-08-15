# Solar-Day Method

Method ID: `MUHURTA_FOUNDATION_SOLAR_DAY_NOAA_APPROX_V1`

Version: `1.0`

The implementation uses a deterministic low-precision solar-event calculation
with latitude, longitude, civil date and IANA timezone. It returns timezone-aware
local sunrise/sunset values or explicit `NO_SUNRISE_FOR_DATE` /
`NO_SUNSET_FOR_DATE` states. It does not claim that this engineering algorithm
is a classical Muhurta rule.

Known conditions: approximate solar events, timezone database dependency,
location/date sensitivity and no event-specific electional interpretation.
