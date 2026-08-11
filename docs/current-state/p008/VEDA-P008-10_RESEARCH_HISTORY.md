# VEDA-P008 Research History

Date: `2026-08-11`

Research History is backed directly by the P006 ledger.

## Available Filters

- domain
- mission
- run
- candidate
- event search text

## Lineage Support

The platform now exposes enough data for an Admin to reconstruct:

`MISSION -> RUN -> SOURCE -> EVIDENCE -> CANDIDATE -> DECISION`

through:

- `GET /api/research/ledger`
- `GET /api/research/missions/{mission_id}`
- `GET /api/research/runs/{run_id}`
- `GET /api/research/candidates/{candidate_id}`

