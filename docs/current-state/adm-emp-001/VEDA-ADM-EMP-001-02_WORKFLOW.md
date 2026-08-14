# Intake Workflow and Governance

The workflow is:

`UPLOAD -> PARSE -> MAP -> PREVIEW -> VALIDATE -> DUPLICATE CHECK -> REVIEW -> INGEST`

CSV uses one row per event. XLSX reads values only from the selected/first
sheet and does not execute formulas or macros. The service records import
fingerprints, row-level validation, mapping, summary counts, ingestion state,
and audit events in the shared research database.

Validation distinguishes errors from warnings. It checks governed event types,
birth/event dates, provenance, cutoff completeness for historical cases,
leakage risk, duplicate/case-family identity, and empirical eligibility.
`REFERENCE_NOT_VERIFIED`, uncertain birth time, research-only cases, duplicate
cases, and leakage-invalid cases are retained as explicit states rather than
silently upgraded or counted as empirical evidence.

Templates are available through Admin-only endpoints:

- `/api/empirical/templates/csv`
- `/api/empirical/templates/xlsx`

No automatic prediction, empirical pattern, Approved Core promotion, or
outcome inference occurs during import.
