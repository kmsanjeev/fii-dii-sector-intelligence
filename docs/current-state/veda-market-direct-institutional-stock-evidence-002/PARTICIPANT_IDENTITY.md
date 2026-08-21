# Participant identity

Raw client names are preserved. The normalized name is deterministic and is
not treated as an independent source. Current local disclosed-deal records
contain 2,533 unique client names.

Known local labels (`FII`, `MF`, `INSURANCE`, `PROMOTER`) are explicitly marked
`DERIVED_HEURISTIC` with method `HEURISTIC` and confidence `CONDITIONAL`.
Unknown/fallback labels remain `UNKNOWN` with low confidence. No local field
is promoted to source-reported FII or DII unless the source itself provides
that classification.

The contract retains both legacy `authority`/`confidence` aliases and the
explicit `classification_method`, `classification_status`,
`classification_source` and `classification_confidence` fields. This keeps
downstream compatibility while making heuristics auditable.
