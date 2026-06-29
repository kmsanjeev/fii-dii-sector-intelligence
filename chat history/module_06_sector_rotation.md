# Module 06 — Sector Rotation + Capital Flow Intelligence
## Session Log (append-only)

---

## Session: 2026-06-30 — Phase 6A / 6B / 6C

### Trigger
User: "start Phase 6"

### Context
- Phase 5 (participant intelligence) complete in same session
- Existing data: bhavcopy 7813 files (1995-2026), classification_v4.csv (2123 symbols → 29 sectors),
  institutional_positioning_history.csv (2563 rows, 2016-2026)
- Problem identified: NSE does not publish per-sector participant F&O data
- Solution: weight-allocate total participant flows using daily sector turnover from bhavcopy

---

### Phase 6A — `sector_capital_flow_engine.py`

**Key discovery:** Bhavcopy has TWO schemas:
- Pre-2020: `CLOSE, TOTTRDQTY` columns (old NSE format)
- Post-2020: `CLOSE_PRICE, TTL_TRD_QNTY` columns (new NSE format)
- First run failed with 2020 start date (old-schema files threw ValueError, silently skipped)
- Fix: `_normalize_bhav()` static method detects schema and renames to canonical columns

**Method:**
- For each bhavcopy date: EQ series only, compute `turnover = CLOSE_PRICE * TTL_TRD_QNTY / 1e7` (crores)
- Map SYMBOL → platform sector from company_classification_v4.csv
- `sector_weight = sector_turnover / total_market_turnover`
- Multiply FII/DII/PRO/CLIENT OI and Volume by sector_weight → attributed flow
- All 29 platform sectors present each day (sectors with 0 turnover get 0 attribution)

**Output:** `data/intelligence/sector_capital_flows.csv`
- 74,269 rows, 14 cols, 29 sectors × 2561 dates (2016-01-04 to 2026-06-02)
- Columns: date, sector, sector_turnover_cr, sector_weight, market_turnover_cr, symbol_count,
  FII_OI_Net_attr, DII_OI_Net_attr, PRO_OI_Net_attr, CLIENT_OI_Net_attr,
  FII_Volume_Net_attr, DII_Volume_Net_attr, PRO_Volume_Net_attr, CLIENT_Volume_Net_attr

**Top sectors by turnover weight (2026-06-02):**
  IT=13.4%, FINANCIAL_SERVICES=10.5%, BANKING=9.2%, CAPITAL_GOODS=7.3%

---

### Phase 6B — `sector_flow_score_engine.py`

**Method:** Per sector, sorted time-series:
- OI Delta = day-over-day change in attributed OI
- Rolling sums: 5D/20D/60D for each participant OI
- Z-score normalisation: 252D window, clipped ±3, scaled ±100
- Score base: 20D rolling OI sum (medium-term institutional accumulation signal)
- Smart_Money_Score = avg(FII_flow_score, PRO_flow_score) per sector

**Output:** `data/intelligence/sector_flow_scores.csv` — 74,269 rows, 35 cols

---

### Phase 6C — `sector_rotation_intelligence_engine.py`

**Method:** Combines flow scores with NSE index price momentum:
- Price momentum from `sector_rotation.csv` (Phase 3 output, 29 NSE indices with MOMENTUM_SCORE)
- NSE_TO_PLATFORM dict: 32 NSE index names mapped to 29 platform sectors
- Price normalised: clip(-10,10)/10*100 → ±100 scale (consistent with flow scores)
- Combined score = 60% FII_flow_score + 40% price_norm
- Rotation quadrants: STRONG_ACCUMULATION, EARLY_ROTATION, PRICE_LED, DISTRIBUTION, NEUTRAL
- Capital flow alignment: ALIGNED or DIVERGENT

**Outputs:**
- `data/intelligence/sector_rotation_intelligence.csv` — 29-row snapshot (latest date)
- `data/intelligence/sector_rotation_history.csv` — 74,269-row time-series

**Latest snapshot (2026-06-02):**
  Most sectors in PRICE_LED (price positive, FII flow negative) or NEUTRAL
  MEDIA shows EARLY_ROTATION (FII improving, price still negative)
  Suggests broad FII distribution phase consistent with institutional_positioning_history regime=DISTRIBUTION

---

### Bugs Fixed
- `→` and `─` Unicode chars in print statements → replaced with ASCII `to` and `-` for Windows cp1252 terminal
- Pre-2020 bhavcopy schema mismatch: added `_normalize_bhav()` static method with dual-schema detection

---

### Files Created
| File | Description |
|------|-------------|
| `engines/participant/sector_capital_flow_engine.py` | Phase 6A |
| `engines/participant/sector_flow_score_engine.py` | Phase 6B |
| `engines/participant/sector_rotation_intelligence_engine.py` | Phase 6C |
| `data/intelligence/sector_capital_flows.csv` | 74,269 rows, 2016-2026 |
| `data/intelligence/sector_flow_scores.csv` | 74,269 rows, 35 cols |
| `data/intelligence/sector_rotation_intelligence.csv` | 29-row snapshot |
| `data/intelligence/sector_rotation_history.csv` | 74,269-row history |
| `chat history/module_06_sector_rotation.md` | This log |

### Files Updated
| File | Change |
|------|--------|
| `docs/governance/CHANGELOG.md` | v2.9 entry |
| `docs/governance/MODULE_REGISTRY.md` | Module 01 Participant: 85% -> 100% COMPLETE |
| `memory/project_fii_dii.md` | Phase 6 status updated |

---

### Next Priority
Phase 7 (old Phase 8 numbering) — Bull Run Discovery / probability engine
Or: GUI-1 (React AppShell) — can start now with all intelligence outputs available
Or: RAG-1 (FAISS indexer) — Phase 3B outputs ready
