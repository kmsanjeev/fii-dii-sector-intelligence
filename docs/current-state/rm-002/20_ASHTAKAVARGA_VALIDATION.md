# VEDA-RM-002 Ashtakavarga Validation Decision

Status: `CALCULATION_DEFECT_CLOSED` / method validation and predictive use `NOT_AUTHORIZED`
Activity: `ASHTAKAVARGA_VALIDATION`
Date: 2026-08-16

## Question

Which Ashtakavarga validation claim remains unresolved?

## Finding

The existing BAV/SAV paths contained a calculation defect despite passing
their current structural tests. `calculate_bav()` iterated over each target
sign but did not use that target sign when counting contributors. It counted
the chart's qualifying planets once and repeated that count in every sign.
`calculate_sav()` then aggregated those repeated BAV columns.

The narrow engineering correction now assigns each qualifying bindu to the
contributor's occupied sign before producing the twelve BAV columns. The
correction is covered by a deterministic target-sign sensitivity test. This
closes the identified implementation defect only; it does not validate the
classical contributor table or authorize interpretation.

Using the existing test chart
`Sun=1, Moon=4, Mars=7, Mercury=10, Jupiter=1, Venus=4, Saturn=7`:

| Output | Observed result | Validation consequence |
|---|---:|---|
| Sun BAV non-zero columns | signs 1, 4, 7, 10 = 1, 2, 2, 1 | Target-sign distribution is represented after repair |
| Sun BAV total | 6 | Structural invariant only; contributor method remains unvalidated |
| SAV non-zero columns | signs 1, 4, 7, 10 = 12, 10, 10, 6 | Aggregation follows repaired BAV columns |
| SAV total | 38 | Not suitable for transit-window or interpretation claims |

The prior suite passed `53/53` because it checked schema, non-negative
counts, total aggregation, table length, and source-claim presence; it did
not assert target-sign sensitivity or an independently reviewed fixture.
The repaired focused suite now passes `63/63` across the Ashtakavarga,
strength-governance, OGDB, and Wikidata adapter tests.

## Evidence boundary

- This is a deterministic implementation finding, not an empirical case,
  prospective prediction, or predictive performance result.
- Existing source claim IDs remain provenance metadata only. The repository
  does not yet contain a passage-level, independently reviewed contributor
  contract sufficient to authorize a corrected method.
- No BAV/SAV interpretation, transit timing, production activation, Approved
  Core promotion, or trust-zone change is authorized by this activity.

## Decision

`ASHTAKAVARGA_VALIDATION` remains blocked for method validation and predictive
use. The target-sign calculation defect is closed, but BAV/SAV remain
`IMPLEMENTED_UNVALIDATED` and `RESEARCH_REQUIRED` because the repository still
lacks passage-level contributor provenance and an independently reviewed
classical numerical witness. No interpretation, transit timing, production
activation, Approved Core promotion, empirical use, or prospective use is
authorized.

## Validation performed

- Repository authority, readiness, prior P018 research, and current Git state
  were inspected.
- Focused Shadbala and P018 governance regression:
  `python -m pytest -q tests/test_veda_shadbala_engine_p018_r2.py
  tests/test_veda_strength_governance_p018_r1.py
  tests/test_veda_strength_governance_p018.py`: `64 passed`.
- Direct execution of the boundary fixture now produces sign-sensitive BAV
  columns and corresponding SAV columns as documented above.
- Boundary probe result after repair: `BAV-TARGET-SIGN-SENSITIVITY` is `PASS`
  and `SAV-COLUMN-AGGREGATION` remains structurally covered; this confirms the
  implementation invariant only, not a validated contributor method.
- No external source, empirical case, prospective subject, prediction outcome,
  or predictive activation was created. The narrow calculation defect repair
  is the only production-code change in this closure.

## Resumable next step

`ASHTAKAVARGA_PASSAGE_AUDIT`: verify a citable contributor-method edition,
register exact locators and school variance, and add an independently reviewed
numerical witness; retain BAV/SAV as `RESEARCH_REQUIRED` until that work is
independently reviewed.
