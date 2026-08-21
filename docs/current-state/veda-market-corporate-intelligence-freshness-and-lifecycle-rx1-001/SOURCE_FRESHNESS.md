# Source and freshness contract

The existing `corporate-intelligence-1.0` contract remains unchanged. RX1 adds
optional metadata; consumers must tolerate its absence for legacy providers.

## Dataset semantics

| Dataset | Source date | Build timestamp | Row retrieval | Current audited state |
|---|---|---|---|---|
| announcements | disclosure `date` | file mtime | legacy unavailable | 402,844 rows; latest 2026-08-20; EOD |
| event_calendar | scheduled `event_date` | file mtime | `retrieved_at` | 35,745 rows; latest 2026-08-31; partial row coverage |
| corp_actions | effective `ex_date_dt` | file mtime | legacy unavailable | 40,954 rows; scheduled-date freshness is separate |
| quarterly_results | valid `date_end` fallback | file mtime | legacy unavailable | 32,403 rows; latest period end 2026-03-31; stale |

`event_date`, announcement date, effective date, record date, completion date,
period end, filing date, retrieval time and dataset build time are separate
fields. A scheduled date does not imply completion. A source refresh timestamp
does not imply publication time.

## Quarterly-results qualification

The loader rejects invalid years outside 1900..2100. When more than half of
quarterly `filing_date` values are invalid and `date_end` is available, the
metadata uses `date_end` as the freshness basis and records the limitation.
The Corporate result linkage separately reports `filing_date_coverage` and
`fundamental_freshness_basis`.

## Failure state

`data/intelligence/corporate_event_calendar_refresh.json` is generated runtime
state and is not a committed dataset. It records query windows, source rows,
rows added, prior successful update, errors and `SUCCESS` or
`SOURCE_REFRESH_FAILED`.
