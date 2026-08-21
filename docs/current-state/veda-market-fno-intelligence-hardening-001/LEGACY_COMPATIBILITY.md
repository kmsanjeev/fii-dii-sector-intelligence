# Legacy compatibility

`data/intelligence/fno_intelligence.csv` retains `symbol`, `futures_oi`, `oi_1d`, `oi_5d`, `oi_signal`, `fut_close`, `expiry`, and `as_of_date`, with additive governed fields. `market_context.json.pcr`, `calls_oi`, `puts_oi`, and `trade_date` remain available, but their stock-option aggregate semantics are explicit and `pcr_signal` is no longer directional.

Legacy stock wording was changed from unsupported smart-money/bullish/bearish claims to descriptive price/OI direction. Existing BUY/SELL surfaces remain non-authoritative and no execution path was added.
