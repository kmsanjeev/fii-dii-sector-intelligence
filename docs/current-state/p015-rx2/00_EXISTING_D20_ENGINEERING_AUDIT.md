# P015-RX2 Existing D20 Engineering Audit

Previous runtime: `varga_sign(longitude, 20, "general")` and `KundliEngine._varga_sign(..., 20, "general")`.

The legacy branch used 20 equal divisions, then the generic zero-based odd/even fallback: same source sign for even index, seventh-sign start for odd index. The canonical Varga registry reported method `general`, version `legacy`, and no D20-specific provenance. The Kundli chart builder, canonical Varga facts, and P004 reference calculator were all callers. No D20-specific persisted store or dedicated cache was found; generic chart/cache artifacts are not rewritten.

P015-RX2 reuses the Varga registry, longitude normalization, sign modality sets, chart pipeline and fact schema. Only D20 routing changes. Other Varga semantics remain on their prior methods.
