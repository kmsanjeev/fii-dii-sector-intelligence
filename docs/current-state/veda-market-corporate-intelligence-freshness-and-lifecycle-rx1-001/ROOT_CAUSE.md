# Root-cause and gap analysis

## Confirmed cause

The daily refresh orchestration already contains stage `7B_event_calendar`
and maps it to `engines.corporate.corporate_event_calendar_engine`. The
previous engine called `nselib.capital_market.event_calendar_for_equity`.
The official response advertised Brotli content encoding, while the installed
transport failed to decode it:

`ContentDecodingError: Received response with content-encoding: br, but failed to decode it.`

The engine caught the exception after retries and returned an empty list. The
old module entry point called `engine.run()` but discarded its boolean result,
so the stage could appear successful while the old valid CSV remained unchanged.

## Data evidence before RX1

| Item | Observation |
|---|---|
| Local event calendar | 35,448 rows, mtime 2026-08-03, latest event date 2026-08-18 |
| Direct official endpoint | HTTP 200, 1,651 rows for an audited 2026-08-04..2026-08-21 window |
| Scheduler stage | Present as 7B; not the root cause |
| Old transport | nselib Brotli decode failure |
| Failure visibility | Empty result and ignored return value |

## Secondary data-quality gap

Quarterly results contain many legacy filing dates such as `10-Nov-202`.
Pandas can interpret those as year 0202 unless the year is validated. RX1
rejects those values, uses valid `date_end` as the freshness basis when filing
coverage is insufficient, and exposes filing coverage as `PARTIAL`.

## Preserved behavior

An acquisition failure does not destroy or replace the last valid dataset.
The refresh-state record reports `SOURCE_REFRESH_FAILED`, retains the previous
successful timestamp, and the module exits non-zero so orchestration can mark
the optional stage degraded while continuing other work.
