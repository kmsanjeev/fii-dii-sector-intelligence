# VEDA-MARKET-CROSS-LAYER-INTELLIGENCE-001

Status: `COMPLETE / OPERATIONAL_WITH_CONDITIONS`

The FII-DII Market provider now composes the existing Market, institutional,
sector and stock contracts through one bounded deterministic endpoint:
`GET /api/market/intelligence/cross-layer`.

Composition ownership remains in FII-DII. VEDA owns routing, authorization,
provider invocation, normalization and presentation. No Market data or
calculation engine moved into VEDA.

The result exposes component states, candidate chains, alignment, conflicts,
dates, freshness, evidence quality, limitations and next-watch items. It does
not create a BUY/SELL score, target price, prediction or stock/sector FII/DII
attribution.
