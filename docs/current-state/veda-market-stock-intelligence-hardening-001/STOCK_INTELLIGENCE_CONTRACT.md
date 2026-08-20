# Stock intelligence contract

Contract version: `stock-intelligence-1.1`.

The additive `stock_intelligence` object contains:

- `identity`;
- `facts.price_windows`, `history`, `volume`, `technical`, `fundamentals`, `corporate`;
- `signals.trend_state`, momentum, market/sector relative strength, sector context, cross-layer state, institutional context, and technical accumulation/distribution context;
- `evidence_quality`, `date_alignment`, `limitations`, `next_watch_items`, and descriptive `interpretation`.

The result is a signal/context contract, not advice or prediction. A price/volume signal is explicitly technical. A deal or ownership record is descriptive and scoped. Broad participant flow is `MARKET_LEVEL_CONTEXT_ONLY`.
