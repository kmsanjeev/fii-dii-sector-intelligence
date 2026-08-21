# Authorized source availability

Source audited: official NSE corporate financial-results API, reached through
the NSE financial-results origin page and the endpoint
`/api/corporates-financial-results`.

Transport result: HTTP 200 with `Accept-Encoding: identity`.

| Query window | Rows | Observation |
|---|---:|---|
| 2026-07-01..2026-08-21 | 4 | delayed/re-filed older periods only |
| 2026-04-01..2026-07-31 | 10 | no representative 2026-06-30 period |
| 2026-01-01..2026-03-31 | 15 | older periods only |
| 2025-01-01..2025-03-31 | 3865 | prior filing season has broad coverage |

The 2026-07-01..2026-08-21 sample included KANANIIND, VSTTILLERS,
IL&FSTRANS and both VSTTILLERS statement variants. The repaired run accepted
source rows for delayed/re-filed periods, but no representative current
quarter was available for RELIANCE, HDFCBANK, ICICIBANK, TCS, INFY or LT.

Classification:

- current representative quarter: `NOT_YET_AVAILABLE_THROUGH_AUTHORIZED_PATH`
- delayed/re-filed older periods: `AVAILABLE_UPSTREAM_MISSING_LOCALLY`, now
  capturable by the repaired path
- yfinance rows: `LEGACY_FALLBACK`, not official NSE evidence

No scraping, mirror, unauthorized dataset, or provider-access bypass was used.
