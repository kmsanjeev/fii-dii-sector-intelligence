# VEDA-P006 Research Ledger

Date baseline: `2026-08-10`

The ledger is append-oriented and durable. It exists to reconstruct who did what, when, and against which artifact.

Ledger record fields:

- `event_id`
- `timestamp`
- `event_type`
- `domain_id`
- `mission_id`
- `run_id`
- `candidate_id`
- `actor_type`
- `actor_id`
- `action`
- `before_state`
- `after_state`
- `reason`
- `metadata`

Actor types:

- `SYSTEM`
- `MODEL`
- `ADMIN`
- `SCHEDULER`
- `PROVIDER`
- `VALIDATOR`

Event types implemented:

- `MISSION_CREATED`
- `MISSION_STARTED`
- `MISSION_PAUSED`
- `RUN_STARTED`
- `QUERY_EXECUTED`
- `SOURCE_DISCOVERED`
- `SOURCE_REJECTED`
- `EVIDENCE_CREATED`
- `CANDIDATE_CREATED`
- `CANDIDATE_MERGED`
- `VALIDATION_COMPLETED`
- `CONTRADICTION_FOUND`
- `FOLLOW_UP_CREATED`
- `ADMIN_APPROVED`
- `ADMIN_REJECTED`
- `MORE_RESEARCH_REQUESTED`
- `RUN_FAILED`
- `RUN_RECOVERED`

Tracked synthetic pilot ledger size:

- `92` events

The tracked snapshot includes full ledger lineage in `data/research/synthetic_pilot/research_ledger_event.json`.
