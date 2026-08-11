# VEDA-P008-R1 Retrieval Reconciliation

## Before

`ChatEngine` had drifted behind the rest of the repository:

- it still pulled local context directly from the legacy `HybridRetriever`;
- it did not populate `last_local_evidence`;
- it did not populate `last_retrieval_audit`;
- it had no shadow-mode comparison path;
- the chat prompt did not restate the reviewed-save boundary for attachments;
- research conflict signalling stopped at `ResearchResult.conflict_note`, leaving the chat layer blind when only local saved memory exposed the contradiction.

## After

`ChatEngine` now follows the same retrieval vocabulary already used by the router and unified retriever:

1. `unified` mode
   - uses `UnifiedHybridRetriever.build_context_bundle()`;
   - returns the unified context block directly to the system prompt;
   - preserves summary metadata in `last_local_evidence`.

2. `legacy` mode
   - combines reviewed memory, approved MIT capability notes, and legacy platform retrieval through `build_legacy_bundle()`;
   - normalizes the result into the same local-evidence summary shape.

3. shadow mode
   - runs the non-primary retrieval path for comparison;
   - records overlap, source deltas, attribution quality, duplicate noise, and errors in `last_retrieval_audit`;
   - optionally appends a JSONL shadow log.

4. external research context
   - remains temporary and non-instructional;
   - now carries a compatibility conflict note when fresh external evidence materially disagrees with saved reviewed memory.

## Scope Control

No kundli calculation, ontology, approval, promotion, or production knowledge path was changed. The reconciliation is confined to chat retrieval assembly, per-turn metadata, and bounded provider/runtime behavior.
