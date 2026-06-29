# ENGINES/INTELLIGENCE — CLAUDE CONTEXT

## PURPOSE
Output intelligence engines that sit above raw data and fetchers.
These consume processed/cached data and produce ranked, scored intelligence datasets.

## ACTIVE ENGINES
| File | Status | Purpose |
|------|--------|---------|
| (none fully active yet) | — | Stubs only |

## STUB FILES — DO NOT EXTEND, DO NOT USE
| File | Lines | Issue |
|------|-------|-------|
| `index_intelligence_engine_v2.py` | 80 | Architecture V2 stub — no implementation |
| `leadership_persistence_engine_v2.py` | 30 | Architecture V2 stub — no implementation |

Production equivalents live at the ENGINE ROOT level:
- `engines/index_intelligence_engine.py` (221 lines) ← USE THIS
- `engines/sector_leadership_persistence_engine.py` (316 lines) ← USE THIS

## PLANNED ENGINES (build after Phase 4 complete)
```
bull_run_probability_engine.py       ← Phase 8 priority
stock_ranking_engine.py              ← Phase 8
sector_rotation_engine.py            ← Phase roadmap step 6
sector_capital_flow_engine.py        ← Phase roadmap step 6
sector_momentum_engine.py
sector_opportunity_engine.py
theme_rotation_engine.py
theme_capital_flow_engine.py
theme_leadership_engine.py
```

## BULL RUN PROBABILITY ENGINE SPEC (when ready to build)
**File:** `bull_run_probability_engine.py`
**Inputs (all required — do not build until all available):**
- Price momentum (from sector_leadership_persistence_engine.py)
- Sector leadership score
- Theme leadership score
- Revenue growth (from results engine, Phase 4)
- PAT growth (from results engine, Phase 4)
- FII accumulation (from institutional_positioning_engine.py)
- DII accumulation
- Management confidence score (Phase 6)
- Order book expansion (Phase 6)
- Governance risk score (Phase 6)

**Output:** `data/intelligence/bull_run_probability.csv`
Schema: `symbol, date, bull_run_score, confidence, signal_strength, component_scores`

## STOCK RANKING ENGINE SPEC (when ready to build)
**File:** `stock_ranking_engine.py`
Multi-factor ranking: Technical + Fundamental + Ownership + Management + Governance
**Output:** `data/intelligence/stock_rankings.csv`
Schema: `symbol, date, overall_rank, technical_score, fundamental_score, ownership_score, management_score, governance_score`
