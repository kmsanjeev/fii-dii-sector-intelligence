# Validation

Focused validation covers complete versus incomplete TTM, negative values,
field provenance dates, legacy ROE rejection, financial-sector limitations,
malformed filing-date rejection, stock contract compatibility and cross-layer
pass-through. The focused suite passed `10/10`; Ruff, compilation and a live
FastAPI `/api/stocks/RELIANCE` probe passed. Two canonical evidence builds
produced the same SHA-256 `a7e201063a0fe6f4b4355791c7b4c09308f54cf4a941abd214f75692d4370853`.

The FII-DII full suite passed `1327` tests in `598.98s`; the VEDA platform
suite exited `0` with its existing dependency deprecation warnings.

The production data files were not rebuilt or staged. The live provider probe
returned contract `stock-intelligence-1.1`, nested evidence contract
`fundamental-evidence-1.0`, `HIGH` field coverage and `VERY_STALE` freshness.
The contract is deterministic and has zero new provider calls.
