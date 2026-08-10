# VEDA-P006 Domain Plugin Standard

Date baseline: `2026-08-10`

P006 keeps domain knowledge out of the research core. The generic platform depends on the abstract `ResearchDomainPlugin` contract in `engines/ai/research/platform/contracts.py`.

Required plugin responsibilities:

- `normalize_candidate(...)`
- `validate_source(...)`
- `compare_to_core(...)`
- `detect_domain_conflict(...)`
- `classify_safety(...)`
- `create_follow_up(...)`

Domain registry fields are represented by `ResearchDomainRecord`:

- `domain_id`
- `name`
- `version`
- `status`
- `description`
- `ontology_namespace`
- `source_policy`
- `validation_policy`
- `safety_policy`
- `approval_policy`
- `provider_policy`
- `schedule_policy`
- `plugin_entrypoint`

Supported domain status values:

- `DISABLED`
- `TEST`
- `ACTIVE`
- `PAUSED`
- `RETIRED`

P006 tracked test domain:

- `domain_id`: `VEDA-DOMAIN-SYNTHETIC`
- `status`: `TEST`
- purpose: prove platform behavior without activating live autonomous astrology research

P007 can implement a Vedic Astrology adapter against this contract without rewriting the platform core.
