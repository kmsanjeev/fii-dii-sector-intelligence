# VEDA-MARKET-INTRADAY-PROVIDER-ACCESS-VALIDATION-RX1

Decision: `VEDA_MARKET_INTRADAY_PROVIDER_ACCESS_VALIDATION_RX1_OPERATIONAL_WITH_CONDITIONS`

Foundation decision: `VEDA_MARKET_INTRADAY_DATA_FOUNDATION_OPERATIONAL_WITH_CONDITIONS`
with provider access still blocked by the configured Dhan account's inactive
Data API plan. Authentication is operational; market-data entitlement is not.

Scope remained read-only. No orders, strategy, prediction, ML, RAG, EMP,
Jyotish, BEBOS or Intraday Intelligence work was performed.

## Evidence summary

- Dhan TOTP authentication: HTTP 200; token cached in Windows Credential
  Manager; token values were never printed or committed.
- Dhan profile: HTTP 200; authenticated client present; active segments
  reported as `E, D, C, M`; `dataPlan=Deactive`; `dataValidity=NA`.
- Detailed instrument master: HTTP 200, 212,285 rows read in memory only.
- Exact representative identities: RELIANCE `2885`, NIFTY index `13`, NIFTY
  August 2026 future `58072`, expiry `2026-08-25`.
- Historical equity, historical futures/OI, quote and option-chain probes were
  blocked by entitlement. No fallback was used.
- Live stream was not started: the test date was outside market hours and the
  data plan was inactive. State is `LIVE_SESSION_VALIDATION_PENDING`.

See the companion validation files for the bounded evidence and limitations.
