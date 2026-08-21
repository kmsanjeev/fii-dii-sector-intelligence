# Source Register

| Source ID | Dataset | Authority | Directness | Reproducibility | Permitted use |
|---|---|---|---|---|---|
| `NSE_CORPORATE_ANNOUNCEMENTS` | `company_announcements.csv` | PRIMARY_EXCHANGE_DISCLOSURE | DIRECT | SOURCE_ACCESS_DEPENDENT | disclosed announcement facts |
| `NSE_EVENT_CALENDAR` | `event_calendar.csv` | PRIMARY_EXCHANGE_DISCLOSURE | DIRECT | SOURCE_ACCESS_DEPENDENT | source-reported scheduled/effective date context |
| `NSE_CORPORATE_ACTIONS` | normalized corporate actions | DERIVED_FROM_PRIMARY | DERIVED | SOURCE_ACCESS_DEPENDENT | dated action facts, no automatic direction |
| `NSE_FINANCIAL_RESULTS` | `quarterly_results.csv` | PRIMARY_EXCHANGE_DISCLOSURE | DIRECT | SOURCE_ACCESS_DEPENDENT | linkage only; metrics remain fundamental-owned |

Rejected as authoritative Corporate sources:

- anonymous/SEO event lists, copied yoga-like tables, search snippets and
  unsourced summaries;
- `corporate_confidence_scores.csv`, `announcement_signals.csv` and
  `management_sentiment.csv` as fact sources because they are derived or AI/
  directional aggregates;
- institutional block/bulk and deal-tape datasets as Corporate confirmation;
  they remain under `stock-institutional-evidence-1.1` / institutional
  contracts.

No external web research or new provider access was required for this
hardening; the existing structured exchange-source lineage was audited first.
