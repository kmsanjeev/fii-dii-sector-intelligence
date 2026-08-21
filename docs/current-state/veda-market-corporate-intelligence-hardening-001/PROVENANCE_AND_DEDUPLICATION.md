# Provenance and Deduplication

Each event receives a deterministic `CORP-` identifier from source ID and
stable source fields (symbol, date, category, reference and source text). The
event retains source ID, authority, source record/reference URL where present,
classification method and limitations.

Deduplication is by deterministic event ID within a response. Repeated copies
of the same source record are not treated as independent evidence. The
provider's canonical identity resolver is consulted; unresolved symbols return
`IDENTITY_REVIEW_REQUIRED` and no fuzzy substitute is used.

`retrieved_at` is currently null at row level because the existing CSV contract
does not carry row retrieval timestamps. Dataset-level update/freshness remains
available through `data_status` and `source_summary`; adding row-level retrieval
metadata is a P1 follow-up, not silently invented here.
