# VEDA-P008 Mission Control

Date: `2026-08-11`

Mission Control reuses the existing mission model from P006/P007 and exposes it through the admin console.

## Admin Actions Implemented

- create mission
- pause mission
- resume mission
- run now
- archive mission

## UI/Backend Paths

- UI: [frontend/src/components/admin/ResearchAdminConsole.tsx](/D:/Projects/fii-dii-sector-intelligence/frontend/src/components/admin/ResearchAdminConsole.tsx)
- API: `GET /api/research/missions`, `POST /api/research/missions`, `GET /api/research/missions/{mission_id}`, `POST /api/research/missions/{mission_id}/pause`, `POST /api/research/missions/{mission_id}/resume`, `POST /api/research/missions/{mission_id}/trigger`
- Service: `list_mission_rows()`, `get_mission_detail()`, `pause_mission()`, `resume_mission()`, `archive_mission()`

## Mission Detail Exposes

- objective
- research type
- required source classes
- minimum independent sources
- schedule
- run history
- candidate history
- follow-up missions
- ledger history

