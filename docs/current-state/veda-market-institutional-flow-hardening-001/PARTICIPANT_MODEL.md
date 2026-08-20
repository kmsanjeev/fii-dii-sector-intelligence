# Participant and instrument model

| Label | Source meaning | Supported fields |
|---|---|---|
| FII / DII / PRO / CLIENT | F&O participant categories | OI, volume, deltas, windows, score, persistence, acceleration, reversal |
| FPI / MF / INSURANCE / RETAIL | Cash category labels | Buy/sell/net where present, windows and source date |

`CLIENT` is retained as the F&O participant label and `RETAIL` as the cash
category label. The existing `/api/participant/latest` response remains
backward compatible and carries `institutional_contract`; the additive
`/api/participant/institutional` endpoint returns the governed contract.
