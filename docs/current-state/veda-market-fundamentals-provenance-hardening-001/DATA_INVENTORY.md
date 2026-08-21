# Data inventory

| Dataset | Role | Authority | Period/date limitation |
|---|---|---|---|
| `data/NSE/results/quarterly_results.csv` | NSE XBRL quarterly P&L history | Primary provider-local source | Period end and filing date are separate; malformed filing dates remain untrusted |
| `data/NSE/results/extended_quarterly_raw.csv` | Extended XBRL component cache | Primary provider-local cache | Raw component lineage is not fully retained in the aggregate output |
| `data/NSE/results/extended_financials.csv` | OPM, ROCE, book value, capital and growth aggregates | Derived provider-local output | Aggregate `as_of_date` is not a filing date |
| `data/NSE/results/valuation_scores.csv` | Legacy ratios and labels | Legacy derived output | Composite labels are not a governed fair-value conclusion; `roe_pct` is mislabeled net margin |
| `data/NSE/equity_master/company_fundamentals_master.csv` | Identity, classification and ownership master | Provider-local master | `last_updated` is master freshness, not financial statement period |
| `data/reference/company_fundamentals_master.csv` | Legacy/reference classification and ratios | Reference/legacy | Not used as authoritative financial evidence |

The existing `data_loader` remains the shared runtime loader. The evidence
service has a bounded local-file fallback for isolated provider probes.
