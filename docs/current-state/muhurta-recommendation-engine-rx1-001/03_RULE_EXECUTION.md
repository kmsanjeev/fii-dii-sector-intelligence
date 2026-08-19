# Rule Execution and Abstention

The evaluator accepts only the existing declarative operator set and rejects expressions, Python code, callables, unknown operators, unknown rule shapes, missing source lineage, contract identity mismatch, and hash mismatch.

`PANCHANGA_FACTS_AVAILABLE` is a calculation dependency. If it is unavailable, the result is `ABSTAIN` with `CALCULATION_DEPENDENCY_UNAVAILABLE`. The Education routine-scope hard requirement returns `ABSTAIN` with `ACTIVITY_SCOPE_MISMATCH` when routine daily study is requested. Nonblocking source gaps are preserved in `unevaluated_source_gaps`.

The engine evaluates a single supplied candidate. A positive source-scoped indicator produces `SUPPORTED_WITH_CAUTION`; simultaneous support and adverse/context results produce `MIXED_FACTORS`; no numeric score or probability is emitted.
