# VEDA-P008 Research Control Centre Architecture

Date: `2026-08-11`

## Governing Design

P008 reuses the P006/P007 research platform and does not introduce a second research backend.

Primary implementation paths:

- UI host: [frontend/src/pages/AdminPage.tsx](/D:/Projects/fii-dii-sector-intelligence/frontend/src/pages/AdminPage.tsx)
- Research UI: [frontend/src/components/admin/ResearchAdminConsole.tsx](/D:/Projects/fii-dii-sector-intelligence/frontend/src/components/admin/ResearchAdminConsole.tsx)
- Admin API client: [frontend/src/api/researchAdmin.ts](/D:/Projects/fii-dii-sector-intelligence/frontend/src/api/researchAdmin.ts)
- Backend router: [backend/routers/research.py](/D:/Projects/fii-dii-sector-intelligence/backend/routers/research.py)
- Read-model and decision service: [engines/ai/research/platform/service.py](/D:/Projects/fii-dii-sector-intelligence/engines/ai/research/platform/service.py)

## Information Architecture

Admin

- Research Dashboard
- Missions
- Runs
- Approval Queue
- Contradictions
- Knowledge Gaps
- Sources
- Research History
- Schedules
- Analytics

## Data Flow

`/admin` tab
-> `ResearchAdminConsole`
-> `frontend/src/api/researchAdmin.ts`
-> existing `/api/research/*` admin endpoints
-> `ResearchPlatformService`
-> persisted P006/P007 research artifacts

## Boundary Enforcement

- approvals remain `PROMOTION_READY` only
- no direct production rule mutation
- no dependence on Admin UI for research execution
- no persistent scheduling activation in P008

