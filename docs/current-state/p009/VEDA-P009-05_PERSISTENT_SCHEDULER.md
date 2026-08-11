# Persistent Scheduler

P009 activates the P006 schedule contract through persisted due-time evaluation.

Supported cadence types:
- `HOURLY`
- `DAILY`
- `WEEKLY`
- `CUSTOM`
- `MANUAL_ONLY`

Schedule behaviour:
- due schedules are read from SQLite;
- schedules advance their `next_run_at` after execution or governed skip;
- overlap is prevented by a persisted worker lease rather than an in-memory flag alone.

The default operational timezone is configurable and defaults to `Asia/Kolkata`.
