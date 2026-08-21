# Evidence inventory

The audited local inventory at execution time was:

| Artifact | Rows | Symbols | Date coverage / cadence | Status |
|---|---:|---:|---|---|
| `block_bulk_deals.csv` | 16,612 | 1,327 | 2026-01-12 to 2026-08-19; disclosed deal dates | usable with semantic conditions |
| `deal_records.csv` | 13,282 | 1,327 | derived transaction pairing | contextual only |
| `institutional_deal_signals.csv` | 392 | 392 | 30-day derived summary as of 2026-08-19 | derived only |
| `quarterly_shp.csv` | 76,170 | 1,994 | quarter-end filings; 15,674 FII and 15,389 DII non-null cells | usable as periodic ownership |
| `holding_trends.csv` | 14,264 | 1,977 | derived QoQ history, as-of 2026-07-08 | derived ownership change |
| `participant_flow_scores.csv` | existing market dataset | market-wide | aggregate participant context | never stock-attributed |

The current NSE equity master has blank ISIN values. Exact symbols are used
only when present in the canonical master; unknown or stale symbols are marked
`REVIEW_REQUIRED`.
