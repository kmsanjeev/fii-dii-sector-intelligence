# Time, Location and Sunrise Audit

The natal runtime has local birth datetime and chart location context, but the
Panchanga helper receives a birth datetime and two longitudes rather than an
electional date/location request. It therefore cannot yet guarantee:

- local sunrise/sunset;
- civil-day and sunrise-day conventions;
- high-latitude or polar edge handling;
- DST/timezone historical resolution for an election date;
- solar-day subdivisions used by regional time-window conventions;
- reproducible location-specific electional windows.

Readiness: `MISSING_FOUNDATION` for electional use. This is an engineering and
calculation dependency, not a claim that a particular modern convention is
classical.
