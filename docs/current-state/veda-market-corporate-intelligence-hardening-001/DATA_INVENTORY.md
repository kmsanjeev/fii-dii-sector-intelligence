# Corporate Data Inventory

Inventory observed from the provider-local runtime on 2026-08-21. Counts are
descriptive and may change as provider-local files refresh.

| Dataset | Rows | Symbols | Date range / date field | Role | Authority |
|---|---:|---:|---|---|---|
| `data/intelligence/company_announcements.csv` | 402,844 | 2,434 | 2024-06-01..2026-08-20 / `date` | disclosure facts | primary structured NSE disclosure |
| `data/intelligence/event_calendar.csv` | 35,448 | 2,434 | 2023-01-02..2026-12-08 / `event_date` | scheduled/contextual events | primary structured NSE calendar |
| `data/intelligence/corporate_action_signals.csv` | 40,954 | 3,327 | 1999-01-09..2026-12-08 / `ex_date` | normalized actions | derived from primary NSE actions |
| `data/NSE/corporate_actions/*.csv` | yearly raw files | provider-local | 1999..2026 / exchange dates | raw source lineage | primary NSE files; not committed by this activity |
| `data/NSE/results/quarterly_results.csv` | 32,403 | 2,333 | 2017..2026 / period and filing fields | financial context linkage | fundamental-owned NSE results |
| `announcement_signals.csv` | 2,434 | 2,434 | latest per symbol | derived aggregate | not authoritative event fact |
| `upcoming_catalysts.csv` | 1 | 1 | generated forward view | legacy derived view | not authoritative event fact |
| `corporate_confidence_scores.csv` | 1,179 | 1,179 | legacy 12-month score | legacy directional/confidence view | excluded from authoritative contract |
| `block_bulk_deals.csv` / `deal_records.csv` | 16,612 / 13,282 | 1,327 | 2026 dates | institutional evidence | institutional-owned; not duplicated |
| `management_sentiment.csv` | 1,997 | 1,997 | as of 2026-08-20 | AI/derived sentiment | not authoritative corporate fact |

The source summary exposes rows, symbol counts, date ranges, authority,
directness, freshness and limitations at runtime. Raw provider data remains
local/ignored and is not part of the governed change.
