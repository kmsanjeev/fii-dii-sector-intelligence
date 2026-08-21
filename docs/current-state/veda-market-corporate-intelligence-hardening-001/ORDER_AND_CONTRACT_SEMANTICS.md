# Order, Contract, Approval and Completion Semantics

The contract intentionally does not collapse the following pairs:

| Observed fact | Not inferred |
|---|---|
| order/customer disclosure | revenue, delivery, execution or collection |
| MOU/LOI | binding order or completed transaction |
| board meeting/approval | implementation or closing |
| fundraising approval/announcement | funds received or dilution outcome |
| acquisition/merger announcement | regulatory approval, closing or integration |
| corporate action row | bullish/bearish direction |
| management change | management quality |
| result announcement | fresh fundamental metrics in Corporate |

Follow-up evidence is represented through later source events and watch items,
not reverse-inferred. `next_watch_items` identifies the type of evidence that
would resolve an open lifecycle, such as execution/amendment, completion or
fundamental ingestion.
