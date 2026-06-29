# FETCHERS DIRECTORY — CLAUDE CONTEXT

## STATUS: LEGACY FLAT STRUCTURE
`fetchers/` is the original engine directory from Generation 1 of this platform.
All files here are production engines but they pre-date the `engines/` subdirectory structure.

**DO NOT add new engines here.**
New engines go in `engines/<module>/` following the proper structure.
Migrate fetchers to `engines/` gradually as each module is refactored.

## ENGINE INVENTORY

### Institutional Intelligence (Phase 7 — COMPLETE ✅)
| File | Purpose | Migrate To |
|------|---------|-----------|
| `daily_fii_dii_fetcher.py` | Daily FII/DII cash flow download | `engines/intelligence/` |
| `fii_dii_backfill_engine.py` | Fill missing FII/DII history | `engines/intelligence/` |
| `institutional_backfill_engine.py` | Institutional OI/volume backfill | `engines/intelligence/` |
| `institutional_integrity_engine.py` | Validate institutional history completeness | `engines/intelligence/` |
| `institutional_positioning_engine.py` | Build positioning dataset | `engines/intelligence/` |
| `institutional_trend_engine.py` | Trend analysis (IN PROGRESS) | `engines/intelligence/` |
| `flow_regime_engine.py` | Market regime classification | `engines/intelligence/` |
| `conviction_engine.py` | Institutional conviction scoring | `engines/intelligence/` |

### Sector Intelligence (Phase 8 — Partial ✅)
| File | Purpose | Migrate To |
|------|---------|-----------|
| `sector_fetcher.py` | Sector data retrieval | `engines/intelligence/` |
| `sector_history_fetcher.py` | Historical sector data | `engines/intelligence/` |
| `sector_stock_mapper.py` | Map stocks to sectors | `engines/fundamentals/` |
| `persistence_engine.py` | Sector/theme persistence tracking | `engines/intelligence/` |
| `leadership_duration_engine.py` | Leadership duration analysis | `engines/intelligence/` |
| `aggregation_engine.py` | Multi-timeframe aggregation | `engines/intelligence/` |

### Theme Intelligence
| File | Purpose | Migrate To |
|------|---------|-----------|
| `thematic_history_fetcher.py` | Historical theme data | `engines/intelligence/` |

### Historical Data
| File | Purpose | Migrate To |
|------|---------|-----------|
| `historical_data_engine.py` | Per-symbol OHLCV cache builder | `engines/acquisition/` |
| `data_store.py` | Data persistence layer | `engines/common/` |

### Signals
| File | Purpose | Migrate To |
|------|---------|-----------|
| `signal_engine.py` | Signal generation | `engines/intelligence/` |
| `movers_fetcher.py` | Top movers detection | `engines/intelligence/` |
| `screener_sector_scraper.py` | Screener.in sector scraper (validation only) | `engines/fundamentals/` |

## MIGRATION RULES
When migrating a fetcher to `engines/`:
1. Rewrite to use `engines.common.config` for all paths (replace hardcoded paths)
2. Rewrite to use `engines.common.logger.get_logger(__name__)`
3. Apply engine template structure (see `engines/CLAUDE.md`)
4. Update `main.py` imports before deleting from `fetchers/`
5. Run full validation test before committing

**Never migrate and refactor at the same time.** Migrate first (minimal changes),
then refactor in a separate commit.

## INSTITUTIONAL TREND ENGINE (pending completion)
`institutional_trend_engine.py` is marked IN PROGRESS in the module docs.
Before starting Phase 4, review and complete this engine.
It produces trend direction/strength/acceleration across: Daily, Weekly, BiWeekly, Monthly, Quarterly, HalfYearly, Yearly horizons.
Output: `data/historical/institutional/institutional_trends.csv`

## IMPORTS (existing pattern in fetchers)
Many files in `fetchers/` use direct path construction.
When reading these engines, be aware they may NOT use `engines.common.config`.
Always check imports before assuming path constants.
