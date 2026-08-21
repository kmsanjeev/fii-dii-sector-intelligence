# VEDA-MARKET-THEME-INTELLIGENCE-001

Status: `VEDA_MARKET_THEME_INTELLIGENCE_OPERATIONAL_WITH_CONDITIONS`

The FII-DII repository now exposes a governed, read-only Theme Intelligence
contract at `/api/themes/governed`. FII-DII remains the data and calculation
owner. VEDA only resolves the formal capability and normalizes the provider
response.

The new contract is intentionally separate from the legacy Phase-E `/api/themes`
surface. It uses a bounded 15-theme registry, deterministic current membership,
equal-weight price proxies, coverage-aware breadth, and cautious leadership
states. It does not claim an official theme index, forecast, capital rotation,
or theme-specific FII/DII flow.

The conditional state reflects current-universe membership, unavailable
historical membership snapshots, and `INSUFFICIENT_HISTORY` persistence until a
governed multi-date theme history exists.
