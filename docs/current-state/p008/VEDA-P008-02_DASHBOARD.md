# VEDA-P008 Dashboard

Date: `2026-08-11`

Dashboard implementation lives in [frontend/src/components/admin/ResearchAdminConsole.tsx](/D:/Projects/fii-dii-sector-intelligence/frontend/src/components/admin/ResearchAdminConsole.tsx) and is fed by `GET /api/research/dashboard`.

## Dashboard Contents

- research engine status
- active domains
- active missions
- runs today
- successful runs
- failed runs
- pending approvals
- open contradictions
- knowledge gaps
- last research run
- next expected run
- provider health
- external web research status
- attention notifications

## Backend Support

`ResearchPlatformService.dashboard_bundle()` now assembles:

- domain-scoped mission/run/candidate counts
- provider-health rows
- notifications
- analytics bundle
- knowledge gaps
- coverage rows

## Important Behavior

- `IDLE` is distinguished from `PAUSED`
- `LOCAL_ONLY` external research status is shown when live web/API providers are not configured
- clicking dashboard attention cards navigates to queue, contradictions, or gaps views

