# VEDA-P006 Scheduling and Provider Model

Date baseline: `2026-08-10`

## Schedule Contract

Schedules are modeled independently from mission logic through `ResearchScheduleRecord`.

Fields:

- `schedule_id`
- `domain_id`
- `mission_id`
- `cadence_type`
- `timezone`
- `enabled`
- `next_run_at`
- `last_run_at`
- `misfire_policy`
- `overlap_policy`
- `priority`

Cadence values:

- `HOURLY`
- `DAILY`
- `WEEKLY`
- `CUSTOM`
- `MANUAL_ONLY`

Overlap policies:

- `SKIP`
- `QUEUE`
- `COALESCE`
- `ALLOW`

Misfire policies:

- `RUN_ONCE`
- `SKIP`
- `RESCHEDULE`

P006 keeps scheduling portable. The platform is not tightly coupled to the current application scheduler.

## Provider Contract

Providers implement:

- `search()`
- `retrieve()`
- `fetch_metadata()`
- `extract()`
- `health_check()`

Provider descriptor fields:

- `provider_id`
- `provider_type`
- `capabilities`
- `rate_limits`
- `cost_model`
- `auth_required`
- `supports_search`
- `supports_fetch`
- `supports_documents`
- `status`
- `allowed_uri_schemes`

P006 includes a safe synthetic provider:

- `provider_id`: `synthetic-fixture`
- `provider_type`: `FIXTURE`
- role: deterministic end-to-end validation without live crawling
