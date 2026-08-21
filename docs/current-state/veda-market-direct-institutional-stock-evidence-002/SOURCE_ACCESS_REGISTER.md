# Source access register

| Candidate | Authority | Stock-specific | Participant-specific | Transaction-level | Frequency/history | Identifiers/date fields | Access/automation | Decision |
|---|---|---:|---:|---:|---|---|---|---|
| NSE disclosed bulk/block reports | NSE; SEBI disclosure framework | YES | YES for disclosed client; class not guaranteed in local extract | YES for disclosed events | Daily after market hours; local archive currently 2026-01-12 to 2026-08-19 | symbol, security name, client, deal type, quantity, price, report date; transaction/disclosure distinction limited locally | Public official source; automation conditional; local archive reproducibility | `AVAILABLE_WITH_RESTRICTIONS`; not a complete FII/DII tape |
| NSE shareholding filings | NSE corporate filings | YES | Ownership categories, not transaction participant identity | NO | Periodic/quarterly; local history through 2026-06-30 | symbol, as-on date, submission/broadcast dates, ownership percentages | Public official source; automation conditional | `AVAILABLE_WITH_RESTRICTIONS`; ownership snapshot only |
| SEBI trade-wise FPI equity archive | SEBI | YES | YES, but FPI/subaccount fields are masked and custodian/broker fields are bounded | YES | Historical archive listed through 2025; not a current daily all-participant feed | custodian code, report date, transaction ID, scrip, ISIN, transaction date, type, exchange, quantity, value | Public official archive; manual/history access; no raw data downloaded | `AVAILABLE_WITH_RESTRICTIONS`; FPI-only historical evidence |
| SEBI equity cash-market curation | SEBI | YES by linked source family | Varies by linked dataset | Varies | Daily/category and security-wise links | Depends on linked official dataset | Public official index; automation conditional | Candidate discovery; semantics must be assessed per dataset |
| BSE bulk/block disclosures | BSE via official/SEBI references | YES | YES for disclosed events | YES for disclosed events | Event-driven/daily archive varies | security/client/deal fields where available | Official link observed; one FAQ access returned 403; no bypass | `PUBLIC_MANUAL_ONLY` / `ACCESS_NOT_AUTHORIZED` for automation |
| SEBI corporate acquisition/disclosure filings | SEBI | YES when security named | Participant/event party may be identified | Event-level, not tape | Event-driven | filing and effective dates vary | Public official source; manual/conditional automation | `SEMANTICS_INSUFFICIENT` for daily flow |
| Licensed commercial market-data vendor | Not selected | Potentially | Potentially | Potentially | Vendor-dependent | Vendor-dependent | No subscription or licence selected | `NOT_SELECTED`; future procurement decision only |

Research did not scrape, bypass access controls, download raw restricted data,
or claim that repeated web references are independent evidence. Official
references inspected included [NSE All Reports](https://www.nseindia.com/all-reports),
[NSE shareholding filings](https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern),
[SEBI trade-wise FPI equity data](https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html),
[SEBI equity cash-market curation](https://www.sebi.gov.in/curation/equity_cash_market.html),
and the [SEBI bulk-deal disclosure circular](https://www.sebi.gov.in/legal/circulars/jan-2004/disclosure-of-trade-details-of-bulk-deals_11912.html).
