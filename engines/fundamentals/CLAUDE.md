# ENGINES/FUNDAMENTALS — CLAUDE CONTEXT

## THIS IS THE CRITICAL PATH
Phase 4 is at 0%. Everything downstream (Phase 5, 6, 8) is blocked until this is done.
**Do not start any other module until `company_fundamentals_master_engine.py` is complete.**

## BUILD SEQUENCE (strict order)

### STEP 1 — Company Fundamentals Master Engine (NEXT BUILD)
**File:** `company_fundamentals_master_engine.py`
**Purpose:** Authoritative company master with industry/sector/theme mapping for all 2123 symbols.

Required outputs:
```
data/NSE/equity_master/company_fundamentals_master.csv
data/NSE/equity_master/fundamentals_review_queue.csv   ← symbols needing manual review
data/NSE/equity_master/fundamentals_coverage_report.csv
```

Required schema:
```
symbol, isin, company_name, series, status, listing_date,
industry_nse,           ← from NSE (primary)
sector_platform,        ← platform's sector taxonomy (29 sectors)
theme_platform,         ← platform's theme taxonomy (18 themes)
market_cap_category,    ← LARGE / MID / SMALL / MICRO
business_profile,       ← one-line description
fii_holding_pct,        ← last available
dii_holding_pct,
promoter_holding_pct,
last_updated
```

Data source priority:
1. nselib equity master (symbol, isin, listing_date, industry_nse)
2. NSE industry/sector classification
3. Screener.in (VALIDATION LAYER ONLY — not primary source)
4. Manual override CSV for exceptions

Success criteria:
- 95%+ of 2123 symbols have valid `industry_nse`
- ZERO null `isin` values
- ZERO null `listing_date` values
- ADANIPORTS → sector=LOGISTICS, theme=INFRASTRUCTURE (not AEROSPACE)

---

### STEP 2 — Industry Master Engine
**File:** `industry_master_engine.py`
**Purpose:** Map all NSE industry codes to platform sector + theme taxonomy.

Required output:
```
data/reference/mapping/industry_master.csv
```

Schema:
```
industry_nse, sector_platform, theme_platform, industry_group, confidence_score
```

This fixes the ADANIPORTS → AEROSPACE bug (keyword classification fails when industry master is absent).

---

### STEP 3 — Classification Engine V4 Completion
**File:** `classification_engine_v4.py`
**Status:** Exists (221 lines) but incomplete.

Classification hierarchy (in priority order):
1. Industry Master lookup (exact match on industry_nse)
2. NSE sector index membership (Nifty IT → IT sector)
3. Business profile keyword matching
4. Manual override table
5. Flag as UNCLASSIFIED for manual review

Target: 95%+ of 2123 symbols correctly classified.

---

## ACTIVE FILES IN THIS DIRECTORY

| File | Status | Notes |
|------|--------|-------|
| `company_fundamentals_master_engine.py` | 🔴 In Progress | #1 build priority |
| `industry_master_engine.py` | 🔴 Not started | Step 2 |
| `classification_engine_v4.py` | 🟡 Incomplete | Step 3 |
| `security_master_engine_v2.py` | ✅ Active | Use this — v2 is canonical (502 lines) |
| `company_name_mapping_engine.py` | ✅ Active | Symbol ↔ company name resolution |
| `screener_classification_engine.py` | ✅ Active | Validation layer only |
| `theme_master_engine.py` | ✅ Active | Theme taxonomy engine |
| `security_master_engine.py` | ❌ LEGACY | Do not use — superseded by v2 |

## PLATFORM TAXONOMIES (fixed, do not change without ADR)

**29 Platform Sectors:**
BANKING, FINANCIAL_SERVICES, IT, PHARMA, FMCG, AUTO, CAPITAL_GOODS,
DEFENCE, POWER, ENERGY, METAL, REALTY, INFRASTRUCTURE, TELECOM,
CHEMICALS, CEMENT, LOGISTICS, AGRICULTURE, TEXTILES, MEDIA,
RETAIL, HOSPITALITY, AVIATION, HEALTHCARE, INSURANCE, AMC,
EXCHANGE, DIVERSIFIED, OTHER

**18 Platform Themes:**
DIGITAL_INDIA, DEFENCE_ELECTRONICS, EV_TRANSITION, GREEN_ENERGY,
CHINA_PLUS_ONE, CAPEX_CYCLE, FINANCIALISATION, REAL_ESTATE_RECOVERY,
INFRASTRUCTURE_BUILD, SMART_MANUFACTURING, DATA_CENTRES, HEALTHCARE_EXPANSION,
RURAL_CONSUMPTION, PREMIUMISATION, EXPORT_GROWTH, PSU_REVIVAL,
SEMICONDUCTOR, LOGISTICS_MODERNISATION

## KNOWN CLASSIFICATION BUGS TO FIX
| Symbol | Current (Wrong) | Expected |
|--------|-----------------|---------|
| ADANIPORTS | AEROSPACE | LOGISTICS / INFRASTRUCTURE |
| (audit more when industry_master is complete) | | |

## GUARDRAILS SPECIFIC TO THIS DIRECTORY

### Classification Edge Cases
| Scenario | Rule |
|----------|------|
| ISIN shared by 2 symbols post-merger | Keep active symbol; mark retired as DELISTED |
| Conglomerate (ITC, RELIANCE, L&T) | Classify by primary revenue segment — add to manual_override.csv |
| Holding company (BAJAJ HOLDINGS) | Classify by underlying business, not holding structure |
| PSU in multiple sectors (ONGC) | Primary business wins (ENERGY for ONGC, not CHEMICALS) |
| Recently listed (< 1 year) | No historical data for peer comparison; flag as RECENTLY_LISTED |
| Company changed business | Use current business — update classification, log reason |
| SME stocks (NSE Emerge) | EXCLUDE from main 2123 EQ universe |
| ETF / Index Fund in bhavcopy | EXCLUDE using EXCLUDE_KEYWORDS filter |
| Warrant / Rights / Partly-paid | EXCLUDE — non-EQ series |

### Company Fundamentals Master — Edge Cases
| Field | Edge Case | Handling |
|-------|-----------|---------|
| `isin` | Null ISIN for very old listings | Log to review queue; do not fill with placeholder |
| `listing_date` | Pre-1990 listings may have no date | Use `1995-01-01` as min bound; flag as ESTIMATED |
| `industry_nse` | NSE industry code changes over time | Track history; use most recent in master |
| `market_cap_category` | Changes over time (MID → LARGE) | Snapshot at compute time; re-classify quarterly |
| `sector_platform` | UNCATEGORIZED after all fallbacks | Add to review_queue; never block downstream |
| `theme_platform` | Some stocks have no theme | NULL is acceptable for theme; sector is mandatory |

### Financial Results Edge Cases (Phase 4 build reference)
- Q4 results may be annual + Q4 combined — parse correctly
- Some companies report quarterly, others half-yearly — handle both
- Standalone vs Consolidated results — prefer Consolidated; note when only Standalone available
- PAT can be legitimately negative (loss-making companies) — do not filter out
- Revenue < 0 is valid for hedging/derivatives companies — flag but retain

## IMPORTS FOR THIS DIRECTORY
```python
from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.nse_client import NSEClient
from engines.common.validators import validate_schema

# Key paths
cfg.EQUITY_MASTER_DIR    # data/NSE/equity_master/
cfg.RESULTS_DIR          # data/NSE/results/
cfg.SHAREHOLDING_DIR     # data/NSE/shareholding/
```
