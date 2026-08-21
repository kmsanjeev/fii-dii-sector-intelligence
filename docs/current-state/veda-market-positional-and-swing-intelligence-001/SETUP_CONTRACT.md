# Setup contract

Contract: `trade-setup-intelligence-1.0`
Capability: `market.trade-setup.intelligence`
Provider: `veda-market-intelligence`
Actions: read-only
Freshness: provider-owned EOD

Detail route: `GET /api/trade-setups/{symbol}?horizon=SWING|POSITIONAL`
Screen route: `GET /api/trade-setups/screen?horizon=...&limit=1..50&fno_only=...`

The detail contract includes setup state, direction, technical, F&O, market,
sector, Theme, institutional, fundamental, corporate, dates, conflicts,
risks, invalidation, entry context, portfolio context, evidence quality,
facts, interpretation, watch items, limitations and provenance. The screen
contract is bounded and returns ranked descriptive setup records plus counts;
it does not perform unbounded deep analysis.
