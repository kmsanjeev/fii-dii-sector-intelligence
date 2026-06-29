# CLAUDE MASTER DEVELOPMENT GUIDE
## Capital Flow Intelligence Platform
### Version 2.0 — June 2026

---

## PURPOSE

This document is the authoritative reference Claude must load before any development session.
It supersedes all legacy docs in `docs/legacy/`. When this file conflicts with legacy docs, this file wins.

---

## SECTION 1 — PROJECT IDENTITY

**Name:** Capital Flow Intelligence Platform (fii-dii-sector-intelligence)
**Mission:** Identify how capital flows through markets before broad recognition.
**Philosophy:** Follow the Money — not the news, not the price.

```
Participant → Sector → Theme → Stock → Fundamental Validation → Portfolio → Execution
```

This is NOT a screener. It is a decision intelligence platform.

---

## SECTION 2 — AI OPERATING MODE

Always act as:
- Senior System Architect
- Lead Python Developer
- Quant Research Engineer
- Data Platform Architect

Never act as: Python tutor, generic chat assistant, beginner trainer.

**Mandatory coding rules:**
- Always deliver complete copy-paste-ready files (no partial snippets)
- Always provide git commit commands after every code change
- Freeze architecture before writing a single line of code
- Prefer incremental processing with recovery mechanisms
- Prefer scalable solutions over quick hacks

---

## SECTION 3 — ARCHITECTURE OVERVIEW (10 LAYERS)

```
Layer 01  RAW DATA               nselib / NSE API / yFinance
Layer 02  DATA PROCESSING        Validation, Normalization, Cache Generation
Layer 03  PARTICIPANT INTEL      FII, DII, PRO, CLIENT behavior
Layer 04  SECTOR INTEL           Sector rotation, capital flow, momentum
Layer 05  THEME INTEL            Thematic rotation, narrative detection
Layer 06  STOCK INTEL            Accumulation, RS, delivery, F&O
Layer 07  FUNDAMENTAL INTEL      Results, shareholding, management, orders
Layer 08  AI PLATFORM            Analyst agents, NL interface
Layer 09  GUI PLATFORM           Dashboards, heatmaps, infographics
Layer 10  EXECUTION PLATFORM     Portfolio, risk, broker adapters
```

**Cross-cutting systems:** Research, Documentation, Alerts, Reporting.

**Data acquisition priority (always enforce):**
1. nselib (primary)
2. NSE API
3. Alternative sources
4. yFinance (last resort)

---

## SECTION 4 — CANONICAL DATA DIRECTORY MAP

The actual on-disk structure (verified June 2026):

```
data/
├── bhavcopy/                     ← NSE Equity bhavcopy (1995–2026, by year)
│   ├── equity/YYYY/              ← bhavcopy_YYYYMMDD.csv
│   └── fno/YYYY/                 ← F&O bhavcopy
├── NSE/                          ← New NSE structured data
│   ├── bhavcopy/                 ← (to be migrated from data/bhavcopy/)
│   ├── equity_master/            ← equity_master.csv + reports
│   ├── indices/                  ← index constituent CSVs + reports
│   ├── corporate_actions/        ← (empty, Phase 5)
│   ├── announcements/            ← (empty, Phase 5)
│   ├── results/                  ← (empty, Phase 4)
│   └── shareholding/             ← (empty, Phase 4)
├── BSE/                          ← BSE data (future, no engines yet)
│   ├── bhavcopy/equity/
│   └── bhavcopy/fno/
├── aggregated/                   ← Multi-source aggregated (no engines yet)
├── cache/
│   ├── stock_history/            ← Per-symbol OHLCV cache
│   └── reports/
├── historical/
│   ├── fii_dii/
│   ├── institutional/            ← institutional_positioning_history.csv
│   ├── sectors/
│   ├── stocks/
│   └── thematic/
├── intelligence/                 ← Derived intelligence outputs
│   └── history/
├── reference/
│   └── mapping/                  ← Sector/theme mapping tables
├── logs/
└── (signals/, reports/ — planned)
```

**IMPORTANT — Path discrepancy:** Several legacy docs and some engines reference
`data/NSE Data/` (with a space). This path does NOT exist. The correct paths are
`data/NSE/` (structured) and `data/bhavcopy/` (raw bhavcopy). Always use the above
canonical map. Fix any engine that uses `data/NSE Data/`.

---

## SECTION 5 — ENGINE DIRECTORY MAP

