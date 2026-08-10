# Veda Unified ML-RAG Plan

Date: 2026-08-04
Status: Phase 7 implementation complete with save-sync hardening
Scope: Veda chat layer, approved memory, MIT capability memory, core RAG, ML-to-chat evidence flow, research-mode governance

## Implementation Update - Save Sync Hardening Completed On 2026-08-04

- Approved reviewed-memory saves and approved MIT capability saves now trigger
  immediate unified runtime sync after a real save or merge.
- The runtime sync now refreshes:
  - unified durable corpus
  - unified BM25
- Save-time unified FAISS rebuild is now optional and disabled by default.
- This keeps the review/save path fast while still fixing the earlier problem
  where approved durable knowledge could exist on disk but not yet be visible
  to the unified retriever.
- Focused validation completed on 2026-08-04:
  - `python -m pytest tests/test_veda_unified_runtime_sync.py -q` -> `3 passed`
  - `python -m pytest tests/test_veda_knowledge_review_service.py tests/test_veda_repo_capability_service.py -q` -> `15 passed`
  - `python -m pytest tests/test_veda_knowledge_contract.py tests/test_veda_unified_corpus_builder.py -q` -> `8 passed`

## Implementation Update - Phase 7 Completed On 2026-08-04

- Outside research now carries explicit governance metadata:
  - temporary by default
  - review required before save
  - optional conflict note
  - plain governance note
- Veda now checks whether outside research conflicts with saved memory already stored in the system.
- When that conflict exists, Veda now tells the user plainly instead of silently overriding the saved memory.
- Approved reviewed memory now preserves research provenance in retrievable metadata, including:
  - source title
  - source URL
  - published date
  - excerpt
  - latest research date
- The unified knowledge contract now carries that research provenance forward through reviewed-memory normalization.
- The evidence panel and save-review panel now remind the user that outside research is temporary until approval.
- Focused validation completed on 2026-08-04:
  - `python -m pytest tests/test_veda_knowledge_review_service.py tests/test_veda_knowledge_contract.py tests/test_veda_chat_engine.py tests/test_veda_chat_router.py` -> `32 passed`
  - `npm.cmd run test -- MessageEvidence KnowledgeReviewPanel` -> `7 passed`
  - `npx.cmd tsc --pretty false --noEmit -p tsconfig.app.json` -> passed
  - `python -m py_compile engines/ai/research/schemas.py engines/ai/chatbot/chat_engine.py engines/ai/knowledge/review_service.py engines/ai/knowledge/contracts.py backend/routers/chat.py` -> passed

## Implementation Update - Phase 5 Completed On 2026-08-04

- Veda's unified local evidence bundle now preserves user-readable source references for the top ranked results.
- Each local source reference now carries:
  - source label
  - evidence label
  - domain
  - date
  - short summary
  - model/version details when the evidence is predictive ML
- Veda now stores those local source references inside chat responses and saved chat history, so the source trail survives in previous chats.
- The evidence panel now shows:
  - local source cards
  - local conflict notes
  - freshness notes
  - model and reliability details where relevant
- Local conflict detection now warns when top evidence for the same entity points in opposite directions.
- Local freshness detection now warns when the answer mixes different source dates or combines dated platform signals with saved memory.
- Focused validation completed on 2026-08-04:
  - `python -m pytest tests/test_veda_unified_retriever.py tests/test_veda_chat_engine.py tests/test_veda_chat_router.py` -> `19 passed`
  - `npm.cmd run test -- MessageEvidence` -> `3 passed`
  - `npx.cmd tsc --pretty false --noEmit -p tsconfig.app.json` -> passed

## Implementation Update - Phase 4 Completed On 2026-08-04

- Veda now receives local evidence with explicit meaning:
  - predictive ML signal
  - platform snapshot
  - approved memory
  - attachment memory
  - MIT capability note
- ML-heavy stock evidence now carries:
  - model name
  - model version
  - feature date
  - score meaning
  - reliability note
