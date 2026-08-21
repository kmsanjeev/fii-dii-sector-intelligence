# VEDA-MARKET-INTRADAY-DATA-FOUNDATION-001

Status: `IMPLEMENTED_WITH_CONDITIONS`; after RX1 authentication evidence the
foundation decision is
`VEDA_MARKET_INTRADAY_DATA_FOUNDATION_OPERATIONAL_WITH_CONDITIONS`.
Market-data acquisition remains blocked until the configured Dhan Data API
entitlement is active and representative data is validated.

This activity establishes acquisition, identity, session, normalization,
quality, storage and bounded read foundations. It does not create signals,
BUY/SELL calls, trade setups, predictions, ML, alerts, orders or execution.
Existing EOD Swing/Positional behavior remains unchanged.

Primary candidate: official DhanHQ APIs. Current runtime state:
`AUTHENTICATED / ENTITLEMENT_BLOCKED`. yfinance remains a legacy chart-only
compatibility source and is never a silent governed fallback.
