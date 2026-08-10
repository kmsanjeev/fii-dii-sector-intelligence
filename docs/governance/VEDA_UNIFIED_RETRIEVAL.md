# Veda Unified Retrieval

Date: 2026-08-04
Status: Phase 7 rollout controls complete plus save-sync hardening

## Purpose

This phase replaces the old chat-time stitching model with one ranked local
evidence path.

Before Phase 2:

- reviewed memory was searched separately
- MIT capability notes were searched separately
- base platform RAG was searched separately
- chat combined those blocks in the prompt

After Phase 2:

- a unified corpus is indexed through unified BM25 and unified FAISS
- one retriever ranks all approved local evidence together
- chat prefers the unified retriever first
- chat still falls back to the old split path if unified assets are missing

## New Runtime Assets

- `data/intelligence/rag_knowledge/veda_unified_bm25_index.pkl`
- `data/intelligence/rag_knowledge/veda_unified_faiss/`

## New Backend Modules

- `engines/ai/knowledge/unified_bm25_indexer.py`
- `engines/ai/knowledge/unified_faiss_indexer.py`
- `engines/ai/knowledge/unified_retriever.py`
- `engines/ai/knowledge/retrieval_rollout.py`
- `engines/ai/knowledge/retrieval_benchmark.py`
- `engines/ai/knowledge/unified_runtime_sync.py`

## Save-Time Sync Hardening

The first rollout benchmark exposed a practical gap:

- approved knowledge could be written correctly
- but unified retrieval would not see it until a later manual or scheduled
  rebuild refreshed the shared corpus and indexes

That gap is now closed for the fast path.

After an approved reviewed-memory save, merge, or approved MIT capability save:

- unified corpus refresh runs immediately
- unified BM25 refresh runs immediately

This makes newly approved durable knowledge searchable right away through the
primary unified retrieval path.

Unified FAISS rebuild on save is now controlled separately:

- `VEDA_UNIFIED_RETRIEVAL_SYNC_ON_SAVE`
  - master switch for immediate unified refresh after approval
- `VEDA_UNIFIED_FAISS_SYNC_ON_SAVE`
  - defaults to `false` so user-facing save/review flows stay fast
- `VEDA_UNIFIED_FAISS_LOCAL_ONLY_ON_SAVE`
  - when FAISS-on-save is enabled, prevents save-time model download attempts

This means the normal user path now prefers:

- immediate corpus + BM25 freshness
- optional later FAISS refresh through the scheduled full index pipeline

That tradeoff is intentional because save/review lives on the chat path and
cannot block on a full semantic rebuild.

## Chat Behavior

`engines/ai/chatbot/chat_engine.py` now tries unified retrieval first when
`VEDA_UNIFIED_RETRIEVAL_ENABLED=true`.

If unified retrieval cannot run, Veda falls back to the old path:

- reviewed memory service
- MIT capability service
- legacy hybrid retriever

This keeps the rollout reversible and safe.

## Phase 7 Rollout Controls

Phase 7 added the control layer around that retrieval switch:

- `VEDA_UNIFIED_RETRIEVAL_SHADOW_ENABLED`
  - runs the non-primary path in parallel for comparison
- `VEDA_UNIFIED_RETRIEVAL_SHADOW_WRITE_LOG`
  - optionally writes shadow audit records to
    `data/veda/retrieval_audits/veda_unified_shadow_runs.jsonl`
- `docs/governance/fixtures/veda_unified_retrieval_benchmark.json`
  - committed benchmark cases for the main Veda question families

`/api/chat` now also returns retrieval-audit metadata so tests and rollout
checks can see:

- which path was configured as primary
- which path actually answered
- how many sources overlapped
- where only one path found relevant evidence
- whether attribution quality or duplicate noise favored one side

## First Local Benchmark Snapshot

On 2026-08-04, the first local benchmark report was written to:

- `data/veda/retrieval_audits/benchmark_reports/latest_report.json`

Current summary from that run:

- unified hit rate: `0.857`
- legacy hit rate: `0.714`
- unified top-k relevance: `0.679`
- legacy top-k relevance: `0.607`
- unified source attribution quality: `1.000`
- legacy source attribution quality: `0.833`
- duplicate noise: tied at `0.000`

One content gap still remains visible in the report:

- the astrology-memory benchmark case missed on both paths with the current
  local corpus, so that is still a knowledge coverage problem rather than a
  rollout-control problem

## Ranking Rules In Phase 2

Current ranking approach:

- unified BM25 recall
- unified FAISS recall
- reciprocal rank fusion
- small post-rank boosts for:
  - matching requested domain
  - file-memory style queries
  - MIT repo capability queries
  - freshness-heavy queries

This is a practical bridge design.
It is better than prompt-side stitching, but it is not yet the final reranker
architecture.
