# Acquisition flow

```text
recent completed filing windows
        |
official NSE master request (identity encoding, bounded retry)
        |
XBRL fetch and normalized filing/statement records
        |
existing local rows + new rows
        |
canonical deduplication and stable ordering
        |
no-op signature check or atomic CSV replacement
```

Routine mode derives the newest completed filing windows from the current UTC
date. Backfill mode retains the existing all-window behavior. A window label is
never treated as proof that all issuers are complete.

Existing downstream consumers remain unchanged: extended financials,
valuation compatibility, `fundamental-evidence-1.0`, stock intelligence and
cross-layer intelligence continue to consume the provider-local outputs.

Quarterly results are not in `engines/orchestration/daily_refresh.py`'s
`STAGES`; the existing `backend/routers/data_ops.py` manual operation remains
the controlled invocation point. No new scheduler or overlapping job was
created.
