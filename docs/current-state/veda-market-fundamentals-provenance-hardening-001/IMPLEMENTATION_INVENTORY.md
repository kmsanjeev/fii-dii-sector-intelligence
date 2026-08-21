# Implementation inventory

| Component | Change |
|---|---|
| `backend/services/fundamental_evidence.py` | New bounded field-level provenance and period contract |
| `backend/services/stock_intelligence.py` | Additive nested evidence and field-level availability |
| `backend/services/cross_layer_intelligence.py` | Pass evidence through and expose its quality in stock freshness |
| Existing engines | No raw/derived dataset rewrite in this activity |
| Identity | Reuses existing stock identity and master lookup |
| RAG/ML/PRED/EMP | Unchanged |
