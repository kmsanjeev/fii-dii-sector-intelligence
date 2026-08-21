# Implementation Inventory

| Component | Location | State |
|---|---|---|
| Registry | `data/reference/veda_theme_registry.json` | Implemented, data-driven |
| Membership/provenance | `backend/services/governed_theme_intelligence.py` | Implemented, provider-local |
| HTTP summary/detail | `backend/routers/governed_themes.py` | Implemented read-only |
| Legacy Theme routes | `backend/routers/themes.py` | Preserved unchanged |
| VEDA adapter | `D:\Projects\veda\platform\app\providers\market_intelligence.py` | Formal capability added |
| VEDA routing | `experience/routing.py` | Deterministic theme language route added |

Provider ID remains `veda-market-intelligence`; formal capability ID is
`market.theme.intelligence`.
