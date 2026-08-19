# Segmentation contract

- All datetimes are aware and normalized to the location timezone.
- The range is strictly bounded: `DEFAULT_SEARCH_RANGE=7 days`, `MAX_SEARCH_RANGE=31 days`.
- Daily earliest/latest bounds clip local-day intervals before segmentation.
- Boundaries come from explicit caller-supplied transition records or the existing Kundli/P032 calculated transition adapter. No fixed 15-minute, 30-minute or hourly sampling is used.
- A representative is the interval start plus one second when the interval permits; otherwise its midpoint. This avoids evaluating exactly on a half-open P032 boundary.
- Adjacent intervals merge only when RX1 recommendation state, evaluated outcomes, support/adverse factors, requirements, source gaps, abstention reason, contract metadata and caution are all semantically equal.
- Activity scope is validated by RX1. Unsupported activities return a maturity gate without generic search.
