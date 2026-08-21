# Implementation inventory

| File | Role |
|---|---|
| `backend/services/cross_layer_intelligence.py` | FII-owned composition contract and bounded discovery |
| `backend/routers/market.py` | One public cross-layer endpoint |
| `platform/app/providers/market_intelligence.py` | VEDA formal capability and query validation |
| `platform/app/experience/routing.py` | Bounded natural-language mode routing |
| `platform/app/orchestration/service.py` | Provider request metadata and human answer ownership |
| `tests/test_cross_layer_intelligence.py` | Deterministic alignment/conflict/safety fixtures |
| `platform/tests/test_cross_layer_routing.py` | Natural routing fixtures |

No internal HTTP N+1 composition, duplicate calculation stack, new database,
RAG retriever, subscription or personal-context dependency was introduced.
