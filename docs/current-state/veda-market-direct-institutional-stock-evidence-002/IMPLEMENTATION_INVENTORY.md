# Implementation inventory

| Surface | Change | Status |
|---|---|---|
| `backend/services/stock_institutional_evidence.py` | additive contract 1.1, identity/provenance/date/frequency/dedup/coverage hardening | implemented |
| `/api/stocks/{symbol}` | existing nested evidence surface; no new endpoint | preserved |
| cross-layer stock confirmation | existing nested evidence surface | preserved |
| VEDA provider adapter | no code change; existing pass-through allowlist accepts nested provider fields | unchanged |
| RAG/ML/PRED/EMP | no change | unchanged |
| sector attribution | no implementation | explicitly gated |
