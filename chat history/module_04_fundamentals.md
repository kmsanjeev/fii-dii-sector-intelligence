# Chat History — Module 04: Fundamentals Layer

> **Append-only. Add new entries at the bottom. Never overwrite.**
> Covers: Phase 4A (Company Fundamentals Master), 4B (Industry Master), 4C (Classification V4 completion), 4D (NSE Constituents)

---

## Session: 2026-06-29 — Phase 4A: Company Fundamentals Master Engine

### Context
First critical-path item. Everything downstream (ML, classification completion, sector intelligence) was blocked until this engine was complete.

### Data Discovery
| Source | Rows | Used For |
|--------|------|----------|
| `data/NSE/equity_master/equity_master.csv` | 2394 | Identity (SYMBOL, COMPANY_NAME, SERIES, LISTING_DATE) |
| `data/reference/company_classification_v4.csv` | 2373 | SECTOR (→sector_platform) + THEME (→industry_nse) |
| `data/reference/company_fundamentals_master.csv` | 4353 | ISIN + MARKET_CAP_BUCKET from old Screener data |
| `data/reference/mapping/company_name_mapping.csv` | 4353 | ISIN (100% coverage for all 2123 EQ symbols) |

**Key finding:** equity_master.csv has blank ISIN column — ISINs come from company_name_mapping.csv.  
**Key finding:** classification_v4 THEME column = NSE/Screener industry classification (not our 18 platform themes).  
**Key finding:** classification_v4 SECTOR column has non-canonical names (METALS, OIL_GAS, PROFESSIONAL_SERVICES etc.) — needs normalization to our 29-sector taxonomy.

### Engine Design
Class-based (`CompanyFundamentalsMasterEngine`), 9 pipeline steps:
1. `_validate_inputs()` — check all 4 source files exist
2. `_build_universe()` — EQ+active filter, universe size guard (G-S-04: min 1800)
3. `_enrich_classification()` — sector normalization, basic theme derivation
4. `_enrich_isin()` — ISIN from name_mapping
5. `_enrich_market_cap()` — normalize old MARKET_CAP_BUCKET to LARGE/MID/SMALL/MICRO
6. `_apply_overrides()` — manual_override.csv applied last (G-C-02)
7. `_finalize_schema()` — add placeholder fields, validate sector/theme against canonical sets
8. `_validate_output()` — schema, empty df, universe size guards
9. `_save()` → `_write_review_queue()` → `_write_coverage_report()` — atomic writes (G-D-02)

### Sector Normalization Map (SECTOR_NORMALIZE)
44 entries mapping classification_v4 names → our 29 canonical sectors. Key fixes:
- `PROFESSIONAL_SERVICES` → `IT` (NSE consulting = IT-adjacent)
- `PACKAGING` → `CHEMICALS`
- `EDUCATION` → `HEALTHCARE`
- `OIL_GAS` → `ENERGY`, `METALS` → `METAL`, `AGRI` → `AGRICULTURE`
- `INDUSTRIAL_MANUFACTURING` → `CAPITAL_GOODS`

### Manual Override File Created
`data/reference/mapping/manual_override.csv` — 8 entries:
- ADANIPORTS: CHEMICALS (Screener error) → LOGISTICS
- ONGC: AGRI (Screener error) → ENERGY
- COALINDIA: POWER → ENERGY (with PSU_REVIVAL theme)
- ITC, RELIANCE, BAJAJHLDNG, SCHAEFFLER, CAMS — sector refinements

### Results (All PASS)
| Spec Criterion | Result | Status |
|---------------|--------|--------|
| 95%+ industry_nse populated | 100.0% | PASS |
| ZERO null ISIN | 0 nulls | PASS |
| ZERO null listing_date | 0 nulls | PASS |
| ADANIPORTS = LOGISTICS | LOGISTICS | PASS |

Final coverage:
- ISIN: 100%
- Sector classified (non-OTHER): **95.1%**
- Theme classified: 94.8%
- Market cap known: 100%
- Review queue: 103 symbols (mostly niche/non-standard businesses)

### Output Files
| File | Path | Description |
|------|------|-------------|
| company_fundamentals_master.csv | `data/NSE/equity_master/` | 2123 rows, 15 columns — **canonical master** |
| fundamentals_review_queue.csv | `data/NSE/equity_master/` | 103 symbols needing attention |
| fundamentals_coverage_report.csv | `data/NSE/equity_master/` | Metrics snapshot |
| manual_override.csv | `data/reference/mapping/` | 8 manual corrections |

