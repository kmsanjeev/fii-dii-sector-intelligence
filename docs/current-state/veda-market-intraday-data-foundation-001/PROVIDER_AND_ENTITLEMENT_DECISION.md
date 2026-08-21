# Provider and Entitlement Decision

Primary source decision: `DHAN_PRIMARY` for historical candles, live quotes/
feed, and option-chain requests, subject to account verification.

The installed official `dhanhq==2.2.0` package exposes
`intraday_minute_data`, `quote_data`, `option_chain` and `MarketFeed`. The
current checkout has `DHAN_CLIENT_ID` metadata in the shell but no
`DHAN_ACCESS_TOKEN`, and `data/portfolio/broker_auth.json` is absent. No API
call was made with incomplete credentials. Therefore:

- source authority: `OFFICIAL_DHAN_API`;
- authorization: `CREDENTIALS_UNAVAILABLE`;
- entitlement: `UNVERIFIED` / `REQUIRES_PROVIDER_VALIDATION`;
- live/historical/options runtime: not activated;
- final foundation decision: `BLOCKED` pending access verification.

Official references:

- https://dhanhq.co/docs/v2/historical-data/
- https://dhanhq.co/docs/v2/market-quote/
- https://dhanhq.co/docs/v2/live-market-feed/
- https://dhanhq.co/docs/v2/option-chain/
- https://dhanhq.co/docs/v2/instruments/
