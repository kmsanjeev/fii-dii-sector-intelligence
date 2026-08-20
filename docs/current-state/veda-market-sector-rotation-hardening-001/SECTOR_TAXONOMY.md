# Canonical sector taxonomy

The authoritative stock-to-sector mapping is
`data/reference/company_classification_v4.csv` (`SYMBOL`, `SECTOR`). The
current audit found 2,123 unique symbols, no duplicate symbol rows and 27
non-empty platform sectors. `OTHER` is an existing canonical bucket, not a
new inferred sector.

NSE index names are mapped centrally in the Phase 6C engine only for legacy
index traceability. An index alias is not silently treated as a new platform
sector. Unknown or unmapped index names remain without an index alias.

Sector and theme remain distinct:

- sector: the canonical one-sector stock classification used for aggregation;
- theme: a separate multi-theme classification and future hardening lane.

This programme does not merge sector and theme semantics and does not create
new theme identities.
