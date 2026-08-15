# VEDA-RM-002 Ashtakavarga Source-Contract Boundary

Status: `VALIDATION_BLOCKED` / predictive use `NOT_AUTHORIZED`  
Activity: `ASHTAKAVARGA_VALIDATION`  
Date: 2026-08-16

## Question

Which Ashtakavarga validation claim remains unresolved after the existing
structural tests and the new governed-input review?

## Contract finding

The R2 claims `VEDA-R2-CLM-000008` (BAV contributor table) and
`VEDA-R2-CLM-000009` (SAV aggregation) are marked `PROMOTION_READY`, but the
repository contains no passage IDs, page/verse locators, or independently
reviewed numerical witness for either claim. Their metadata may remain a
research lead; it is not sufficient authority for formula activation.

The deterministic boundary fixture at
`data/veda/validation/foundation/p018_strength/ashtakavarga_boundary_fixture.json`
therefore tests only an implementation invariant: a BAV result must be
target-sign sensitive when the chart contains occupied signs with different
relative contributor positions, and SAV must aggregate the resulting columns.
It deliberately does not prescribe a classical table, expected bindu totals,
interpretation, transit window, or predictive conclusion.

## Observed result

The current `calculate_bav()` previously repeated one contributor count for
every target sign, so the fixture's sign-sensitivity invariant failed.
`calculate_sav()` inherited the repeated columns. The defect is now corrected:
qualifying bindus are assigned to the contributor's occupied sign and the
boundary test passes. This confirms an implementation invariant, not a
validated astrological method.

## Governance decision

Keep BAV and SAV `RESEARCH_REQUIRED` and `IMPLEMENTED_UNVALIDATED`; keep
production activation, Approved Core promotion, predictive interpretation,
empirical records, and prospective records at zero. The narrow defect repair
does not promote metadata-only claims or resolve source provenance.

The next admissible step is passage-level source reconciliation for contributor
semantics and an independently reviewed numerical fixture. Any further method
change remains a separately governed activity.

## Resumable next step

`ASHTAKAVARGA_PASSAGE_AUDIT`: obtain inspectable witnesses for the contributor
contract, register exact locators and school variance, then review the repaired
boundary fixture before any additional method or production decision.
