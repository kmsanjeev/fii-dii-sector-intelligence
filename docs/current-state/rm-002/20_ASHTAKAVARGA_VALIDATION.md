# VEDA-RM-002 Ashtakavarga Validation Decision

Status: `VALIDATION_BLOCKED` / predictive use `NOT_AUTHORIZED`
Activity: `ASHTAKAVARGA_VALIDATION`
Date: 2026-08-16

## Question

Which Ashtakavarga validation claim remains unresolved?

## Finding

The existing BAV/SAV paths are not valid calculation fixtures despite passing
their current structural tests. `calculate_bav()` iterates over each target
sign but does not use that target sign when counting contributors. It counts
the chart's qualifying planets once and repeats that count in every sign.
`calculate_sav()` then aggregates those repeated BAV columns.

Using the existing test chart
`Sun=1, Moon=4, Mars=7, Mercury=10, Jupiter=1, Venus=4, Saturn=7`:

| Output | Observed result | Validation consequence |
|---|---:|---|
| Sun BAV each sign | 6 bindus for all 12 signs | Target-sign distribution is not represented |
| Sun BAV total | 72 | Inflated/repeated column result |
| SAV each sign | 38 bindus for all 12 signs | Aggregated BAV defect propagates to SAV |
| SAV total | 456 | Not suitable for transit-window or interpretation claims |

The existing suite passes `53/53` because it checks schema, non-negative
counts, total aggregation, table length, and source-claim presence; it does
not assert target-sign sensitivity or an independently reviewed fixture.

## Evidence boundary

- This is a deterministic implementation finding, not an empirical case,
  prospective prediction, or predictive performance result.
- Existing source claim IDs remain provenance metadata only. The repository
  does not yet contain a passage-level, independently reviewed contributor
  contract sufficient to authorize a corrected method.
- No BAV/SAV interpretation, transit timing, production activation, Approved
  Core promotion, or trust-zone change is authorized by this activity.

## Decision

`ASHTAKAVARGA_VALIDATION` remains blocked for predictive use. The next narrow
step is to establish a source-to-contract register for contributor semantics,
including whether the method is contributor-relative and how each occupied
planet contributes to each target sign. Then add independently reviewed
deterministic fixtures that require sign-sensitive BAV columns and reconcile
SAV totals. Only after those fixtures pass should a code repair be considered.

## Validation performed

- Repository authority, readiness, prior P018 research, and current Git state
  were inspected.
- Focused Shadbala and P018 governance regression:
  `python -m pytest -q tests/test_veda_shadbala_engine_p018_r2.py
  tests/test_veda_strength_governance_p018_r1.py
  tests/test_veda_strength_governance_p018.py`: `64 passed`.
- Direct execution of the existing fixture reproduced constant BAV/SAV
  columns as documented above.
- Boundary probe result: `BAV-TARGET-SIGN-SENSITIVITY` is `FAIL` while
  `SAV-COLUMN-AGGREGATION` is `PASS`; this confirms a calculator defect, not
  a validated contributor method.
- No external source, empirical case, prospective subject, prediction
  outcome, or production code change was created.

## Resumable next step

`ASHTAKAVARGA_SOURCE_CONTRACT`: verify a citable contributor-method edition,
define target-sign and occupancy semantics, and prepare boundary fixtures;
retain BAV/SAV as `RESEARCH_REQUIRED` until that work is independently
reviewed.
