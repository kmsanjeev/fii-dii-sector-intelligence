# VEDA-P004 Ephemeris & Ayanamsha Validation

Current runtime configuration observed on `2026-08-10`:

- Python package: `pyswisseph 20230604`
- Library version: `2.10.03`
- Requested runtime flags: `FLG_SIDEREAL, FLG_SPEED`
- Active local ephemeris mode: `MOSEPH`
- Sidereal mode: `SIDM_LAHIRI`
- Node method: `TRUE_NODE`
- House method code: `W`

Validation outcome:

- Sampled ayanamsha values matched direct Lahiri references.
- The code never sets `FLG_SWIEPH` explicitly and never calls `set_ephe_path()`.
- No ephemeris files were detected inside the repository workspace, and local runtime flags resolve to `MOSEPH`.

Condition:

- The platform is `swisseph`-backed, but the local environment is not pinned to Swiss ephemeris files in an explicit, reviewable way.
