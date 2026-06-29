# Module 08 — Bull Run Probability Engine
## Session Log (append-only)

---

## Session: 2026-06-30 — Phase 8A / 8B

### Trigger
User: "start Phase 8" (continued from context-compacted prior session)

### Context
- Phases 5/6/7 all complete (Participant + Sector Rotation + Corporate Intelligence)
- Survey completed in prior session: confirmed all inputs available
- No code written yet when context was compacted — resumed directly to engine creation

### Scope Decision
2 engines in `engines/intelligence/`:
- 8A: `price_momentum_engine.py` — price returns + volume trend + sector-relative strength
- 8B: `bull_run_probability_engine.py` — multi-factor bull run probability score

---

### Phase 8A — `price_momentum_engine.py`

**Data source:** legacy bhavcopy at `data/bhavcopy/equity/` (7813+ files, dual schema support)

**Lookback windows:**
- 30D = 22 trading days back
- 60D = 43 trading days back
- 90D = 65 trading days back
- 365D = 252 trading days back
- Volume window = last 22 files for 20D average

**Dual schema handling:**
- Pre-2020: CLOSE + TOTTRDQTY columns
- Post-2020: CLOSE_PRICE + TTL_TRD_QNTY columns
- `_load_bhav()` detects and normalises on load

**Scoring (all percentile-ranked 0-100):**
- ret_30d_pct: 35%
- ret_90d_pct: 25%
- ret_365d_pct: 20%
- sector_rel_pct: 15% (return vs sector median)
- vol_ratio_pct: 5%

**Results (2026-06-30):**
- 2441 symbols, as_of_date: 2026-06-10
- 30D range: -94.3% to +98.0%
- 1872 symbols with 365D data
- Price score range: 3 to 98
- Top: INOXINDIA (98), JNKINDIA (98) — both CAPITAL_GOODS

---

### Phase 8B — `bull_run_probability_engine.py`

**Factor inputs:**
| Factor | Source | Weight | Normalization |
|--------|--------|--------|---------------|
| price_score | price_momentum.csv | 30% | Already 0-100 from 8A |
| sector_flow_score | sector_rotation_intelligence.csv (FII_flow_score) | 25% | (score+100)/2 |
| deal_score | institutional_deal_signals.csv (inst_net_value_cr) | 25% | Percentile rank 0-100; neutral=50 |
| corporate_score | corporate_confidence_scores.csv (confidence_score_12m) | 20% | Clip[-3,6] rescaled 0-100; neutral=50 |

**Market regime multiplier** from institutional_positioning_history.csv:
- ACCUMULATION: ×1.10
- DISTRIBUTION: ×0.80
- Others: ×0.90

**Labels:**
- STRONG_CANDIDATE (>=65)
- EMERGING (>=45)
- WATCHLIST (>=30)
- NEUTRAL (>=15)
- AVOID (<15)

**Results (2026-06-30):**
- 2441 symbols scored
- Regime: DISTRIBUTION (×0.80) — caps ceiling at ~55
- Score range: 12.3 to 54.9
- EMERGING: 16 symbols (no STRONG_CANDIDATE possible in DISTRIBUTION regime)
- WATCHLIST: 1599 symbols
- NEUTRAL: 824 symbols
- AVOID: 2 symbols
- Top candidates: ADANIENSOL (55), ADANIENT (51), GMRAIRPORT (50), CRAFTSMAN (48), EMCURE (48)

**Design notes:**
- Symbols with no deal data → neutral score 50 (not 0, not NaN)
- Symbols with no corporate data → neutral score 50
- Sectors with no rotation data → neutral sector_flow 50
- vol_ratio outliers >50x clipped to NaN to prevent distortion
- Regime multiplier applied after base_score; final score clipped [0, 100]

---

### Files Created
| File | Description |
|------|-------------|
| `engines/intelligence/price_momentum_engine.py` | Phase 8A |
| `engines/intelligence/bull_run_probability_engine.py` | Phase 8B |
| `data/intelligence/price_momentum.csv` | 2441 rows, 17 cols |
| `data/intelligence/bull_run_probability.csv` | 2441 rows, 17 cols |
| `data/intelligence/bull_run_watchlist.csv` | 16 rows (EMERGING only in DISTRIBUTION regime) |
| `chat history/module_08_bull_run_probability.md` | This log |

### Files Updated
| File | Change |
|------|--------|
| `docs/governance/CHANGELOG.md` | v3.1 entry |
| `docs/governance/MODULE_REGISTRY.md` | Module 05 Stock Intelligence: 10% → 40%, ACTIVE |
| `memory/project_fii_dii.md` | Phase 8 ✅ 100% |

### Next Priority
Platform is now at a natural integration point:
- All 4 intelligence layers operational: Participant + Sector + Corporate + Price/Bull-Run
- Capital flow cascade: FII/DII/PRO/CLIENT → sector attribution → stock scoring
- Options:
  1. Run Phase 5 engines (participant_acquisition_engine.py) against live NSE API to generate participant_flow_scores.csv
  2. Build GUI (React) — Phase GUI-1 AppShell (no data dependency)
  3. Build RAG-1 FAISS indexer (Phase 3B outputs already exist)
  4. Start Management Intelligence / financial results layer
