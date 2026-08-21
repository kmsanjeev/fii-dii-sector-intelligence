# Historical Candle Contract

Contract version: `intraday-market-data-1.0`.

Canonical candle fields include exact `instrument_id`, `trade_date`,
`interval`, `bar_start`, `bar_end`, `timezone`, OHLC, optional `volume`,
optional `open_interest`, closure state, source, retrieval time, status and
quality flags. Missing values remain missing; they are never converted to zero.

Supported provider intervals are 1, 5, 15, 25 and 60 minutes. Higher bars can
be derived only within exchange-session boundaries. OHLC uses first/max/min/
last; volume sums; OI uses the last point-in-time value and is never summed.
