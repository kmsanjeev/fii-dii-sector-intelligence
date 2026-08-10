# VEDA Astrology Research Workflow

Status: P002 baseline  
Contract version: `2026-08-10`

## Lifecycle

The governed lifecycle is:

`DISCOVERED -> REGISTERED -> EXTRACTED -> CROSS_REFERENCED -> UNDER_REVIEW -> APPROVED -> IMPLEMENTATION_READY`

The full state model supported by the schema is:

- `DISCOVERED`
- `REGISTERED`
- `EXTRACTED`
- `CROSS_REFERENCED`
- `UNDER_REVIEW`
- `REVIEWED`
- `CONFLICT_FOUND`
- `NEEDS_MORE_RESEARCH`
- `APPROVED`
- `APPROVED_WITH_CONDITIONS`
- `REJECTED`
- `IMPLEMENTATION_READY`
- `IMPLEMENTED`
- `VALIDATED`
- `SUPERSEDED`

## Roles

- `RESEARCHER`
- `REVIEWER`
- `DOMAIN_APPROVER`
- `ENGINEERING_APPROVER`
- `VALIDATION_APPROVER`

P002 allows one actor to fill multiple roles, but the data model preserves role separation for future governance.

## Approval Record

Approvals are stored at:

- `data/veda/research/astrology/approvals/*.json`
- schema: `schemas/astrology/approval.schema.json`

An approval record captures:

- artifact set
- workflow state
- approval status
- role decisions
- conditions
- implementation readiness
- whether runtime comparison has happened yet

## P002 Boundary

`IMPLEMENTATION_READY` in P002 means research-governed and schema-valid.  
It does not authorize production astrology changes in this phase.
