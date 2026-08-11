# Approved-Core RAG Architecture

Authoritative approved-core retrieval now uses:
- runtime research store current core records
- promoted-source lineage from P010
- P002 source, passage, claim, and conflict artifacts
- P003 approved-rule artifacts where linked

Flow:
- query
- ontology expansion
- approved-core current-version search
- authority and version aware scoring
- conflict enrichment
- citation enrichment
- unified retrieval fusion
- chat/admin diagnostics consumption

The implementation reuses the existing unified retrieval stack instead of creating an isolated astrology-only RAG subsystem.
