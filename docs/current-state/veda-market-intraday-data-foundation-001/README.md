# VEDA-MARKET-INTRADAY-DATA-FOUNDATION-001

Status: `IMPLEMENTED_WITH_CONDITIONS`; final decision is
`VEDA_MARKET_INTRADAY_DATA_FOUNDATION_BLOCKED` until a Dhan Data API access
token and entitlement are verified in a controlled runtime.

This activity establishes acquisition, identity, session, normalization,
quality, storage and bounded read foundations. It does not create signals,
BUY/SELL calls, trade setups, predictions, ML, alerts, orders or execution.
Existing EOD Swing/Positional behavior remains unchanged.

Primary candidate: official DhanHQ APIs. Current runtime state:
`CREDENTIALS_UNAVAILABLE`. yfinance remains a legacy chart-only compatibility
source and is never a silent governed fallback.
