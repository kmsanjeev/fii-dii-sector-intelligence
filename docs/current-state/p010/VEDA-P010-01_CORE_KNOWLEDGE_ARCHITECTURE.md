# VEDA-P010 Core Knowledge Architecture

P010 keeps the three-zone model intact:
- `APPROVED_CORE`
- `RESEARCH_CANDIDATE`
- `RESEARCH_ARCHIVE`

Promotion writes durable governed knowledge without deleting research history. The implementation adds:
- `ResearchPromotionPreflightRecord`
- `ResearchPromotionRecord`
- `ResearchRollbackRecord`
- `ResearchIndexSyncRecord`
- expanded `ResearchCoreKnowledgeRecord`

Authoritative storage remains split by concern:
- SQLite runtime state for promotion, rollback, and index-sync records;
- governed astrology files under `data/veda/research/astrology/*` and `data/veda/rules/approved/*` when astrology materialization is used;
- approved-core retrieval documents under `data/intelligence/rag_knowledge/veda_core_documents.jsonl`.

Approved-core retrieval classification remains distinct from:
- temporary research;
- reviewed note memory;
- attachment memory;
- predictive ML evidence;
- production astrology rule activation.