```
engines/
├── common/                       ← Shared utilities (always import from here)
│   ├── config.py                 ← Project config
│   ├── constants.py              ← Constants
│   ├── filesystem.py             ← Path utilities
│   ├── holiday_engine.py         ← NSE trading calendar
│   ├── logger.py                 ← Structured logging
│   ├── nse_client.py             ← nselib wrapper
│   ├── progress.py               ← Progress reporting
│   ├── recovery.py               ← Recovery mechanisms
│   ├── registry.py               ← Engine registry
│   └── validators.py             ← Data validators
│
├── acquisition/                  ← Data downloaders
│   ├── nse_equity_acquisition_engine.py
│   ├── nse_fno_acquisition_engine.py
│   └── nse_corporate_actions_acquisition_engine.py
│
├── foundation/                   ← Foundation layer
│   └── nse_constituents_engine_v1.py
│
├── fundamentals/                 ← Phase 4 engines (critical path)
│   ├── security_master_engine_v2.py    ← ACTIVE (v1 is legacy)
│   ├── classification_engine_v4.py     ← ACTIVE
│   ├── company_fundamentals_master_engine.py  ← IN PROGRESS
│   ├── company_name_mapping_engine.py
│   ├── industry_master_engine.py
│   ├── screener_classification_engine.py
│   └── theme_master_engine.py
│
├── intelligence/                 ← Phase 3 intelligence engines
│   ├── index_intelligence_engine_v2.py   ← STUB (30 lines, incomplete)
│   └── leadership_persistence_engine_v2.py  ← STUB (30 lines, incomplete)
│
├── analytics/
│   └── price_adjustment_engine.py
│
├── classification/               ← EMPTY DIRECTORY (planned)
├── corporate/                    ← EMPTY DIRECTORY (Phase 5 planned)
├── management/                   ← EMPTY DIRECTORY (Phase 6 planned)
├── orchestration/                ← EMPTY DIRECTORY (planned)
│
├── bhavcopy_import_engine.py     ← Phase 1 ✅
├── equity_master_engine.py       ← Phase 1 ✅ (legacy root placement)
├── cache_manager.py              ← Phase 1 ✅
├── classification_engine.py      ← Phase 2 V1 (superseded by V4)
├── auto_classification_engine_v2.py  ← Phase 2 active
├── index_intelligence_engine.py  ← Phase 3 ✅ ACTIVE
├── index_intelligence_engine_v1_backup.py  ← LEGACY BACKUP (mark for removal)
├── index_snapshot_engine.py      ← Phase 3 ✅
├── index_taxonomy_engine.py      ← Phase 3 ✅
└── sector_leadership_persistence_engine.py  ← Phase 3 ✅ ACTIVE
```

**Fetchers directory** (legacy flat structure, to be migrated to engines/):
```
fetchers/
├── daily_fii_dii_fetcher.py
├── fii_dii_backfill_engine.py
├── institutional_backfill_engine.py
├── institutional_integrity_engine.py
├── institutional_positioning_engine.py
├── institutional_trend_engine.py
├── flow_regime_engine.py
├── conviction_engine.py
├── aggregation_engine.py
├── persistence_engine.py
├── leadership_duration_engine.py
├── signal_engine.py
├── sector_fetcher.py
├── sector_history_fetcher.py
├── sector_stock_mapper.py
├── thematic_history_fetcher.py
├── movers_fetcher.py
├── historical_data_engine.py
├── data_store.py
└── screener_sector_scraper.py
```

---

## SECTION 6 — PHASE BUILD STATUS (June 2026)

| Phase | Name                    | Status     | Coverage |
|-------|-------------------------|------------|----------|
| 1     | Foundation Layer        | ✅ 100%    | Complete |
| 2     | Classification Layer    | 🟡 70%     | 37% symbol coverage (783/2123) |
| 3     | Index Intelligence      | ✅ 100%    | 139 indices, 29 sectors, 18 themes |
| 4     | Fundamentals Layer      | 🔴 0%      | **CRITICAL BOTTLENECK** |
| 5     | Corporate Intelligence  | ⚪ 0%      | Blocked by Phase 4 |
| 6     | Management Intelligence | ⚪ 0%      | Blocked by Phase 4 |
| 7     | Institutional Intel     | ✅ 100%    | FII/DII/PRO/CLIENT data, 2016–present |
| 8     | Bull Run Discovery      | 🟡 40%     | Sector + Theme leadership done |
| 9     | AI Platform             | ⚪ 15%     | Architecture only |
| 10    | GUI Platform            | ⚪ 10%     | Architecture only |
| 11    | Execution Platform      | ⚪ 5%      | Architecture only |

**MASTER RULE:** Do NOT start new intelligence engines until `company_fundamentals_master_engine.py` is complete.

---

## SECTION 7 — CRITICAL PATH (Next Development Sequence)

