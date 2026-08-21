# Direct source decisions

## Daily stock flow

Final: `NO_GOVERNED_DIRECT_DAILY_STOCK_FLOW_SOURCE`.

NSE disclosed bulk/block events are stock-specific and daily, but are a
disclosure subset rather than complete stock trading activity. The local
participant class is derived from client-name heuristics unless the source
reports a class. SEBI's trade-wise FPI archive is valuable participant-level
historical evidence but is FPI-only and not a current all-FII/DII stream.

## Sector flow

Final: `NO_GOVERNED_DIRECT_SECTOR_FLOW_SOURCE`.

No governed direct source or validated sector aggregation was introduced.
Stock evidence must not be presented as sector FII/DII attribution.

## Licensed source

No commercial source was selected or licensed. A future licensed vendor may be
evaluated only with explicit scope, terms, fields, dates, coverage and
reproducibility evidence.
