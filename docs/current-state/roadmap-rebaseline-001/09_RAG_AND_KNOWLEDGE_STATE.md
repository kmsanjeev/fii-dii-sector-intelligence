# RAG and Knowledge State

Observed manifest: `data/intelligence/rag_knowledge/veda_unified_manifest.json`.

| Metric | Value |
|---|---:|
| Unified documents | 1,205 |
| Platform documents | 1,091 |
| Approved Core documents | 17 |
| Research-tier documents | 94 |
| Reviewed-memory documents | 2 |
| Duplicate records | 0 |
| Missing critical fields | 0 |
| Trust-zone entries | APPROVED_CORE 17; VALIDATED_KNOWLEDGE 3; RESEARCH_CANDIDATE 86; EXPERIMENTAL 7; RESEARCH_ARCHIVE 1; ML_EVIDENCE 500; PLATFORM_EVIDENCE 591 |

Roadmap and governance metadata changed only in this activity. No semantic
knowledge document changed, so no `scripts/rebuild_unified_rag.py` run was
required. Existing unified artifacts remain deterministic and trust-zone
correct. Approved Core count remained 17; autonomous promotions were 0.
