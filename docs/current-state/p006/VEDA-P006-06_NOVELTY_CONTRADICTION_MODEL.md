# VEDA-P006 Novelty and Contradiction Model

Date baseline: `2026-08-10`

## Novelty Status

Core novelty values:

- `NEW`
- `KNOWN`
- `DUPLICATE`
- `PARTIAL_EXTENSION`
- `REFINEMENT`
- `POSSIBLE_UPDATE`
- `UNKNOWN`

Comparison targets:

- `APPROVED_CORE`
- pending candidates
- rejected archive
- superseded archive

## Contradiction Status

Core contradiction values:

- `NONE`
- `POSSIBLE`
- `DIRECT`
- `PARTIAL`
- `CONTEXTUAL`
- `SOURCE_VARIANCE`
- `UNRESOLVED`

Conflict records are persisted as `ResearchConflictRecord`.

Important fields:

- `conflict_id`
- `candidate_id`
- `conflicting_candidate_id`
- `conflicting_core_id`
- `conflict_type`
- `analysis`
- `possible_reconciliation`
- `implementation_impact`
- `resolution_status`
- `confidence`

Synthetic pilot examples:

- `gamma` is `KNOWN` because it matches existing approved core
- `alpha` becomes a duplicate-strengthening continuation, not a second candidate
- `beta` is a `DIRECT` contradiction against approved core
- `delta` remains unresolved and triggers follow-up research rather than silent promotion
