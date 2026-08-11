# VEDA-P010 Index Synchronization

Promoted Core Knowledge is synchronized into the existing unified retrieval architecture rather than a parallel astrology-only index.

Implemented sync behavior:
- write approved-core retrieval docs to `veda_core_documents.jsonl`;
- feed approved-core docs into `UnifiedCorpusBuilder`;
- preserve `source_type = approved_core`;
- preserve `governed_core` freshness classification;
- track sync status with `ResearchIndexSyncRecord`.

Current runtime behavior:
- BM25 sync is exercised and verified;
- FAISS remains optional and may be skipped according to existing runtime behavior;
- index-sync failure does not erase already written authoritative core records.

P010 tests added explicit coverage for approved-core normalization and unified-corpus inclusion.
