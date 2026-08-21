# Retrieval metadata

Newly acquired event-calendar records carry UTC `retrieved_at`. Existing
records without this field are loaded with an explicit null value. RX1 never
backfills a timestamp from file modification time.

Corporate responses expose:

- `retrieval_metadata.row_timestamp_field = retrieved_at`;
- `retrieval_metadata.dataset_timestamp_field = dataset_build_at`;
- per-dataset row count, retrieved row count, coverage, build timestamp and
  last successful update;
- limitations distinguishing row retrieval from dataset build time.

Coverage values are `COMPLETE`, `PARTIAL`,
`LEGACY_RETRIEVAL_TIMESTAMP_UNAVAILABLE`, or `UNAVAILABLE`.

Controlled official refresh on 2026-08-21:

| Metric | Result |
|---|---:|
| Query window | 2026-08-14..2026-10-20 |
| Official source rows returned | 330 |
| Existing rows before merge | 35,448 |
| Rows after deterministic deduplication | 35,745 |
| Rows with non-null retrieval timestamp | 319 |
| Legacy rows retaining null timestamp | 35,426 |

The difference between source rows and rows added is deterministic overlap with
existing event keys.
