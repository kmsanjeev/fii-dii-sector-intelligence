# Period and frequency model

The contract distinguishes `QUARTERLY`, `TTM`, `YOY`,
`ANNUAL_OR_LATEST_AGGREGATE`, and `UNKNOWN`. TTM requires four component
quarters; it never silently annualises a partial set. YOY requires eight valid
comparable periods.

`period_end`, `filing_date` and `retrieved_at` are separate fields. Filing
dates that cannot be parsed remain null with a reason. Retrieval time describes
the local file only and does not make an old reporting period current.
