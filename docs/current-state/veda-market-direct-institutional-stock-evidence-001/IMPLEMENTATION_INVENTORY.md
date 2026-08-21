# Implementation inventory

| Component | Change | Reuse boundary |
|---|---|---|
| `backend/services/stock_institutional_evidence.py` | New authoritative bounded contract service | Reuses `data_loader` and canonical identity passed by stock intelligence |
| `backend/services/stock_intelligence.py` | Delegates institutional context to authoritative service; adds nested evidence | Existing `stock-intelligence-1.1` contract retained |
| `backend/services/cross_layer_intelligence.py` | Exposes the per-stock evidence contract in summaries | Existing cross-layer composition retained |
| VEDA adapter | No schema-specific code needed; existing `stock_intelligence` allowlist passes nested provider-owned contract | Routing/authorization remains VEDA-owned |

No new provider, retriever, database, ML, LLM, prediction, RAG, identity,
subscription or Jyotish capability was created.
