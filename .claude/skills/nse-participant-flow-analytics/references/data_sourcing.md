# Data Sourcing Guidance

Load before writing any fetch function, backfill script, or when `nselib` errors/gaps come up.

## Primary source

`nselib` is the primary NSE data library for this project. Treat it as reliable but incomplete — validate before trusting.

## Known-limitation protocol

If a task hits an `nselib` gap or limitation (missing historical range, missing participant-level breakdown for a segment, rate limiting, schema drift), flag it upfront to Sanjeev rather than silently working around it, and suggest one of:

- Scraping NSE Bhav Copy directly for the missing range.
- `nsepy` as a fallback library for specific data types `nselib` doesn't cover.
- Manual CSV import as a last resort, with the same validation pipeline applied as any fetched data.

## Fetch design rules

- Retry with exponential backoff, max 3 retries, on every `nselib`/network call.
- Backfill in monthly chunks to avoid rate limits; store incrementally by date partition (so a failed run doesn't require restarting from scratch).
- Store raw fetched data before any transformation — this is required, not optional, so reprocessing is possible if downstream logic changes.

## Validation before processing (every fetch)

- Null checks
- Schema checks (must include `exchange`, `segment`, `participant` columns per the project schema rule)
- Stale-date checks (did the fetch actually return the expected trading date?)
- Range sanity checks on values (e.g. net flow figures within plausible bounds for the segment)

Any fetch function that skips this validation step is incomplete — always include it, don't wait to be asked.