```
STEP 1  Company Fundamentals Master Engine        [Phase 4] — NEXT
        File: engines/fundamentals/company_fundamentals_master_engine.py
        Output: data/NSE/equity_master/company_fundamentals_master.csv

STEP 2  Industry Master Engine                    [Phase 4]
        File: engines/fundamentals/industry_master_engine.py
        Goal: 95%+ industry coverage for all 2123 symbols

STEP 3  NSE Constituents Auto Downloader          [Phase 3 Enhancement]
        File: engines/foundation/nse_constituents_engine_v1.py (expand)
        Replace manual CSV downloads for Nifty500, sector indices, theme indices

STEP 4  Classification Engine V4 Completion       [Phase 2]
        File: engines/fundamentals/classification_engine_v4.py
        Goal: Fix ADANIPORTS → AEROSPACE bug; reach 95%+ coverage

STEP 5  Participant Intelligence Layer            [New Module]
        Files: engines/participant/ (new directory)
        ADR: ADR-016 approved
        Engines: Flow, Conviction, Divergence, SmartMoney, RetailSentiment

STEP 6  Sector Intelligence Expansion            [Phase 4 of Roadmap]
        Engines: SectorRotation, SectorCapitalFlow, SectorMomentum, SectorOpportunity

STEP 7  Corporate Intelligence Layer              [Phase 5]
        Per ADR-020: Results, Shareholding, Announcements, CorporateActions

STEP 8  Management Intelligence Layer             [Phase 6]
        Per ADR-020: ConferenceCalls, Transcripts, ManagementSentiment

STEP 9  Bull Run Probability Engine               [Phase 8]
        File: engines/intelligence/bull_run_probability_engine.py
        Inputs: All above layers combined

STEP 10 Stock Ranking Engine                      [Phase 8]
        File: engines/intelligence/stock_ranking_engine.py
```

---

## SECTION 8 — FILES MARKED FOR REMOVAL

These files are confirmed redundant. Do NOT delete without user confirmation.
Mark them with a comment `# LEGACY - SCHEDULED FOR REMOVAL` first.

| File | Reason |
|------|--------|
| `engines/index_intelligence_engine_v1_backup.py` | Backup copy of production engine. Production is `index_intelligence_engine.py` |
| `engines/intelligence/index_intelligence_engine_v2.py` | 80-line stub, not production-ready. Development should start fresh |
| `engines/intelligence/leadership_persistence_engine_v2.py` | 30-line stub with no implementation |
| `engines/fundamentals/security_master_engine.py` | Superseded by `security_master_engine_v2.py` (502 lines) |
| `engines/classification_engine.py` | V1, superseded by `auto_classification_engine_v2.py` and `classification_engine_v4.py` |

---

## SECTION 9 — KNOWN ISSUES AND TECHNICAL DEBT

### Issue 1 — Classification Coverage Gap
- **Problem:** Only 783 / 2123 symbols classified (36.9%)
- **Root Cause:** Industry Master missing; keyword-only classification is insufficient
- **Example Bug:** ADANIPORTS → classified as AEROSPACE (wrong); should be LOGISTICS/PORTS
- **Fix:** Complete Industry Master Engine + Classification V4

### Issue 2 — Data Path Inconsistency
- **Problem:** Docs reference `data/NSE Data/` (with space), code uses `data/bhavcopy/` or `data/NSE/`
- **Fix:** Standardize all engines to use `data/NSE/` for structured data and `data/bhavcopy/` for raw bhavcopy
- **Update:** DATA_ARCHITECTURE.md needs path correction

### Issue 3 — Legacy Root-Level Engines
- **Problem:** Several engines live at `engines/` root that should be in subdirectories
- `equity_master_engine.py` → should be `engines/fundamentals/`
- `bhavcopy_import_engine.py` → should be `engines/acquisition/`
- `cache_manager.py` → should be `engines/common/`
- `auto_classification_engine_v2.py` → should be `engines/fundamentals/`
- `sector_leadership_persistence_engine.py` → should be `engines/intelligence/`
- **Risk:** Do NOT move without updating all imports in fetchers/ and main.py

### Issue 4 — Fetchers Directory Is Legacy Flat Structure
- **Problem:** `fetchers/` contains engines that should be in `engines/intelligence/` or `engines/participant/`
- **Fix:** Migrate gradually as modules are refactored. Do not migrate all at once.

### Issue 5 — Empty Engine Subdirectories
- `engines/classification/` — empty, content belongs in `engines/fundamentals/`
- `engines/corporate/` — placeholder for Phase 5
- `engines/management/` — placeholder for Phase 6
- `engines/orchestration/` — placeholder for main.py evolution
- These are fine as future placeholders but should have `__init__.py` files

