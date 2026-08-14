# Existing System and Reuse

| Area | Existing component | ADM-EMP-001 action |
|---|---|---|
| Shared empirical cases | `engines/ai/orchestration/cases.py` / `pred_cases` | Extended and reused |
| Prediction/outcome store | `engines/ai/orchestration/persistence.py` | Preserved and linked by shared database |
| Research platform store | `engines/ai/research/platform/store.py` | Same SQLite path reused |
| Admin authorization | `backend.auth.middleware.require_admin` | Reused |
| Admin UI | `frontend/src/pages/AdminPage.tsx` | Extended with Empirical Cases tab |
| Admin research patterns | `backend/routers/research.py`, `ResearchAdminConsole` | Preserved; no parallel console |
| File parsing | Python `csv`, installed `openpyxl` | Reused for CSV/XLSX |

New components were limited to the intake service, Admin router, API client,
and Admin component because no existing case import workflow or API existed.
The new SQLite tables are intake staging/audit tables in the existing shared
database, not a new database.
