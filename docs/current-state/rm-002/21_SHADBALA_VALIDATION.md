# VEDA-RM-002 Shadbala Validation Decision

Status: `VALIDATION_BLOCKED` / predictive use `NOT_AUTHORIZED`
Activity: `SHADBALA_VALIDATION`
Date: 2026-08-16

## Question

Which Shadbala method or source discrepancy remains unresolved?

## Finding

P018-R2 research artifacts assert that core Shadbala methodology is
multi-source cross-verified, but the current repository does not provide the
passage-level evidence or a reconciled authority record needed to close the
legacy P018 conflict. The authoritative P018 baseline still records zero
accepted sources and nine unresolved methodologies. The R2 source register is
metadata-only, contains no passage IDs or quotations, and its claims are
marked `PROMOTION_READY` despite the absence of independent review.

The unresolved discrepancy is therefore provenance and method-contract
reconciliation, not permission to activate the R2 formulas. In addition, the
R2 implementation is only structurally tested: its BAV implementation repeats
the same contributor count for every target sign, and its simplified Sthana and
Kala sub-components are explicitly not independently validated.

## Validation

- Focused Shadbala and P018 governance regression:
  `python -m pytest -q tests/test_veda_shadbala_engine_p018_r2.py
  tests/test_veda_strength_governance_p018_r1.py
  tests/test_veda_strength_governance_p018.py`: `64 passed`.
- The tests verify schema, source-claim presence, blocked states and broad
  component behavior; they do not establish passage-level provenance,
  independent numerical fixtures, or complete method correctness.
- No new passage-level source record, independent review, or numerical
  boundary fixture was added in this activity. R2 source entries remain
  `METADATA_VERIFIED`, and R2 claims remain research-only despite their
  `PROMOTION_READY` metadata.
- `data/veda/validation/foundation/p018_strength/p018_summary.json` remains at
  `sources_accepted: 0`, `approved_strength_claims: 0`, and
  `unresolved_methodology: 9`.

## Decision

Keep Shadbala research and calculation capabilities blocked. Do not promote
R2 claims, repair or activate runtime calculations, alter Approved Core, add
empirical/prospective records, or infer classical formulas from metadata-only
source entries.

## Resumable next step

`SHADBALA_SOURCE_CONTRACT`: reconcile each R2 claim to citable passages and
edition records, then prepare independently reviewed numerical boundary
fixtures. Keep every unresolved component explicitly blocked until that
register and fixture review are complete.
