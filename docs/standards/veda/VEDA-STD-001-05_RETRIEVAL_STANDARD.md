# Retrieval Standard

`UnifiedCorpusBuilder` preserves `VEDA-RAG-GEN-001-R` and now adds existing research-tier records to the unified corpus. `UnifiedHybridRetriever` supports `PRODUCTION_SAFE`, `RESEARCH`, `SHADOW`, `BACKTEST`, and `ADMIN_AUDIT` modes.

Research and shadow modes retrieve Approved Core, validated knowledge, candidates, experiments, archives, ML evidence, and platform evidence while preserving trust labels. Production-safe mode excludes unqualified research tiers from ordinary answers. Domain relevance and platform down-ranking prevent governance metadata from dominating Jyotisha answers.
