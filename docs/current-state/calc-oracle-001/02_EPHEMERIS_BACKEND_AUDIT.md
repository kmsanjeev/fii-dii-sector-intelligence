# Ephemeris backend audit

The runtime uses `pyswisseph==2.10.3.2` (Swiss runtime `2.10.03`). No Swiss ephemeris file path is configured. A direct probe showed that the local calculation resolves to Moshier (`MOSEPH`), not an installed Swiss-file backend.

`engines/common/astronomy_policy.py` now defines `VEDA-ASTRONOMY-BACKEND-001` and makes the selected backend explicit. Production `calc_ut` callers use the helper, which adds `FLG_MOSEPH` and rejects an unauthorized returned backend. This is an explicit deterministic runtime choice, not a claim that Moshier and Swiss-file results are universally identical.

The independent oracle uses NASA/JPL Horizons geometric vectors for tropical planetary-position comparison only. It is not a sidereal/Lahiri oracle and is not a D20 or predictive oracle.