- The unified retriever and chat prompt now force a clean separation between:
  - predictive ML output
  - descriptive retrieved knowledge
  - user-approved memory
  - uploaded-file memory
- The frontend evidence panel now tells the user when local ML signals were part of the answer basis.
- Local runtime sync was completed on 2026-08-04 by rebuilding the platform docs, unified corpus, BM25 index, and FAISS indexes.
- Focused validation completed on 2026-08-04:
  - `python -m pytest tests/test_veda_knowledge_contract.py tests/test_veda_unified_corpus_builder.py tests/test_veda_unified_retriever.py tests/test_veda_chat_engine.py tests/test_veda_chat_router.py` -> `26 passed`
  - `npm.cmd run test -- MessageEvidence KnowledgeReviewPanel` -> `5 passed`

## Implementation Update - Phase 3 Completed On 2026-08-04

- Veda reviewed memory now has three user-confirmed outcomes:
  - `discard` when the content is effectively already saved
  - `merge` when the topic already exists but the new draft adds useful value
  - `save` when the draft should remain a separate memory
- The frontend review panel and backend approval API now carry an explicit decision, so recommendation and user action stay separate.
- This keeps the Veda frontend face aligned with the reviewed-memory layer underneath it.
- Focused validation completed on 2026-08-04:
  - `python -m pytest tests/test_veda_knowledge_review_service.py tests/test_veda_chat_router.py` -> `17 passed`
  - `npm.cmd run test -- KnowledgeReviewPanel` -> `2 passed`

## Executive Summary

Veda should not be treated as a simple frontend over ML and RAG.
Veda is the orchestration layer that decides which evidence to use, how to rank it, how to explain it, and what can be saved as durable memory.

The current system is functional but split:

- base platform intelligence uses hybrid BM25 + FAISS retrieval
- approved user memory uses lexical matching only
- approved MIT repo capability memory uses lexical matching only
- chat joins these sources at prompt time instead of ranking them as one shared knowledge system

This plan fixes that in one coordinated program while keeping current functionality stable through feature flags and shadow testing.

## Core Correction

All three layers must work together, but they should not be merged blindly.

- ML should remain the structured scoring and prediction layer
- RAG should remain the document and evidence retrieval layer
- Veda should remain the reasoning, explanation, citation, and approval layer

Uploaded books and approved memory should improve retrieval quality.
They should not directly retrain ML models unless they are later converted into a valid labeled dataset for a specific model.

## Problems To Solve

1. Knowledge is split across multiple stores and is not ranked together.
2. Approved memory and MIT capability notes rely on keyword overlap, not semantic meaning.
3. Chat context assembly is prompt-side concatenation, not unified evidence retrieval.
4. ML outputs inform RAG text, but ML, RAG, and chat do not share one evidence contract.
5. Source traceability is not strong enough for a serious long-term knowledge system.
6. Retrieval quality is tested functionally, but not benchmarked for relevance quality.
7. Older ASTRO book-ingestion code still exists separately and should be formally retired or migrated.

## Target Architecture

The target state is one evidence pipeline with separate governance stores.

- Separate storage remains for:
  - platform intelligence documents
  - approved user memory
  - approved attachment chunks
  - approved MIT capability notes
  - temporary external research cache
- One shared retrieval layer searches all approved durable sources together
- One evidence assembler returns ranked results with provenance, freshness, and confidence
- One answer composer decides how Veda presents ML facts, retrieved memory, uploaded-file content, and research evidence

## Unified Data Contract

Every retrievable item should expose the same minimum fields:

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
- `license_name` when relevant
- `model_version` when produced by ML

This contract lets ML outputs, RAG documents, reviewed memory, and MIT capability notes behave like one system without losing source identity.

## Execution Plan

### Phase 0 - Freeze The Knowledge Contract

Goal: define one schema before changing retrieval.

Work:

- create a shared schema for all durable knowledge records
- map current stores into that schema without changing user behavior
- define `source_type` values such as `platform_intelligence`, `user_reviewed`, `attachment_chunk`, `mit_repo_capability`, and `external_research`
- define `entity_keys` for stock, sector, theme, astro topic, and free-form research topic
- document which fields are mandatory, optional, derived, and user-facing

