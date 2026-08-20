# VEDA-MARKET-STOCK-INTELLIGENCE-HARDENING-001

Status: `IMPLEMENTED / OPERATIONAL_WITH_CONDITIONS`

This activity hardens the existing `/api/stocks/{symbol}` surface with the additive `stock-intelligence-1.1` contract. It reuses the existing OHLCV cache, technical indicators, price momentum, sector-rotation-1.1, ownership/deal context, fundamentals, and corporate-event datasets.

The contract is descriptive and bounded. It does not issue BUY/SELL instructions, target prices, expected returns, predictions, ML scores, astrological outputs, or broad FII/DII stock attribution.

## Scope

- canonical NSE/equity-master identity and bounded unknown-symbol handling;
- deterministic 1D/3D/5D/10D/20D price windows with dates and completeness;
- separate trend, momentum, volume confirmation, market/sector relative strength;
- reuse of sector-rotation-1.1 rather than a second sector engine;
- explicit cross-layer states and date alignment;
- institutional scope constrained to the governed five-state vocabulary;
- fundamentals and corporate events as dated evidence, not automatic catalysts;
- evidence quality, limitations, and next watch items.

Raw provider data remains local/ignored and is not part of this change.
