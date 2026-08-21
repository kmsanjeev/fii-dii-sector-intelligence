# Acquisition and refresh behavior

`engines.corporate.corporate_event_calendar_engine` now reuses
`engines.common.nse_client.create_session` and calls the official
`https://www.nseindia.com/api/event-calendar` endpoint with bounded date
windows. The shared client uses identity content encoding, avoiding the prior
nselib Brotli decoding failure.

The engine retains the existing seven-day catch-up and sixty-day forward
window. It writes CSV outputs atomically and keeps the previous valid calendar
when all source chunks fail. It writes refresh diagnostics atomically and
returns false on any exhausted source chunk. The module entry point maps that
false result to exit code 1.

The daily scheduler still includes the 7B stage. RX1 does not redesign the
scheduler or make event-calendar retrieval a critical dependency for unrelated
stages.

Idempotency remains deterministic on `(event_date, symbol, purpose_type)`.
Repeated successful refreshes may update the retrieval timestamp of rows
returned by the source, but do not duplicate event keys.