Exit criteria:

- one schema document is approved
- current stores can be normalized into the same shape

### Phase 1 - Build A Unified Knowledge Corpus

Goal: keep separate source files, but generate one retrievable corpus.

Work:

- build a corpus builder that reads:
  - `documents.jsonl`
  - `veda_reviewed_documents.jsonl`
  - `veda_capability_documents.jsonl`
- create a normalized combined corpus manifest
- preserve source-specific metadata and approval history
- add exact-duplicate detection across sources
- define a migration decision for old ASTRO direct-ingestion content:
  - migrate into normalized corpus
  - or retire the old path formally

Exit criteria:

- one combined approved corpus exists
- no current feature is removed

### Phase 2 - Replace Split Retrieval With One Unified Retriever

Implementation status:

Complete on 2026-08-04.
Unified BM25, unified FAISS, and a unified hybrid retriever now exist, and the
chat engine prefers that path with automatic fallback to the older split
retrieval route.

Goal: stop stitching three unrelated searches together inside chat.

Work:

- replace prompt-side context concatenation with a dedicated unified retriever
- Stage 1 recall:
  - BM25 across combined corpus
  - FAISS across combined corpus
- Stage 2 ranking:
  - reciprocal rank fusion as baseline
  - source-aware weighting
  - freshness weighting
  - confidence weighting
  - optional reranker after baseline is stable
- return one ranked evidence list instead of three disconnected blocks

Exit criteria:

- Veda gets one ordered evidence bundle for each query
- base RAG, approved memory, and MIT capability notes compete together fairly

### Phase 3 - Upgrade Memory Intelligence

Goal: make approved memory behave like smart memory, not simple note storage.

Work:

- replace keyword-only duplicate detection with semantic similarity plus content fingerprinting
- support three memory decisions for overlapping content:
  - discard duplicate
  - save as new because it adds value
  - merge with existing memory
- let Veda suggest the recommended action, but require user approval for permanent save
- rank richer, newer, and better-sourced memory above thinner old notes

Exit criteria:

- Veda can explain why it recommends save, merge, or discard
- same-topic books no longer create noisy duplicate memory by default

### Phase 4 - Sync ML With Retrieval Properly

Goal: connect ML and RAG through evidence, not through blind mixing.

Work:

- keep ML models independent from uploaded books and general document memory
- expose ML outputs as evidence records with:
  - model name
  - model version
  - feature date
  - score meaning
  - reliability notes
- ensure Veda can answer:
  - what came from ML
  - what came from retrieved documents
  - what came from user-approved memory
- prevent document memory from being mistaken for model truth

Exit criteria:

- Veda can separate predictive evidence from descriptive knowledge in every serious answer

### Phase 5 - Add Strong Source Grounding

Implementation status:

Complete on 2026-08-04.
Local source references, conflict notes, freshness notes, and saved-history
evidence preservation now flow through the unified retrieval path, chat API,
and React evidence panel.

Goal: make answers auditable and easier to trust.

Work:

- carry source IDs and short source labels into the answer pipeline
- show whether a statement came from:
  - local platform intelligence
  - uploaded file memory
  - approved memory note
  - MIT capability note
  - external research
- attach dates where freshness matters
- add conflict reporting when sources disagree

Exit criteria:

- user can understand where the answer came from in plain language
- chat history can preserve evidence references

### Phase 6 - Research Mode Governance

Implementation status:

Complete on 2026-08-04.
Outside research is now explicitly temporary by default, reviewed-memory
records preserve research provenance, and Veda now raises a plain conflict
note when outside research and saved memory disagree.

Goal: keep research helpful without polluting memory.

Work:

- keep external research temporary by default
- save research-derived knowledge only through the same approval flow
- store research source title, URL, date, and excerpt in provenance
- when research conflicts with saved memory, Veda must say so instead of silently overriding local memory

Exit criteria:

