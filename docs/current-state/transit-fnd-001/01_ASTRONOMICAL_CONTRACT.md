# VEDA-TRANSIT-FND-001 — Astronomical Contract

| Field | Contract |
|---|---|
| Method | `VEDA-TRANSIT-FND-001-HISTORICAL-V1` |
| Version | `1.0` |
| Ephemeris | Swiss Ephemeris via existing VEDA runtime |
| Ayanamsha | Lahiri |
| Zodiac | Sidereal |
| Planets | Jupiter, Saturn only |
| Timestamp | UTC, daily at 00:00 UTC |
| Output | Julian day, tropical longitude, ayanamsha, sidereal longitude, sign, speed, retrograde |
| Cache | In-memory deterministic key: timestamp, planet, configuration |

This is a factual position foundation. It does not select natal targets,
apply orbs, infer events, or produce predictive scores.
