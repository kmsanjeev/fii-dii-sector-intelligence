# Implementation inventory

| Component | Change |
|---|---|
| Existing stock router | extended in place; `/api/stocks/{symbol}` preserved |
| New helper | `backend/services/stock_intelligence.py`, bounded contract builder |
| Existing data loader | reused; no second loader or retriever |
| Sector engine | reused through existing sector-rotation dataset |
| VEDA adapter | allowlist extended for `stock_intelligence` and `contract_version` |
| ML/prediction/RAG/Jyotish | unchanged and excluded from formal stock contract |
| Tests | deterministic unit/contract coverage added |