- research improves answers without silently becoming permanent memory

### Phase 7 - Evaluation, Shadow Mode, And Rollout

Implementation status:

Complete on 2026-08-04.
Unified retrieval now has a real benchmark fixture, a benchmark runner, a
shadow-mode comparison path against the older stitched retrieval flow, and a
retrieval-audit record on the chat API so rollout stays measurable and
reversible.

Goal: improve quality without breaking current behavior.

Work:

- build a benchmark set of real Veda questions across:
  - market
  - sector
  - stock
  - astrology
  - uploaded-book recall
  - MIT capability reuse
  - research-mode freshness
- measure retrieval quality before and after:
  - hit rate
  - top-k relevance
  - duplicate noise
  - source attribution quality
- run unified retrieval in shadow mode first
- compare old and new evidence bundles before cutover
- release behind feature flags

Exit criteria:

- new stack beats or matches the current stack on benchmark queries
- rollout is reversible

## Suggested Build Order

Do not implement this as one giant release.

Use one architecture plan, one benchmark suite, and one cutover goal.
But ship it in this order:

1. schema and corpus normalization
2. unified retriever in shadow mode
3. memory intelligence upgrade
4. ML evidence sync
5. source-grounded answer layer
6. research governance alignment
7. production cutover

## Non-Negotiable Guardrails

- no permanent save without explicit approval
- no direct ML retraining from uploaded books
- no silent replacement of existing memory
- no loss of current chat functionality during migration
- no external research treated as durable truth unless reviewed and approved

## Main Contradiction To The Current Thinking

The statement "Veda is the frontend face of ML and RAG" is incomplete.

The more correct statement is:

Veda is the decision layer above ML, RAG, reviewed memory, attachment understanding, and research evidence.

If Veda is treated as just a frontend, the system will keep growing sideways.
If Veda is treated as the orchestration and evidence-governance layer, the platform can scale cleanly.

## Expected Outcome

After this program:

- Veda will search all approved durable knowledge through one ranked evidence path
- uploaded books will improve memory quality without pretending to retrain ML
- ML outputs and retrieved documents will support each other without being confused with each other
- answers will become more explainable, more traceable, and less noisy
- future growth like research mode, domain expansion, and capability reuse will become easier

## Phase 0-1 Execution Roadmap

This section converts the plan above into a practical implementation sequence.

### Phase 0 - Knowledge Contract Freeze

Objective:

Define one shared evidence schema before changing retrieval behavior.

Implementation status:

Complete on 2026-08-04.
Shared contract code now lives in `engines/ai/knowledge/contracts.py`, with
focused normalization coverage in `tests/test_veda_knowledge_contract.py`.

Why this phase matters:

If retrieval is changed before the schema is fixed, the project will create more adapters, more special cases, and more technical debt.

Suggested new files:

- `engines/ai/knowledge/contracts.py`
- `docs/governance/VEDA_KNOWLEDGE_CONTRACT.md`

Suggested files to update:

- `engines/common/config.py`
- `engines/ai/knowledge/document_builder.py`
- `engines/ai/knowledge/review_service.py`
- `engines/ai/capabilities/service.py`
- `docs/PROJECT_MASTER_STATE.md`
- `docs/governance/CHANGELOG.md`

What to build in Phase 0:

1. Create shared dataclasses or typed schemas for:
   - `KnowledgeEvidenceRecord`
   - `KnowledgeProvenance`
   - `KnowledgeFreshness`
   - `KnowledgeEntityKeys`

2. Define normalized fields for all durable knowledge:
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

3. Add normalizer helpers:
   - `from_platform_doc(...)`
   - `from_reviewed_memory(...)`
   - `from_attachment_chunk(...)`
   - `from_repo_capability(...)`

4. Do not change chat retrieval yet.
   Phase 0 is contract work only.

Implementation order:

1. Add new schema file with strict field names and defaults.
2. Add one contract document in docs with plain-language meanings.
3. Add translation helpers for current source formats.
4. Add small unit tests for schema normalization only.
5. Update governance docs.

