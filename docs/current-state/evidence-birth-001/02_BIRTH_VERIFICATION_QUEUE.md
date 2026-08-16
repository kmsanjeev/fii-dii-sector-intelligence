# Birth Verification Queue

The 13 exact-day subjects are retained in `02_VERIFICATION_QUEUE.json` with
birth date, time, raw precision, source URLs, upstream cluster, event frame,
verification state and human-review flag. All are `PENDING_REVIEW`; none is
upgraded. Conflicting times would be retained as variants, never resolved by
chart fit.
