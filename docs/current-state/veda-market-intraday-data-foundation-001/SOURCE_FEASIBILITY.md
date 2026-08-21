# Source Feasibility

| Source | Historical | Live | Options/OI | Authority | Current state |
|---|---|---|---|---|---|
| Official DhanHQ Data APIs | 1/5/15/25/60 minute candles; provider documents last five years | quote APIs and WebSocket feed | futures/options OI, option chain, IV/Greeks where supplied | official authenticated provider | `AUTHORIZED_WITH_LIMITS`; account entitlement unverified |
| Official Dhan instrument master | security IDs and derivative metadata | n/a | identity dependency | official provider list | reachable; no raw file committed |
| yfinance | chart-oriented query path | non-governed compatibility | not selected | secondary/free chart source | `LEGACY_CHART_SOURCE_ONLY` |
| Existing `/ws/live` | none | intelligence snapshots only | none | internal derived data | not a market feed |

No scraping, browser bypass, private endpoint, credential bypass or unlicensed
redistribution is used.
