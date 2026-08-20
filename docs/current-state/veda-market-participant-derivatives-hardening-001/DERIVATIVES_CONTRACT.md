# Derivatives contract

The public `institutional_contract` is now `institutional-flow-1.1`, an
additive minor evolution of `institutional-flow-1.0`.

Each FII/DII/PRO/CLIENT participant exposes:

- `position_level`: aggregate futures `*_OI_Net`, in contracts;
- `position_change`: daily `*_OI_Delta`, in contracts;
- 1D/3D/5D/10D/20D change windows with observation counts and completeness;
- positive and negative 20-observation persistence;
- neutral `POSITIVE`, `NEGATIVE` or `MIXED` change direction;
- 5D acceleration and sign reversal descriptors.

The contract also exposes `derivatives.instrument_capabilities`, the source
granularity, formula, FII-statistics boundary, options decision and explicit
F&O/cash date alignment. `derived_signals.divergence.participant_derivatives`
compares FII/DII/PRO/CLIENT on the same aggregate-futures OI-change window.

All fields are descriptive. The contract deliberately contains no forecast,
recommendation, trading instruction, ML score or normalized cash comparison.
Missing evidence remains missing.
