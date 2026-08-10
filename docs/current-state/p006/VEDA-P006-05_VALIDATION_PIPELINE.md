# VEDA-P006 Validation Pipeline

Date baseline: `2026-08-10`

P006 implements a generic staged validation pipeline in `ResearchPlatformService._apply_validations(...)`.

Validation stages:

- `V1_SOURCE_VALIDATION`
- `V2_AUTHORITY_VALIDATION`
- `V3_PROVENANCE_VALIDATION`
- `V4_EXISTING_KNOWLEDGE_CHECK`
- `V5_CONTRADICTION_CHECK`
- `V6_CROSS_SOURCE_SUPPORT`
- `V7_ONTOLOGY_COMPATIBILITY`
- `V8_RULE_IMPACT`
- `V9_SAFETY_CLASSIFICATION`
- `V10_NOVELTY_ASSESSMENT`

Validation outputs are stored as `ResearchValidationRecord` with:

- `validation_id`
- `candidate_id`
- `validator`
- `result`
- `score`
- `status`
- `evidence`
- `reason`
- `requires_follow_up`
- `created_at`

Supported validation statuses:

- `PASS`
- `PASS_WITH_CONDITIONS`
- `FAIL`
- `UNKNOWN`
- `NOT_APPLICABLE`

Confidence is deliberately multi-dimensional, not one opaque score:

- `source_confidence`
- `authority_confidence`
- `cross_source_confidence`
- `provenance_confidence`
- `novelty_confidence`
- `contradiction_confidence`
- `domain_confidence`

Synthetic pilot behavior:

- `alpha` advanced from `PENDING` to `APPROVED` after two supporting evidence records
- `beta` remained directly contradictory to approved core and was rejected
- `delta` stayed `PASS_WITH_CONDITIONS` and generated follow-up research
