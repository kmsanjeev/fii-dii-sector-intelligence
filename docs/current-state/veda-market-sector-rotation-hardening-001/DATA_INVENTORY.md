# Sector data inventory

| Dataset | Source / authority | Date range or as-of | Coverage / quality | Consumers and limitation |
|---|---|---|---|---|
| `company_classification_v4.csv` | Derived platform classification from NSE industry mapping | updated 2026-06-30 | 2,123 symbols; 27 non-empty sectors; no duplicate symbols in audit | sector mapping and breadth; no historical membership snapshots |
| NSE equity bhavcopy CSV | NSE equity bhavcopy, provider-local | 1995-01-02 to 2026-08-20; bounded rotation window 2026-07-22 to 2026-08-20 | 7,867 CSV files; current EQ price evidence | current constituent returns and breadth; raw price history is not an index-weighted series |
| `nifty_50_constituents.csv` | NSE constituent reference | current file, 50 symbols | used as a fixed current benchmark universe | equal-weight benchmark proxy; historical membership is not reconstructed |
| `index_strength.csv` / `sector_rotation.csv` | Derived from `MW-All-Indices-05-Jun-2026.csv` | source date 2026-06-05 | 139 indices / 29 legacy sector rows; stale relative to current constituent prices | legacy compatibility and traceability only |
| `sector_flow_scores.csv` | Derived from weighted participant/F&O context | 2016-01-04 to 2026-08-19 | 75,864 rows, 2,616 dates | broad participant context; not direct sector institutional attribution |
| `fpi_sector_signals.csv` | provider-local FPI ownership source | 2012-04-15 to 2026-06-30 | fortnightly/irregular sector ownership signal | optional ownership context; date may lag current prices |
| `sector_rotation_history.csv` | Phase 6C derived output | 2026-07-22 to 2026-08-20 | 22 dates × 27 sectors | bounded return/rank history; insufficient for unsupported long-term claims |
| `sector_rotation_intelligence.csv` | Phase 6C snapshot | 2026-08-20 | 27 sectors; contract 1.1 | formal `/api/sectors` source |

Missing values remain missing. No unavailable constituent is counted as
unchanged, positive or negative.
