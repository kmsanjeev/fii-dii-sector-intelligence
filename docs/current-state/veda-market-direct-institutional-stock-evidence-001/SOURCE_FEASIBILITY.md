# Source feasibility

## Authoritative source families

| Source | Local artifact | Frequency | Feasible claim | Boundary |
|---|---|---:|---|---|
| NSE bulk/block deal reports | `data/intelligence/block_bulk_deals.csv` | Daily disclosed activity | A dated disclosed bulk/block event for a symbol | Not a complete FII/DII tape; client classes are heuristic in the current local extract |
| NSE shareholding/XBRL | `data/NSE/shareholding/quarterly_shp.csv` | Quarterly / filing-driven | Ownership snapshot and like-for-like change | Not a transaction ledger or daily flow |
| Derived deal summary | `data/intelligence/institutional_deal_signals.csv` | Rolling 30-day rebuild | Derived summary of the local deal tape | Never treated as direct evidence |
| Market participant files | `data/intelligence/participant_flow_scores.csv` and related | Daily aggregate | Market-level participant context | Not attributed to a stock or sector |

NSE's public reports expose bulk/block deal archives and security-wise data,
while NSE shareholding pages expose quarter-end and submission dates. These
source semantics support the bounded claims above, not a universal
stock-level FII/DII flow claim.

References: [NSE all reports](https://www.nseindia.com/all-reports), [NSE
shareholding patterns](https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern),
[NSE block-deal market data](https://www.nseindia.com/market-data/block-deal-watch),
[SEBI bulk-deal disclosure](https://www.sebi.gov.in/legal/circulars/jan-2004/disclosure-of-trade-details-of-bulk-deals_11912.html).