### Known Remaining Issue
ITC market_cap_category = MICRO — inherited from old Screener data (incorrect; ITC is LARGE cap).  
Fix: Phase 4 shareholding engine will update market_cap from live NSE data. Acceptable for now.

### Next (Phase 4B)
`engines/fundamentals/industry_master_engine.py` — build `industry_nse → sector_platform + theme_platform` 
mapping table. This will reduce the 103-symbol review queue by providing definitive classification for
rare industry types (PACKAGING, DIVERSIFIED COMMERCIAL SERVICES, TRADING, etc.).

---

---

## Session: 2026-06-29 — Phase 4B: Industry Master Engine

### Purpose
Build authoritative industry_nse → sector_platform + theme_platform lookup table covering all 183 unique NSE industry classifications, then apply it back to improve company_fundamentals_master.csv.

### Design
- Reads Phase 4A output (company_fundamentals_master.csv) — Phase 4B depends on Phase 4A
- Computes majority-vote sector per industry_nse from 2123-symbol data
- Applies MANUAL_CORRECTIONS dict for 13 known wrong/ambiguous cases
- Assigns industry_group (10 groups) and theme_platform (from SECTOR_TO_THEME)
- Computes confidence_score (1.0 = manual, 0.95 = majority ≥95%, 0.80 = 75-94%)
- Applies lookup back to company_fundamentals_master.csv (skips manually-overridden symbols)

### Bugs Found and Fixed
1. `_manual_theme` column NaN initialization bug — `.loc[mask, new_col]` creates NaN for unmasked rows; then `str.strip() != ""` on NaN evaluates True → overwrites all themes with NaN. Fix: initialize `master["_manual_theme"] = ""` before any corrections loop.
2. `float('nan')` is truthy in Python — `if new_theme` passes for NaN, causing NaN to be assigned as theme. Fix: use `pd.notna(new_theme)` guard.

### Key Corrections in MANUAL_CORRECTIONS dict
| Industry | Was | Now |
|----------|-----|-----|
| DIVERSIFIED COMMERCIAL SERVICES (37 cos) | IT | OTHER |
| COAL (3 cos) | POWER | ENERGY, PSU_REVIVAL |
| PACKAGING (31 cos) | OTHER | CHEMICALS |
| PAPER AND PAPER PRODUCTS (21 cos) | OTHER | CHEMICALS |
| FURNITURE HOME FURNISHING (10 cos) | OTHER | REALTY |
| HOUSEWARE (4 cos) | OTHER | FMCG |
| AMUSEMENT PARKS OTHER RECREATION (3 cos) | OTHER | HOSPITALITY |
| GEMS JEWELLERY AND WATCHES | FMCG/RURAL | FMCG/PREMIUMISATION |

### Results
- Industries mapped: 183
- Industries in OTHER (by design): 5 (DISTRIBUTORS, DIVERSIFIED COMMERCIAL SERVICES, FOREST PRODUCTS, OTHER CONSUMER SERVICES, TRADING AND DISTRIBUTORS — genuinely no single sector)
- All 183 at high confidence — no review queue
- company_fundamentals_master.csv updated: 96.7% sector, 100% theme coverage

### Output Files
| File | Path |
|------|------|
| industry_master.csv | `data/reference/mapping/` |
| company_fundamentals_master.csv | `data/NSE/equity_master/` (updated) |

### Next (Phase 4C)
`engines/fundamentals/classification_engine_v4.py` — complete the classification engine to use industry_master.csv as primary lookup (currently incomplete at 221 lines). Target: 95%+ correct classification using industry_master + manual overrides, verified against test cases.

---

## Session: 2026-06-30 — Phase 4C: Classification Engine V4 Completion

### Context
Resumed Phase 4C from prior session summary. Discovery in prior session identified 71 symbols
classified as OTHER after Phase 4B, broken into:
- 37 DIVERSIFIED COMMERCIAL SERVICES (staffing, facility management)
- 23 TRADING AND DISTRIBUTORS (trading companies)
- 9 OTHER CONSUMER SERVICES (includes AMC companies, IT firms)
- 1 FOREST PRODUCTS, 1 DISTRIBUTORS

