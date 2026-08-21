# Source and policy research

Research was limited to official provider and exchange material plus package
metadata. No provider data was downloaded or committed.

| Source | Evidence used | Governance result |
|---|---|---|
| [Dhan authentication](https://dhanhq.co/docs/v2/authentication/) | access token and API-key/OAuth alternatives; Data API charges/eligibility | Dhan auth is provider-specific; entitlement is explicit |
| [Kite Connect overview](https://kite.trade/docs/connect/v3/) | API key/secret, redirect login, server-side secret boundary | Zerodha is a separate auth/connection variant |
| [Kite historical](https://kite.trade/docs/connect/v3/historical/) | instrument token and interval-specific historical candles | capability metadata only; no adapter activated |
| [Kite portfolio](https://kite.trade/docs/connect/v3/portfolio/) | holdings/positions are separate read surfaces | portfolio capability is not conflated with market feed |
| [Kite WebSocket](https://kite.trade/docs/connect/v3/websocket/) | live stream, quote/depth modes and limits | live stream is capability/entitlement gated |
| [HDFC Sky developer portal](https://developer.hdfcsky.com/) | Open API exists; product scope remains portal-controlled | `POLICY_REVIEW_REQUIRED`, no implementation claim |
| [NSE data usage policy](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE_DataUsageandSharingPolicy.pdf) | use/sharing/redistribution terms | market-data licensing is not inferred from package availability |

Community package pages and repeated blog claims were not treated as
authority. yfinance is retained only as a legacy/public compatibility class;
nselib and nsepython remain research candidates.
