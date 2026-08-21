# Corporate Contract

Contract version: `corporate-intelligence-1.0`

The formal response includes:

`contract_version`, `symbol`, `isin`, `as_of`, `data_status`, `identity`,
`source_summary`, bounded `recent_events`, `events_by_category`,
`results_context`, `evidence_quality`, `facts`, descriptive `interpretation`,
`limitations` and `next_watch_items`.

`results_context` references `fundamental-evidence-1.0` and sets
`metrics_inlined=false`; Corporate does not duplicate financial metrics.
`evidence_quality` is `HIGH`, `MEDIUM` or `INSUFFICIENT` based on source and
identity availability, not outcome probability.

Query parameters are bounded: `days` 1..3650 and `limit` 1..100. Global and
symbol-scoped requests sort/filter source rows before event normalization so a
small response cannot trigger whole-corpus event construction.

The old KPI surface remains available in `legacy_summary`; its status is kept
separately as `legacy_data_status` so it cannot overwrite the authoritative
Corporate freshness contract.
