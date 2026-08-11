# VEDA-P008 Run Explorer

Date: `2026-08-11`

Run Explorer is backed by:

- `GET /api/research/runs`
- `GET /api/research/runs/{run_id}`

## Delivered Views

- run list with status, provider, counts, and duration
- per-run timeline from ledger events
- per-run source observation summaries
- evidence and candidate linkage via run detail payload

## Read Models

Implemented in [engines/ai/research/platform/service.py](/D:/Projects/fii-dii-sector-intelligence/engines/ai/research/platform/service.py):

- `list_run_rows()`
- `get_run_detail()`

## Traceability

The run detail surface exposes the same persisted artifacts used by research execution. No separate UI-only logging system was introduced.

