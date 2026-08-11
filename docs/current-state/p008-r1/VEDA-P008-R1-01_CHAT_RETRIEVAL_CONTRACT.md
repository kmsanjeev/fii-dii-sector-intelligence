# VEDA-P008-R1 Chat Retrieval Contract

Status: Accepted  
Decision Date: August 11, 2026

## Decision

The authoritative chat retrieval contract after P008 is:

| Area | Contract |
| --- | --- |
| Retrieval primary mode | `unified` when `VEDA_UNIFIED_RETRIEVAL_ENABLED=true`; otherwise `legacy` |
| Unified retrieval behavior | `ChatEngine` calls `UnifiedHybridRetriever.build_context_bundle()` when available and records `last_local_evidence` from the returned summary |
| Legacy retrieval behavior | `ChatEngine` builds a legacy bundle from reviewed memory, approved MIT capability notes, and the legacy platform retriever using `build_legacy_bundle()` |
| Shadow mode | When `VEDA_UNIFIED_RETRIEVAL_SHADOW_ENABLED=true`, the non-primary retrieval mode runs as a shadow path for audit only; `last_retrieval_audit` records overlap, attribution quality, and source deltas |
| Shadow log | When `VEDA_UNIFIED_RETRIEVAL_SHADOW_WRITE_LOG=true`, `append_shadow_audit()` writes a JSONL audit record |
| Local evidence metadata | `last_local_evidence` must expose source counts, evidence kinds, predictive-ML counts, top date, conflict note, freshness note, and normalized source references |
| Temporary external research | External research remains source content only, not instructions; it stays temporary until reviewed/saved and is returned via `last_research.temporary=true` and `save_requires_review=true` |
| Reviewed/core knowledge boundary | Approved memory and attachment memory remain local evidence only; chat may use them for answering but may not silently promote new research into approved knowledge |
| Conflict handling | Chat surfaces governed `ResearchResult.conflict_note` when present; otherwise it may emit a narrow per-turn memory-vs-external conflict note for answer framing only |
| ML/evidence separation | Predictive ML signals must be labeled as scored/predictive evidence, not confirmed fact; saved memory, attachments, and external research must not be described as changing the ML model |
| History bounding | Each message is clipped to `VEDA_CHAT_MAX_MESSAGE_CHARS`; retained history is limited by `VEDA_CHAT_MAX_HISTORY_MESSAGES` and `VEDA_CHAT_MAX_HISTORY_CHARS` |
| Voice-mode invocation | `chat()` always invokes `_run_turn(..., voice_mode=...)`; internal doubles and compatibility shims must accept the keyword |

## Consequences

- `ChatEngine` is the authoritative place where retrieval mode selection, temporary research framing, and per-turn metadata are assembled.
- The FastAPI chat router can treat `last_local_evidence`, `last_retrieval_audit`, and `last_research` as stable response metadata.
- P009 external research activation can proceed against a documented trust boundary instead of an ambiguous legacy chat path.
