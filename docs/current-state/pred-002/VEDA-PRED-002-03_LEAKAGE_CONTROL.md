# Leakage Control

`audit_leakage()` checks prediction cutoffs, post-outcome fields, future-dated retrieved documents, outcome-bearing documents, case metadata, and data availability timestamps. Invalid cases are labelled `LEAKAGE_INVALID`, audited, and excluded before registry evaluation. `HistoricalPredictionHarness` performs the audit before locking and revealing an outcome.

The controls are deterministic and tested for both clean and contaminated cases. Future-derived empirical/model features remain a declared future-data risk unless they carry a cutoff no later than the prediction cutoff.
