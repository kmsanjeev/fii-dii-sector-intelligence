# Provider and Entitlement Decision

Primary source decision: `DHAN_PRIMARY` for historical candles, live quotes/
feed, and option-chain requests, subject to account verification.

The installed official `dhanhq==2.2.0` package exposes
`intraday_minute_data`, `quote_data`, `option_chain` and `MarketFeed`. RX1
validated Dhan TOTP authentication and the profile endpoint. The profile
reported `dataPlan=Deactive` and `dataValidity=NA`; historical requests
returned `DH-902` and all governed market-data probes were blocked. Therefore:

- source authority: `OFFICIAL_DHAN_API`;
- authorization: `AUTHENTICATED`;
- entitlement: `ENTITLEMENT_REQUIRED`;
- live/historical/options runtime: `ENTITLEMENT_BLOCKED`;
- final foundation decision: `OPERATIONAL_WITH_CONDITIONS` pending active
  Data API entitlement and representative data validation.

Official references:

- https://dhanhq.co/docs/v2/historical-data/
- https://dhanhq.co/docs/v2/market-quote/
- https://dhanhq.co/docs/v2/live-market-feed/
- https://dhanhq.co/docs/v2/option-chain/
- https://dhanhq.co/docs/v2/instruments/
