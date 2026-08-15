# Source Provenance and Calibration

## Bounded activity result

Status: `PASS_WITH_CONDITION`.

The PRED-004 pilot remains empty in this activity. No consented or publicly
observable subject, governed event record, prospective prediction, outcome, or
calibration statistic was created. The legitimate-input blocker therefore
remains active.

## Provenance gate

Any future prediction or case must retain, at minimum, a subject reference,
domain/event definition, prediction and data cutoffs, source or observation
provenance, verification quality, and the method/knowledge/model versions used
at prediction time. Prediction evidence is snapshotted before the outcome
window; outcomes are independently recorded and cannot rewrite the prediction.
Unverified references remain `REFERENCE_NOT_VERIFIED` or otherwise gated and
are not promoted into `APPROVED_CORE`.

## Calibration result

| Measure | Result |
|---|---|
| Eligible verified empirical cases | `0` |
| Prospective predictions | `0` |
| Resolved predictions | `0` |
| Confidence calibration | `INSUFFICIENT_SAMPLE` |
| Predictive maturity | `PRED-M3_OPERATIONAL_PLUS` |
| PRED-M4 confidence claim | `NOT ACHIEVED` |

The registry’s empty-store calibration path and existing provenance/lock
regression tests were inspected; no code or production behavior required
change. Qualitative confidence bands and all human-validation statuses remain
unchanged.

## Validation evidence

- Focused PRED-001 through PRED-004, STD-002, and unified-retriever regression:
  `33 passed`.
- Two unified RAG rebuilds: `1,142` records each, identical corpus hash
  `8f19860f151ea2d644d526f6ade1a3cf581263e23785c25cc35ab3907c9ea065`.
- Both rebuilds reported `written={'documents': False, 'metadata': False,
  'manifest': False}`; no generated semantic churn was staged.

## Resumable next step

Continue with the controller-selected calculation-validation activity only
when its track is unblocked. Revisit calibration after legitimate governed
inputs produce independently resolved outcomes; do not synthesize fixtures,
subjects, outcomes, or performance claims for that purpose.
