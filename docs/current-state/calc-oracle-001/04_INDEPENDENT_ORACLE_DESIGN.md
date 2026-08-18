# Independent oracle design

The fixed oracle contains 72 UTC timestamps spanning 1850–2026, four seasonal points per selected year, and seven bodies: Sun, Moon, Mercury, Venus, Mars, Jupiter, and Saturn. Each body is compared against NASA/JPL Horizons `EPHEM_TYPE=VECTORS`, geocentric Earth center, TDB, ecliptic J2000, `VEC_CORR=NONE`, position-only output. The committed cache contains only derived vectors/longitudes and response hashes; raw provider responses are not committed.

The local side uses explicit `MOSEPH`, J2000, true-position, and no-nutation flags. Results are compared with circular angular error and body-specific tolerances. This validates the tropical planetary-position surface within the stated oracle configuration; it does not validate sidereal ayanamsha, D20 interpretation, or prediction.

Official references:

- [NASA/JPL Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
- [NASA/JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [Swiss Ephemeris programmer documentation](https://www.astro.com/ftp/swisseph/doc/swephprg.2.10.pdf)

