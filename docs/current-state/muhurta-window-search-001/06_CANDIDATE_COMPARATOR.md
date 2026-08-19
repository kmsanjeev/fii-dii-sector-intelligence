# Candidate comparator

`CATEGORICAL_STATE_ORDER_V1` is explicit orchestration governance, not a score:

1. `SUPPORTED_WITH_CAUTION`
2. `MIXED_FACTORS`
3. `INSUFFICIENT_RULE_COVERAGE`
4. `NOT_RECOMMENDED_UNDER_SELECTED_RULESET`
5. `ABSTAIN`

Only the first two states are recommendable search candidates. Same-state candidates are not ranked by rule count, factor count, duration, or hidden weights. They are returned as equivalent top windows in chronological order. A primary window is therefore a deterministic representative of the top categorical group, not a claim of greater success probability.
