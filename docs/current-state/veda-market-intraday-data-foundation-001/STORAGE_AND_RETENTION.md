# Storage and Retention

The foundation uses a partitioned Parquet store at ignored local
`data/intraday/candles/date=YYYY-MM-DD/interval=N/`. The canonical key is
provider security identity + interval + bar start. Writes are atomic and
deduplicated; prior valid data survives acquisition failure. No raw provider
tick retention is required, and no broad backfill was launched.

Representative storage/API-call sizing is pending verified provider access.
The initial policy is bounded representative symbols and intervals only; no
full-market 1-minute five-year backfill is authorized.
