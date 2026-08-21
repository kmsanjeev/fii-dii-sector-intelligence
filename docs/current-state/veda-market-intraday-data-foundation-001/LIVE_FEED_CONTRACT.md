# Live Feed Contract

The Dhan seam is prepared for normalized LTP, last trade time, last quantity,
volume, day OHLC, optional OI, bid/ask/depth, source, connection state and
freshness. Connection states are `CONNECTING`, `CONNECTED`, `DEGRADED`,
`STALE`, `RECONNECTING`, `DISCONNECTED`, `AUTH_FAILED`,
`ENTITLEMENT_FAILED` and `SOURCE_FAILED`.

Current runtime is `NOT_CONFIGURED`; no live socket is started by application
startup. The existing `/ws/live` remains an intelligence heartbeat and is not
exposed or described as this feed.
