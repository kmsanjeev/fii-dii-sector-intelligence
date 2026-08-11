# VEDA-P008 Admin Decision Workflow

Date: `2026-08-11`

## Supported Actions

- `APPROVE`
- `APPROVE_WITH_CONDITIONS`
- `REJECT`
- `REQUEST_MORE_RESEARCH`
- `MERGE`
- `SUPERSEDE`
- `ARCHIVE`

## Important Enforcement

- approved candidates become `PROMOTION_READY`
- production core knowledge is not modified automatically
- high-stakes approval requires explicit acknowledgement
- `REQUEST_MORE_RESEARCH` can create a follow-up mission
- every decision appends an approval record and a ledger event

## Files

- API mutation: [backend/routers/research.py](/D:/Projects/fii-dii-sector-intelligence/backend/routers/research.py)
- decision logic: [engines/ai/research/platform/service.py](/D:/Projects/fii-dii-sector-intelligence/engines/ai/research/platform/service.py)
- UI decision panel: [frontend/src/components/admin/ResearchAdminConsole.tsx](/D:/Projects/fii-dii-sector-intelligence/frontend/src/components/admin/ResearchAdminConsole.tsx)

