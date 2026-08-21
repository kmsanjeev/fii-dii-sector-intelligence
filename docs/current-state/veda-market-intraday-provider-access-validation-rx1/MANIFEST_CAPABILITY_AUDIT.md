# Manifest capability audit

Manifest capability states are now explicit as
`DOCUMENTED_UNVALIDATED`, `POLICY_REVIEW_REQUIRED` or absent.

- Dhan: official documentation supports documented surfaces for intraday
  candles, quotes, WebSocket/depth, futures/OI, option chain and source
  Greeks; this runtime did not validate them because the account Data API plan
  is inactive.
- Zerodha: retained documented-unvalidated candles, quotes, WebSocket,
  depth and futures/OI boundaries. Option-chain and Greeks were removed from
  the inherited optimistic shared broker set because no official Kite Connect
  option-chain/Greeks API was identified in this audit.
- HDFC Sky: no market capabilities are advertised until the official portal
  and account scope are validated.
- yfinance remains public compatibility only.
- nselib and nsepython remain research candidates and cannot satisfy live
  production acceptance.

Provider support, account entitlement and runtime health remain separate
fields throughout the fabric.
