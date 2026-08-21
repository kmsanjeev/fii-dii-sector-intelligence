# Governed portfolio contract

## Provider endpoint

`GET /api/portfolio/governed`

Contract version: `portfolio-intelligence-1.0`
Provider capability version: `0.1.0`
Mode: read-only, local provider-owned data

VEDA exposes `market.portfolio.intelligence` through the existing
`veda-market-intelligence` provider. The VEDA capability requires
authentication and the `portfolio` entitlement. Anonymous queries return the
existing `AUTHENTICATION_REQUIRED` boundary without forwarding portfolio data.

## Position evidence

Each position preserves quantity, average cost, invested value, latest price,
market value, unrealized P/L, weight, first/last transaction dates, price
as-of date, source and data status. Missing prices remain `null`; they are not
coerced to zero.

The projection includes market/sector/stock/fundamental/corporate and
institutional context where the existing governed cross-layer services can
provide it. Provider-local failures are isolated per position and surfaced in
freshness/limitations metadata.

## Sector and Theme exposure

Sector exposure is aggregated from current positions. Theme exposure supports
many-to-many membership. Gross Theme membership exposure is reported with an
explicit overlap map and warning: overlapping Theme weights are not
independent capital and must not be summed as if they were a partition.

Current membership is not historical membership. No Theme persistence claim is
made until governed multi-date membership history exists.

## Risk and execution

Existing risk CSV outputs are read when present. Empty portfolios correctly
report risk outputs as unavailable rather than fabricating zero risk.
Broker/execution data is contextual only. This contract cannot buy, sell,
submit, cancel or mutate orders.
