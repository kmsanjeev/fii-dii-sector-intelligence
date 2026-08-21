# Freshness before and after

The acquisition repair improves source retrieval and provenance; it does not
claim that a source-unavailable period is current.

| Symbol | Latest local period | Source | Governed interpretation |
|---|---|---|---|
| RELIANCE | 2026-03-31 | yfinance fallback | quarterly/TTM components current under frequency rules; aggregate evidence can remain `VERY_STALE` because extended annual data ends 2024-12-31 |
| ICICIBANK | 2026-03-31 | yfinance fallback | current quarterly evidence, with bounded source limitation |
| TCS | 2024-12-31 | NSE XBRL legacy | very stale; no current official row returned |
| LT | 2024-12-31 | NSE XBRL legacy | very stale; no current official row returned |
| EROSMEDIA | 2024-03-31 | NSE XBRL | delayed/re-filed filing captured; still stale by reporting period |

The existing `fundamental-evidence-1.0` contract continues to separate
component freshness from aggregate freshness. No stale value is promoted to a
fresh value merely because the transport succeeds.
