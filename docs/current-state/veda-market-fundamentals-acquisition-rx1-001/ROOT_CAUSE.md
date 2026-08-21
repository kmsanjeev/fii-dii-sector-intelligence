# Root-cause register

## Confirmed defects

1. Routine `--windows N` used a frozen `FILING_WINDOWS` list ending at
   Q3FY25 instead of deriving the current completed filing seasons.
2. `run()` built a global `done_labels` set. One stored row for a window label
   suppressed the entire label, so missing issuers were not retried.
3. The installed `nselib` request path negotiated Brotli and failed in the
   local requests stack with `ContentDecodingError`. The official NSE endpoint
   itself returned HTTP 200 when the request explicitly used
   `Accept-Encoding: identity`.
4. Filing dates were truncated with `[:10]`, turning values such as
   `29-Mar-2025` into `29-Mar-202`, weakening freshness and provenance.
5. Deduplication used only issuer, period and source. It could collapse
   standalone/consolidated statements and distinct filing versions.
6. The engine always rewrote the normalized CSV after a non-empty fetch,
   even when the logical result was unchanged.

## Not root causes

- The official NSE source did not return a representative current Q1 FY27
  filing through the audited endpoint on 2026-08-21. This is source
  availability, not evidence that the repaired transport fabricated or lost a
  current quarter.
- The daily refresh stage list does not contain quarterly financial results;
  its existing manual/backfill route is the declared acquisition boundary.

## Remediation boundary

The implementation repairs only the acquisition transport, window selection,
normalization, deduplication and idempotency defects. It does not redesign the
daily scheduler, extended-financials historical model, or downstream
valuation semantics.