Phase 0 test targets:

- new test file:
  - `tests/test_veda_knowledge_contract.py`
- extend if needed:
  - `tests/test_veda_knowledge_review_service.py`
  - `tests/test_veda_repo_capability_service.py`

Phase 0 success criteria:

- all existing durable stores can be normalized without losing source identity
- no chat behavior changes yet
- no retrieval quality regression risk introduced

Phase 0 non-goals:

- no unified retriever yet
- no ranking logic changes yet
- no frontend behavior changes yet

### Phase 1 - Unified Corpus Builder

Objective:

Generate one combined approved corpus from all durable knowledge sources while keeping their original storage paths intact.

Implementation status:

Complete on 2026-08-04.
The unified durable corpus builder now lives in
`engines/ai/knowledge/unified_corpus_builder.py` and emits combined documents,
manifest, and metadata artifacts without changing live chat retrieval.

Why this phase matters:

The main problem today is not only the schema.
It is that Veda searches different knowledge stores in different ways.
Phase 1 creates the common searchable foundation without yet forcing production cutover.

Suggested new files:

- `engines/ai/knowledge/unified_corpus_builder.py`
- `engines/ai/knowledge/unified_manifest.py`

Suggested files to update:

- `engines/common/config.py`
- `engines/ai/knowledge/index_updater.py`
- `docs/PROJECT_MASTER_STATE.md`
- `docs/governance/CHANGELOG.md`

Suggested new output artifacts:

- `data/intelligence/rag_knowledge/veda_unified_documents.jsonl`
- `data/intelligence/rag_knowledge/veda_unified_manifest.json`
- `data/intelligence/rag_knowledge/veda_unified_metadata.csv`

What to build in Phase 1:

1. Read and normalize these inputs:
   - `data/intelligence/rag_knowledge/documents.jsonl`
   - `data/intelligence/rag_knowledge/veda_reviewed_documents.jsonl`
   - `data/intelligence/rag_knowledge/veda_capability_documents.jsonl`

2. Convert all records into the Phase 0 contract.

3. Preserve source boundaries through metadata:
   - `source_type`
   - `approval_state`
   - `license_name`
   - `parent_doc_id`
   - `attachment_hash`
   - `repo_label`

4. Build a manifest that reports:
   - record count by source
   - record count by domain
   - duplicates by exact hash
   - missing critical fields
   - contract-version used

5. Decide the old ASTRO ingestion path:
   - either map it into the unified corpus
   - or formally retire it in docs and code comments

Implementation order:

1. Add config paths for unified corpus outputs.
2. Build unified corpus builder using only existing source files.
3. Add validation rules for required fields.
4. Emit manifest and metadata outputs.
5. Hook corpus build into `index_updater.py` after current source generation, but before any future unified indexing work.
6. Keep current chat retrieval untouched in this phase.

Phase 1 test targets:

- new test file:
  - `tests/test_veda_unified_corpus_builder.py`
- regression tests:
  - `tests/test_veda_knowledge_review_service.py`
  - `tests/test_veda_repo_capability_service.py`

Phase 1 success criteria:

- one combined durable corpus is generated successfully
- source provenance remains visible
- current chat answers still behave exactly as before
- unified corpus can be inspected independently before retrieval cutover

Phase 1 non-goals:

- no replacement of `HybridRetriever` yet
- no production ranking changes yet
- no answer-format changes yet

### Recommended Delivery Strategy

Do not start by changing `chat_engine.py`.

Start with stable backend assets first:

1. contract
2. normalizers
3. unified corpus builder
4. manifest validation
5. only then move to unified retrieval in the next phase

This keeps risk low because the existing chat path remains untouched while the new foundation is built and inspected.

### My Clear Suggestion

If the goal is to fix everything properly, the right first move is not "make Veda smarter" at the prompt level.

The right first move is:

- freeze the evidence contract
- build one combined corpus
- inspect it
- then replace retrieval

That is the cleanest way to sync Veda, ML evidence, and RAG without damaging the current application.
