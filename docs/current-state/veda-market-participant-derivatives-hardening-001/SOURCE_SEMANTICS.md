# Source semantics

The installed `nselib` implementation was inspected and one current-date
sample was accessed from NSE through the three functions below:

- `participant_wise_open_interest(trade_date)` returns participant rows and
  separate future-index, future-stock and option long/short buckets.
- `participant_wise_trading_volume(trade_date)` returns the same bucket shape
  for trading volume.
- `fii_derivatives_statistics(trade_date)` returns FII buy/sell/open-contract
  statistics by named futures/options instrument family.

The acquisition engine computes persisted participant futures net values as:

`future_index_long + future_stock_long - future_index_short - future_stock_short`

The persisted `*_OI_Net` values therefore mean aggregate futures net open
interest in contracts. They are not gross long contracts, gross short
contracts, an option position, a monetary exposure, or a price forecast.

`FII_Derivatives_Net` is a separate daily FII futures buy-contracts minus
sell-contracts statistic. It must not be treated as the FII participant OI
level or its OI change.

Source authority: NSE provider output accessed through the installed nselib
source functions. Runtime authority: provider-local persisted CSVs and the
deterministic contract in `engines/participant/institutional_contract.py`.
No source citation implies predictive validity.
