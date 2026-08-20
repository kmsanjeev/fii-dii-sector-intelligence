# Metric contracts

The contract exposes `1D`, `3D`, `5D`, `10D` and `20D` windows. Each window
contains `value`, `observations`, `expected_observations`, `coverage` and a
state of `COMPLETE`, `PARTIAL` or `UNAVAILABLE`. A missing value is never
replaced with zero.

- `persistence_20d`: percentage of available F&O OI-delta observations that
  are positive over the trailing 20 observations.
- `acceleration_5d`: current 5D OI-delta sum minus the prior 5D sum.
- `reversal_5d`: true only when current and preceding 5D sums are available
  and have opposite signs.
- `fii_dii` and `smart_retail`: existing provider-owned divergences.

These are descriptive market signals, not outcome probabilities, trade
instructions or predictive confidence. Options and cash-vs-derivatives
normalization are explicitly unsupported by the current source contract.