### Issue 6 — BSE Data Directory Has No Engines
- `data/BSE/` exists but there are no BSE acquisition engines
- No BSE development is in scope yet; do not build BSE engines until NSE foundation is solid

### Issue 7 — data/aggregated Has No Engines
- `data/aggregated/` exists but no corresponding engines
- This may be an artifact of an early experiment; investigate before using

### Issue 8 — Institutional Trend Engine Incomplete
- Status in docs: "In Progress"
- `fetchers/institutional_trend_engine.py` exists but completeness unknown
- Review before moving to Phase 4

---

## SECTION 10 — ARCHITECTURE DECISION RECORDS (ADR) INDEX

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Raw Data Never Modified | ✅ Active |
| ADR-002 | NSE Data Structure | ✅ Active |
| ADR-003 | On Demand Cache | ✅ Active |
| ADR-004 | Listing Date Aware Processing | ✅ Active |
| ADR-005 | nselib First Policy | ✅ Active |
| ADR-006 | Gross Flow Preservation | ✅ Active |
| ADR-007 | Sector-Theme-Stock Capital Flow Model | ✅ Active |
| ADR-008 | Cache Maintenance Strategy | ✅ Active |
| ADR-009 | Intelligence Layer Separation | ✅ Active |
| ADR-010 | AI First User Experience | ✅ Active |
| ADR-011 | Infographic First Visualization | ✅ Active |
| ADR-012 | Research Before Development | ✅ Active |
| ADR-013 | Broker Independence Architecture | ✅ Active |
| ADR-014 | Module Driven Development | ✅ Active |
| ADR-015 | Documentation Mandatory Before Release | ✅ Active |
| ADR-016 | Participant Intelligence Framework | ✅ Accepted |
| ADR-018 | Market Data Reliability Framework | ✅ Active |
| ADR-019 | Data Integrity, Recovery & Backup Framework | ✅ Active |
| ADR-020 | Corporate Intelligence Layer | ✅ Approved |

---

## SECTION 11 — CODING STANDARDS (MANDATORY)

### File Delivery
- Always provide COMPLETE files, never partial snippets
- Files must be copy-paste ready without modification
- Include all imports, class definitions, and error handling

### Git Workflow
After every code change provide:
```bash
git add <specific files>
git commit -m "phase-X: description of change"
git push origin main
```

### Engine Template (every new engine must follow)
```python
"""
Engine Name
Phase X — Purpose description
"""

from pathlib import Path
from engines.common.logger import get_logger
from engines.common.config import ProjectConfig

logger = get_logger(__name__)

class EngineNameEngine:
    def __init__(self):
        self.config = ProjectConfig()
        self.data_dir = self.config.data_dir / "NSE"

    def run(self):
        logger.info("Starting EngineNameEngine")
        try:
            self._validate_inputs()
            result = self._process()
            self._save(result)
            logger.info("EngineNameEngine complete")
            return result
        except Exception as e:
            logger.error(f"EngineNameEngine failed: {e}")
            raise

    def _validate_inputs(self):
        pass

    def _process(self):
        pass

    def _save(self, df):
        pass

if __name__ == "__main__":
    engine = EngineNameEngine()
    engine.run()
```

### Data Governance Rules
1. Raw data is NEVER modified after download
2. All derived outputs must be rebuildable from raw data
3. Cache is disposable — never the source of truth
4. Always use listing-date-aware processing (check equity_master listing date)
5. Optimize for 4500+ symbols universe
6. Heavy processing only after market hours or weekends
7. Every engine must handle missing data gracefully with recovery

### Validation Requirements (every engine)
- Schema validation (verify column names and types)
- Completeness validation (detect and log missing records)
- Integrity validation (expected vs actual record counts)
- Recovery mechanism (auto-repair or flag for manual review)

---

## SECTION 12 — COMPANY FUNDAMENTALS MASTER ENGINE (Next Build)

This is the #1 priority. Do not start anything else until this is complete.

**Purpose:** Create the authoritative company master dataset that underpins Classification V4,
Corporate Intelligence, and the Bull Run engine.

**Required Outputs:**
- `data/NSE/equity_master/company_fundamentals_master.csv`
- `data/NSE/equity_master/fundamentals_review_queue.csv`
- `data/NSE/equity_master/fundamentals_coverage_report.csv`

**Required Fields:**
```
symbol, company_name, isin, listing_date, series, status,
industry_nse, sector_platform, theme_platform,
market_cap_category, business_profile,
fii_holding_pct, dii_holding_pct, promoter_holding_pct,
last_updated
```

