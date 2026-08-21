# Session and Timestamp Model

Canonical timezone is `Asia/Kolkata`. Session states are `PRE_OPEN`,
`REGULAR_OPEN`, `REGULAR_CLOSED`, `POST_CLOSE`, `HOLIDAY`, `WEEKEND`,
`SPECIAL_SESSION` and `UNKNOWN`. The reusable normal-session boundary is
09:15–15:30 IST; holiday/special-session calendar integration remains a
provider/calendar dependency and is not inferred from a fixed hour alone.

Records distinguish `exchange_event_at`, `bar_start`, `bar_end`,
`source_received_at`, `retrieved_at` and `persisted_at` where available. A
partial bar is `OPEN_PARTIAL`; final source data is `CLOSED`; later source
revision is `CORRECTED`.