### Key Technical Decisions
1. **Full engine rewrite** — replaced 221-line Screener-based stub with proper hierarchical engine
2. **5-level classification hierarchy**:
   - Level 1: Industry Master lookup (183 industry groups → sector/theme; covers 95%+)
   - Level 2: SYMBOL_CORRECTIONS dict (60 precision fixes for known OTHER symbols)
   - Level 3: Company name keyword matching (34 rules for future unknown symbols)
   - Level 4: Manual override table (G-C-02 — always applied last)
   - Level 5: Flag as UNCLASSIFIED → review queue
3. **Dual output** — writes company_classification_v4.csv AND updates company_fundamentals_master.csv in-place (atomic writes)
4. **Source tracking** — each classification tagged with SOURCE column (INDUSTRY_MASTER / SYMBOL_CORRECTION / KEYWORD_MATCH / MANUAL_OVERRIDE)

### Classification Logic (SYMBOL_CORRECTIONS — 60 entries)
| Sector | Symbols |
|--------|---------|
| AMC | ICICIAMC, NAM-INDIA, UTIAMC |
| AUTO | SUPRAJIT, MAJESAUT, PTL |
| CAPITAL_GOODS | HARSHA, INTLCONV, SANGHVIMOV, DYNAMATECH, OMNI, TEXINFRA |
| REALTY | INDIQUBE, NESCO, NIRLON, SMARTWORKS, EFCIL, HEMIPROP, WEWORK, MERCANTILE |
| IT | CYBERTECH, GENESYS, SASKEN, DSSL, REDINGTON |
| TELECOM | SPCENET |
| HOSPITALITY | DEVYANI, ADVENTHTL |
| LOGISTICS | GICL, TARACHAND, TVSSCS |
| FINANCIAL_SERVICES | DBSTOCKBRO, ALANKIT, CMSINFO, RADIANTCMS, PRUDENT, ICDSLTD |
| ENERGY | SOUTHWEST, KOTYARK |
| METAL | SHIVAUM, GOYALALUM, MSTCLTD |
| INFRASTRUCTURE | RUCHINFRA, ELITECON |
| CHEMICALS | VIKASLIFE, FLEXITUFF, RUBFILA, SICAGEN, IWP |
| FMCG | KOTHARIPRO, VINCOFE, GOLDIAM |
| AGRICULTURE | UMAEXPORTS |
| TEXTILES | LAHOTIOV |
| MEDIA | TOUCHWOOD |
| DEFENCE | ACEINTEG |
| RETAIL | CNL |
| POWER | BLUSPRING |
| DIVERSIFIED | STCINDIA, MMTC |

### Results
| Metric | Phase 4A | Phase 4B | Phase 4C |
|--------|----------|----------|----------|
| Total symbols | 2123 | 2123 | 2123 |
| Non-OTHER coverage | 95.1% | 96.7% | **99.53%** |
| OTHER remaining | 100 | 71 | **10** |
| UNCLASSIFIED | 0 | 0 | 0 |

### Key Verifications (all PASS)
- ADANIPORTS → LOGISTICS / LOGISTICS_MODERNISATION ✅
- ICICIAMC / NAM-INDIA / UTIAMC → AMC / FINANCIALISATION ✅
- SUPRAJIT → AUTO / EV_TRANSITION ✅
- TVSSCS / TARACHAND → LOGISTICS / LOGISTICS_MODERNISATION ✅
- DEVYANI → HOSPITALITY / PREMIUMISATION ✅
- SASKEN / REDINGTON → IT / DIGITAL_INDIA ✅
- DYNAMATECH → CAPITAL_GOODS / DEFENCE_ELECTRONICS ✅
- TCS → IT / DIGITAL_INDIA ✅
- ITC → FMCG / RURAL_CONSUMPTION ✅
- STCINDIA / MMTC → DIVERSIFIED / PSU_REVIVAL ✅

### Remaining OTHER (10 — genuinely miscellaneous)
AARVI, AKG, DEVX, KAPSTON, KRYSTAL, LANDSMILL, METROGLOBL, QUESS, SIS, UDS
These are facility management / staffing / export trading companies with no dominant sector.

