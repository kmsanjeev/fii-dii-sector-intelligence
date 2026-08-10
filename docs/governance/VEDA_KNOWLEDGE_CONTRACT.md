# Veda Knowledge Contract

Date: 2026-08-04
Status: Phase 0 foundation
Contract version: `2026-08-04`

## Purpose

This contract gives Veda, ML evidence, approved memory, attachment memory, and
MIT capability notes one shared shape before retrieval is unified.

Phase 0 does not change live chat behavior.
It only creates a common schema and normalization helpers so Phase 1 can build a
combined corpus safely.

## Main Rule

Storage can stay separate.
Retrieval logic can change later.
But every durable knowledge record must be able to normalize into one shared
evidence shape.

## Durable Source Types

- `platform_intelligence`
- `user_reviewed`
- `attachment_chunk`
- `mit_repo_capability`

## Required Serialized Fields

- `contract_version`
- `doc_id`
- `source_type`
- `domain`
- `entity`
- `entity_keys`
- `text`
- `summary`
- `tags`
- `saved_at`
- `effective_date`
- `freshness_class`
- `confidence`
- `provenance`
- `approval_state`
- `license_name`
- `model_version`

## Nested Structures

### `entity_keys`

Used to map the same topic across different sources.

Fields currently supported:

- `symbol`
- `sector`
- `theme`
- `topic`
- `regime`
- `intent`
- `repo_label`
- `attachment_name`
- `parent_doc_id`

### `freshness`

Used to separate dated market snapshots from durable memory or reference notes.

Fields:

- `classification`
- `effective_date`
- `saved_at`
- `note`

### `provenance`

Used to explain where Veda got the record from.

Fields:

- `source_kind`
- `source_label`
- `storage_key`
- `source_title`
- `source_url`
- `source_date`
- `repo_label`
- `license_name`
- `attachment_name`
- `attachment_storage_key`
- `attachment_hash`
- `parent_doc_id`
- `details`

## Current Normalizers

Phase 0 adds these normalizers in `engines/ai/knowledge/contracts.py`:

- `from_platform_doc(...)`
- `from_reviewed_memory(...)`
- `from_attachment_chunk(...)`
- `from_repo_capability(...)`
- `normalize_knowledge_record(...)`

## Current Mapping Rules

### Platform intelligence

- source type: `platform_intelligence`
- approval state: `system_generated`
- freshness: `dated_snapshot` when a date exists, otherwise `reference`

### Reviewed memory

- source type: `user_reviewed`
- approval state: `user_approved`
- domain prefers saved `intent` when present
- freshness: `durable_memory`

### Attachment chunk memory

- source type: `attachment_chunk`
- approval state: `user_approved`
- domain prefers saved `intent` when present
- freshness: `durable_memory`

### MIT repo capability notes

- source type: `mit_repo_capability`
- approval state: `user_approved`
- license is carried into the normalized record
- freshness: `reference`

## Explicit Non-Goals In Phase 0

- no unified retriever yet
- no reranking changes yet
- no chat prompt changes yet
- no production answer-format changes yet

## Why This Matters

Without this contract, Veda keeps growing as separate memory systems.

With this contract:

- Phase 1 can build a combined corpus
- Phase 2 can replace split retrieval cleanly
- ML evidence, RAG documents, and approved memory can later be compared and
  ranked through the same pipeline

## Phase 1 Follow-Up

On 2026-08-04, the contract started feeding a combined durable corpus through
`engines/ai/knowledge/unified_corpus_builder.py`.

That builder keeps source files separate but emits:

- `veda_unified_documents.jsonl`
- `veda_unified_manifest.json`
- `veda_unified_metadata.csv`

## Phase 2 Follow-Up

On 2026-08-04, the unified contract also started feeding:

- `veda_unified_bm25_index.pkl`
- `veda_unified_faiss/`

These assets back the new unified retriever used by chat.
