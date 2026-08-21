# Sector attribution decision

Decision: `NO_GOVERNED_DIRECT_SECTOR_FLOW_SOURCE`.

The existing sector rotation contract remains price/breadth/leadership
context. Market participant values remain `MARKET_LEVEL_CONTEXT_ONLY`.
Individual stock evidence is not summed into a sector FII/DII flow number.

If a later activity adds a derived stock aggregation, its output must be named
`DERIVED_STOCK_LEVEL_INSTITUTIONAL_CONFIRMATION`, retain source coverage and
date alignment, and must never be presented as direct sector FII/DII flow.
