# VEDA-P006 Evidence and Candidate Model

Date baseline: `2026-08-10`

P006 keeps source observations, extracted evidence, and reviewable candidates as separate artifacts.

## Source Observation

`SourceObservationRecord` captures:

- provider
- source URI and canonical URI
- title, publisher, author
- timestamps
- content hash
- access status
- trust metadata
- domain metadata

Observation status values:

- `ACCEPTED`
- `REJECTED`
- `UNAVAILABLE`
- `UNSAFE`

## Evidence

`ResearchEvidenceRecord` captures:

- one extracted passage or observation fragment
- normalized text
- claim hint
- evidence type
- extraction method
- confidence
- mission/run/domain lineage

Evidence types supported by core contracts:

- `PRIMARY_SOURCE`
- `SECONDARY_SOURCE`
- `OFFICIAL_DOCUMENT`
- `ACADEMIC_SOURCE`
- `NEWS`
- `DATASET`
- `WEB_REFERENCE`
- `INTERNAL_KNOWLEDGE`
- `ARCHIVED_RESEARCH`
- `USER_PROVIDED`
- `UNKNOWN`

## Candidate

`ResearchCandidateRecord` is the reviewable, non-authoritative knowledge unit.

Important fields:

- `candidate_id`
- `candidate_type`
- `claim`
- `normalized_claim`
- `topic_key`
- `stance`
- `evidence_ids`
- `existing_knowledge_matches`
- `novelty_status`
- `contradiction_status`
- `validation_status`
- `confidence`
- `approval_status`
- `knowledge_zone`
- `promotion_state`
- `support_count`

Candidate types supported:

- `NEW_CLAIM`
- `CLAIM_UPDATE`
- `SOURCE_ADDITION`
- `SOURCE_CORRECTION`
- `CONTRADICTION`
- `RULE_CANDIDATE`
- `PROVENANCE_CANDIDATE`
- `KNOWLEDGE_GAP`
- `DEPRECATION_CANDIDATE`
- `EMPIRICAL_FINDING`

Deduplication behavior:

- candidates are keyed by normalized claim identity and topic context
- additional evidence strengthens the same candidate instead of creating queue spam
- the synthetic pilot demonstrates this with the second `alpha` evidence item
