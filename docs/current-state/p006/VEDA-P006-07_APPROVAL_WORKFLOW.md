# VEDA-P006 Approval Workflow

Date baseline: `2026-08-10`

P006 enforces a hard boundary between autonomous research and authoritative approval.

Approval states supported:

- `PENDING`
- `UNDER_REVIEW`
- `APPROVED`
- `APPROVED_WITH_CONDITIONS`
- `REJECTED`
- `NEEDS_MORE_RESEARCH`
- `MERGE_REQUIRED`
- `SUPERSEDE_APPROVED`
- `ARCHIVED`

Admin actions supported:

- `APPROVE`
- `APPROVE_WITH_CONDITIONS`
- `REJECT`
- `REQUEST_MORE_RESEARCH`
- `MERGE`
- `SUPERSEDE`
- `ARCHIVE`

Approval persistence:

- candidate state is updated
- a `ResearchApprovalRecord` is written
- a ledger event is appended
- approved candidates become `PROMOTION_READY`
- approved candidates are not written into authoritative domain core automatically

Isolation rules proven by P006:

- admin review is separate from research execution
- a pending candidate does not block future runs of the same mission
- a `REQUEST_MORE_RESEARCH` decision can create a bounded follow-up mission
- admin mutation endpoints require `require_admin`

Synthetic pilot approval outcomes:

- `alpha`: `APPROVED`
- `beta`: `REJECTED`
- `delta`: `NEEDS_MORE_RESEARCH`
