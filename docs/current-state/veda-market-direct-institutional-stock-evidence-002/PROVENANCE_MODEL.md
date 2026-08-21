# Provenance and reproducibility

Each disclosed deal and ownership row now carries a deterministic
`source_id` and `source_record_id`. Derived signals retain the source record
IDs contributing to their bounded window and state that the lineage is only
partially reproducible because the upstream participant labels are heuristic.

Current source IDs:

- `NSE_DISCLOSED_BULK_BLOCK_DEAL_LOCAL_EXTRACT`
- `NSE_SHAREHOLDING_LOCAL_EXTRACT`
- `INSTITUTIONAL_DEAL_SIGNALS_DERIVED`

Reproducibility is `LOCAL_ARCHIVE_DEPENDENT` for the deal extract and
`REPRODUCIBLE_FROM_LOCAL_SNAPSHOT` for ownership comparisons. No retrieval
timestamp is invented when the current local files do not provide one.
