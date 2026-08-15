# Evidence Model

`SynthesisEvidence` retains source engine, phase, chart ID, subject ID, domain, type, rule/factor, direction, authority, knowledge zone, method variant, validation state, conditions, time scope, citations, and lineage.

Roles are `PRIMARY`, `SUPPORTING`, `MODIFYING`, `CONDITIONAL`, `TIMING`, `OPPOSING`, `REDUNDANT`, `WEAK`, and `EXPERIMENTAL`. A role is contextual and does not change the source evidence.

Lineage is keyed by `lineage_id`, then rule family, factor, or evidence ID. Only the strongest item in a correlated cluster contributes as primary/support; other correlated items are retained as `REDUNDANT` with links.
