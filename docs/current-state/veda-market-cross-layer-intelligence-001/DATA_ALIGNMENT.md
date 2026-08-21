# Data alignment

The contract preserves separate dates for Market, institutional cash,
institutional F&O, sector, stock, fundamentals and corporate evidence.
Current live evidence shows Market/institutional data at `2026-08-19`, sector
and stock EOD data at `2026-08-20`, and slower fundamentals/corporate sources
with their own dates.

Alignment states are `ALIGNED`, `PARTIALLY_ALIGNED`, `MIXED_FREQUENCY` and
`NOT_COMPARABLE`. Overall freshness is the weakest material component, not the
freshest component.
