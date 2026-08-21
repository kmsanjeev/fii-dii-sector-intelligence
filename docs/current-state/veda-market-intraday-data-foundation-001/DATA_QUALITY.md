# Data Quality

Implemented checks cover missing required fields, numeric prices, positive
prices, OHLC relationships, negative volume/OI, duplicate canonical keys and
session/ordering metadata. Coverage reporting is reserved for source-backed
acquisition because expected bars must use actual exchange sessions. Unknown
gaps are not synthesized as zero-volume bars.
