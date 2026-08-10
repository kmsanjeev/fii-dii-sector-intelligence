# VEDA-P006 Mission and Run Model

Date baseline: `2026-08-10`

## Mission Model

Missions are durable research intents represented by `ResearchMissionRecord`.

Important fields:

- `mission_id`
- `domain_id`
- `title`
- `objective`
- `research_type`
- `priority`
- `status`
- `query_strategy`
- `required_source_classes`
- `minimum_independent_sources`
- `known_claim_ids`
- `known_conflict_ids`
- `known_gap_ids`
- `safety_class`
- `completion_policy`
- `research_budget`
- `follow_up_depth`
- `parent_candidate_id`
- `parent_mission_id`

Supported research types:

- `DISCOVERY`
- `SOURCE_VERIFICATION`
- `CLAIM_VALIDATION`
- `CROSS_SOURCE_VALIDATION`
- `CONTRADICTION_RESOLUTION`
- `KNOWLEDGE_GAP`
- `PROVENANCE_RECOVERY`
- `UPDATE_MONITORING`
- `NOVELTY_SEARCH`
- `EMPIRICAL_VALIDATION`

Supported mission states:

- `DRAFT`
- `QUEUED`
- `ACTIVE`
- `PAUSED`
- `AWAITING_REVIEW`
- `COMPLETED`
- `BLOCKED`
- `CANCELLED`
- `ARCHIVED`

## Run Model

Every execution is a separate `ResearchRunRecord`.

Important fields:

- `run_id`
- `mission_id`
- `domain_id`
- `trigger_type`
- `started_at`
- `completed_at`
- `status`
- `provider_calls`
- `queries_executed`
- `sources_discovered`
- `sources_accepted`
- `sources_rejected`
- `evidence_created`
- `candidates_created`
- `duplicates_detected`
- `conflicts_created`
- `errors`
- `continuation_required`
- `continuation_hint`

Supported trigger types:

- `MANUAL`
- `HOURLY`
- `DAILY`
- `WEEKLY`
- `FOLLOW_UP`
- `ADMIN_REQUEST`
- `SYSTEM_RETRY`

Supported run states:

- `QUEUED`
- `RUNNING`
- `SUCCESS`
- `PARTIAL`
- `FAILED`
- `CANCELLED`
- `RECOVERABLE`

## Budget and Loop Controls

Mission budgets are explicit:

- `max_queries`
- `max_sources`
- `max_provider_calls`
- `max_runtime_seconds`
- `max_model_calls`
- `max_cost`
- `max_follow_up_depth`
- `max_retries`
- `cooldown_seconds`

The synthetic pilot proves that a `NEEDS_MORE_RESEARCH` decision can create exactly one controlled follow-up mission without creating an uncontrolled loop.
