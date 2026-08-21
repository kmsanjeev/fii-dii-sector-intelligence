# Existing Classification Inventory

| Asset | Observed state | Decision |
|---|---|---|
| `data/reference/company_classification_v4.csv` | 2,123 rows; 15 non-empty themes; 27 sectors; 4 source classes | Reused as primary governed classification evidence |
| `data/reference/theme_tagging.csv` | 12,916 multi-theme rows; 50 legacy theme labels; 536 cross-theme rows overlap the bounded 15-theme universe | Reused only for bounded cross-theme relationships |
| `data/reference/mapping/industry_master.csv` | 183 industry mappings with majority-vote/manual-correction provenance | Reused as classification dependency, not a Theme API |
| `data/NSE/equity_master/company_fundamentals_master.csv` | 2,123 current symbols and identity fields | Reused for optional ISIN identity |
| `engines/intelligence/theme_intelligence_engine.py` | Legacy 50-theme score and smart-money aggregation | Preserved; not silently promoted to the governed contract |
| `backend/routers/themes.py` | Legacy `/api/themes` routes and UI contract | Preserved for compatibility |

The old `THEME` field is not treated as an official exchange theme index. The
new registry makes authority, method, current-universe limitation and source
lineage explicit.
