# Event Taxonomy

The normalized event category is descriptive and deterministic. Unknown or
ambiguous source types remain `UNKNOWN`.

| Category | Source examples | Status semantics |
|---|---|---|
| `FINANCIAL_RESULTS` | result update, result calendar | disclosure or scheduled context; link to fundamental contract |
| `ORDER_CONTRACT` | source `ORDER_WIN` | `ANNOUNCED`; no revenue or completion inference |
| `MOU_LOI` | memorandum/letter of intent text | `ANNOUNCED`; no binding-order inference |
| `FUNDRAISING` | source fundraising disclosure | announced/approved context; no funds-received inference |
| `ACQUISITION` | acquisition disclosure | announced; no completion inference |
| `MERGER_DEMERGER` | normalized action category | dated source fact; transaction lifecycle remains open |
| `BOARD_MEETING` | board outcome/calendar | announced or scheduled; no approval/completion inference |
| `DIVIDEND`, `BONUS`, `STOCK_SPLIT`, `BUYBACK` | corporate actions | dated action facts; no bullish/bearish signal |
| `CAPACITY_EXPANSION` | capex expansion | disclosed fact only |
| `CREDIT_RATING`, `REGULATORY`, `INSOLVENCY` | source classifications | disclosed fact only |
| `MANAGEMENT_CHANGE` | management disclosure | disclosed fact only; no quality judgment |
| `UNKNOWN` | unmapped/ambiguous type | preserved without forced interpretation |

Classification method and confidence are returned with each event. Confidence
describes classification, not outcome probability or investment quality.
