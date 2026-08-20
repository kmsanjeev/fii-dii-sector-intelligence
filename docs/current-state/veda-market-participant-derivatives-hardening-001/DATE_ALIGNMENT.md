# Date alignment

F&O and cash are separate source families. The contract reports:

- `fno_as_of` from the latest usable participant F&O OI observation;
- `cash_as_of` from the latest usable cash category observation;
- calendar lag and `ALIGNED`, `CASH_LAGGING`, `FNO_LAGGING` or `UNAVAILABLE`;
- `comparison_allowed: false`.

Equal dates do not make the units comparable: cash is rupee-crore turnover and
F&O is participant futures contracts/OI. A same-date label is therefore not a
normalization or an implied causal comparison.

The current observed baseline is F&O 2026-08-19 and cash 2026-08-18, with
provider freshness delayed/conditional as inherited from the predecessor.
