# Independent Ascendant Validation

The programme corpus contains 120 fixed UTC cases spanning India, Europe, Africa, North/South America, Australia, the Pacific and a high-latitude case, with varied seasons and historical years. Coordinates are explicit WGS84 decimal-degree fixtures and do not depend on the mutable city cache.

The independent path is a GMST plus mean-obliquity Ascendant formula. Swiss `houses()` and `houses_ex()` are comparison surfaces only. All 120 cases pass the documented 0.05° tropical comparison tolerance. The sidereal runtime/reference error is summarized with max and P95 metrics.

The two inherited boundary fixtures and their ±1-second rows remain included. They reproduce the known near-boundary runtime/reference behavior, including the previously observed sign boundary difference. No production output correction is accepted here.

## Decision

`BOUNDARY_POLICY_REQUIRED` with `KEEP_RUNTIME_STANDARD` semantics: retain the current W/whole-sign path, preserve explicit boundary policy, and do not silently migrate to `houses_ex`. A migration would alter Goldset, Silver/Stress, D1, Varga and Dasha downstream surfaces and therefore requires a separate authorized remediation.
