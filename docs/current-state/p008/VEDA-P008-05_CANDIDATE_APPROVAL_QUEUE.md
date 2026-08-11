# VEDA-P008 Candidate Approval Queue

Date: `2026-08-11`

The approval queue is the primary P008 governance screen.

## Supported Filters and Controls

- approval status
- search
- contradiction-only view
- sort by updated time, priority, confidence, evidence, high stakes, contradictions
- pagination

## Candidate Summary Fields

- candidate id
- claim/title
- priority
- approval status
- novelty
- contradiction state
- evidence count
- high-stakes flag
- evolution status
- research recommendation

## Implementation Notes

- backend pagination and filters are served by `list_candidate_rows()`
- frontend pagination is implemented in [frontend/src/components/admin/ResearchAdminConsole.tsx](/D:/Projects/fii-dii-sector-intelligence/frontend/src/components/admin/ResearchAdminConsole.tsx)
- high-stakes filtering treats `HIGH`, `HIGH_STAKES`, and `CRITICAL` as high-stakes

