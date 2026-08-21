# Futures OI semantics

`oi_1d` is the source-reported daily change in open interest for the selected contract. `oi_5d` is the sum of source-reported changes only across a continuous selected expiry; roll-contaminated windows are withheld.

Positioning labels are descriptive derived states: `LONG_BUILDUP`, `SHORT_BUILDUP`, `LONG_UNWINDING`, `SHORT_COVERING`, `NEUTRAL`, `ROLL_TRANSITION`, and `INSUFFICIENT_EVIDENCE`. They do not identify FII/DII activity and do not constitute a recommendation.