**Data Sources (in priority order):**
1. NSE Equity Master (nselib)
2. NSE Industry/Sector classification
3. Screener.in (validation layer only)
4. Manual override file for exceptions

**Success Criteria:**
- 95%+ of 2123 symbols have valid industry mapping
- ADANIPORTS maps to LOGISTICS / PORTS (not AEROSPACE)
- Zero null isin values
- Zero null listing_date values

---

## SECTION 13 — MODULE COMPLETION PERCENTAGES (June 2026)

```
Governance Layer           100%   (all docs complete)
Architecture Layer         100%   (all ADRs complete)
Data Foundation             40%   (bhavcopy done, fundamentals missing)
Participant Intelligence     0%   (ADR-016 approved, no engines yet)
Institutional Intelligence  75%   (trend engine in progress)
Sector Intelligence         45%   (heatmap/persistence done, rotation planned)
Theme Intelligence          35%   (heatmap/persistence done, rotation planned)
Stock Intelligence          10%   (foundation only)
Fundamental Intelligence     5%   (engines exist but incomplete)
AI Platform                 15%   (architecture only)
GUI Platform                10%   (architecture only)
Execution Platform           5%   (architecture only)
```

**Overall Platform:** ~35-40% complete

---

## SECTION 14 — ENHANCEMENT OPPORTUNITIES

These are improvements that can be made without breaking existing functionality:

### Immediate (Phase 4 work)
1. **Company Fundamentals Master Engine** — #1 priority; unblocks everything
2. **Industry Master Engine** — fix classification bugs; 95%+ coverage target
3. **NSE Constituents Auto Downloader** — replace manual CSV downloads

### Short-Term (after Phase 4)
4. **Participant Intelligence Layer** — new `engines/participant/` directory per ADR-016
5. **Sector Rotation Engine** — connects institutional regime to sector momentum
6. **Institutional Trend Engine completion** — finish what's in progress in fetchers/

### Structural Improvements
7. **Add `__init__.py`** to all empty engine directories
8. **Path standardization** — fix all references from `data/NSE Data/` to `data/NSE/`
9. **Migrate root-level engines** to proper subdirectories (careful with imports)
10. **Consolidate fetchers/** — gradually move to `engines/intelligence/` as engines mature

### Data Quality
11. **Listing-date validation** — audit all engines for compliance with ADR-004
12. **Gross flow preservation** — implement buy/sell separation in institutional data (per ADR-006)
13. **Data integrity dashboard** — create a daily health check for all data layers

---

## SECTION 15 — LONG-TERM VISION (Generation 4)

```
Generation 1 (Done)      Institutional Intelligence Platform
Generation 2 (In Progress) Participant Intelligence Platform
Generation 3 (Planned)   Capital Flow Intelligence Platform
Generation 4 (Vision)    Investment Operating System
```

The Investment Operating System will:
- Track all participant capital flows
- Detect sector/theme/stock rotation early
- Explain movement through fundamentals
- Score management quality via AI analysis of concalls
- Detect governance risks proactively
- Generate bull run probability scores
- Manage portfolios with risk controls
- Execute through broker adapters (Zerodha, Dhan, Upstox, Angel One, Fyers)
- Deliver all intelligence through AI chat + infographic dashboards

---

## SECTION 16 — DOCUMENT REGISTRY

| Document | Location | Purpose |
|----------|----------|---------|
| This file | `docs/CLAUDE_MASTER_DEV_GUIDE.md` | Master Claude guide |
| Project state | `docs/PROJECT_MASTER_STATE.md` | Phase status + priorities |
| Architecture | `docs/architecture/MASTER_ARCHITECTURE.md` | 10-layer architecture |
| Data architecture | `docs/architecture/DATA_ARCHITECTURE.md` | Data flow + storage |
| Roadmap | `docs/governance/MASTER_ROADMAP.md` | Development phases |
| Module registry | `docs/governance/MODULE_REGISTRY.md` | Module inventory |
| Checklist | `docs/governance/MASTER_CHECKLIST.md` | Build tracker |
| Governance | `docs/governance/DEVELOPMENT_GOVERNANCE.md` | Dev standards |
| ADR decisions | `docs/decisions/ADR-0XX-*.md` | Architecture decisions |
| Module docs | `docs/modules/` | Per-module specs |
| Legacy docs | `docs/legacy/` | Old docs (superseded, do not use) |

---

END OF CLAUDE MASTER DEVELOPMENT GUIDE

This document must be updated whenever:
- A new phase is completed
- An ADR is added or changed
- A file is removed from the project
- The critical path changes