### Output Files
| File | Path |
|------|------|
| classification_engine_v4.py | `engines/fundamentals/` (complete rewrite) |
| company_classification_v4.csv | `data/reference/` (2123 rows, 7 cols with SOURCE) |
| company_fundamentals_master.csv | `data/NSE/equity_master/` (updated to 99.53%) |
| classification_coverage_report.csv | `data/NSE/equity_master/` |
| classification_review_queue.csv | `data/NSE/equity_master/` (10 symbols) |
| classification_sector_counts.csv | `data/NSE/equity_master/` |

### Next (Phase 4D)
`engines/foundation/nse_constituents_engine_v1.py` — add auto-download of 139 NSE index constituent files from NSE API so sector-level index membership can be used in future classification passes.

---

## Session: 2026-06-30 — Phase 4D: NSE Constituents Engine V1

### Context
Phase 4D was the NSE Constituents auto-downloader. Goal: download index constituent lists so
`index_membership.csv` can serve as a sector-confirmation data source for future classification passes.

### Key Technical Discovery
- `nseindia.com` main API: **blocked** — returns 403 (Akamai bot protection, `_abck` cookie)
- `nselib` has only 4 hardcoded index list functions (nifty50, next50, midcap150, smallcap250)
- `nsearchives.nseindia.com/content/indices/` — **open domain, no auth required** — returns CSV
- This is the same domain nselib uses internally for its 4 hardcoded functions
- 30 indices confirmed accessible via filename probing (named e.g. `ind_niftyautolist.csv`)

### Index Filename Pattern (on nsearchives)
```
ind_nifty50list.csv            → NIFTY 50 (50 stocks)
ind_niftyautolist.csv          → NIFTY AUTO (15 stocks)
ind_niftyitlist.csv            → NIFTY IT (10 stocks)
ind_niftypharmalist.csv        → NIFTY PHARMA (20 stocks)
ind_niftymidcap150list.csv     → NIFTY MIDCAP 150 (150 stocks)
ind_niftysmallcap250list.csv   → NIFTY SMALLCAP 250 (250 stocks)
```

### Engine Design
- Class `NSEConstituentsEngineV1`, single `run()` method
- INDEX_REGISTRY: list of (index_name, filename, platform_sector_hint)
- G-A-01: 1s rate limit between requests
- G-A-02: 3 retries with exponential backoff
- G-A-03: failed indices → recovery queue
- G-D-02: atomic writes (.tmp → shutil.move)
- G-S-01: EQ series filter on each constituent CSV
- Index membership master built from combined data

### Results
- 30/30 indices downloaded (0 failures)
- 2,519 total constituent rows across all indices
- 506 unique symbols in index_membership.csv
- EQ series filter: only equity stocks retained

### Key Verifications (all PASS)
- TCS → dominant_sector_hint=IT ✅
- HDFCBANK → sector_hints=BANKING|FINANCIAL_SERVICES ✅
- MARUTI → dominant_sector_hint=AUTO ✅
- ONGC → dominant_sector_hint=ENERGY ✅
- SUNPHARMA → sector_hints=HEALTHCARE|PHARMA ✅

### Output Files
| File | Path | Rows |
|------|------|------|
| nifty_*_constituents.csv (30 files) | `data/NSE/indices/` | varies |
| index_membership.csv | `data/NSE/indices/` | 506 |
| download_registry.csv | `data/NSE/indices/reports/` | 30 |

### Indices NOT Available on nsearchives (future work)
NIFTY FINANCIAL SERVICES (main), NIFTY PRIVATE BANK, NIFTY CHEMICALS, NIFTY CEMENT,
NIFTY INFRASTRUCTURE, NIFTY TOTAL MARKET, NIFTY INDIA DEFENCE, NIFTY EV,
NIFTY INDIA DIGITAL, NIFTY INDIA MANUFACTURING, NIFTY TRANSPORTATION & LOGISTICS

### Phase 4 Summary — Fundamentals Layer COMPLETE
| Phase | Engine | Status |
|-------|--------|--------|
| 4A | company_fundamentals_master_engine.py | ✅ 2123 symbols, 100% ISIN |
| 4B | industry_master_engine.py | ✅ 183 industries mapped, 96.7% → improved |
| 4C | classification_engine_v4.py | ✅ 99.53% coverage, 10 OTHER remain |
| 4D | nse_constituents_engine_v1.py | ✅ 30 indices, 506 symbols, 0 failures |
