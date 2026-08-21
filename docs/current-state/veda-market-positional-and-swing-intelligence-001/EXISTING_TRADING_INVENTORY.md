# Existing trading inventory

- Reused: technical indicators, price momentum, stock intelligence,
  governed F&O, market context, sector rotation, Theme membership/intelligence,
  institutional flow, fundamental and corporate evidence.
- Isolated: legacy `bull_run_probability.csv`, `ml_scores_combined.csv`,
  `trade_conviction_scores.csv` and `signal_recommender`/legacy execution
  paths. They remain historical or experimental and are not dependencies.
- Not reused as authority: BUY/SELL labels, target prices, position sizing,
  broker mutation, backtesting outcomes or intraday state.
- Portfolio context is represented as `NOT_REQUESTED` unless an authorized
  portfolio context is supplied; no holdings or order action is inferred.
