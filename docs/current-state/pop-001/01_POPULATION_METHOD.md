# VEDA-POP-001 — Population Method

Population ID: `VEDA-POP-OGDB-001`
Version: `1.0.0`
Source: [official OGDB timed data](https://opengauquelin.org/download/ogdb-time.csv.zip)

Records were selected in source order until 1,000 usable charts were obtained.
The selection used only source completeness and calculation eligibility:

`source row → coordinate validation → source local/UTC offset → D1 calculation → P016 timing facts → canonical hash`.

Calculation configuration was frozen as Lahiri, Swiss Ephemeris, existing VEDA
Kundli house method, `OGDB_DATE_UT_DELTA` timezone method and
`P016_CANONICAL_TIMING`.

The compressed artifact is deterministic (`gzip mtime=0`, canonical JSON,
sorted keys). Two independent builds produced the same compressed hash.
