# CLAUDE MASTER DEVELOPMENT GUIDE
## Capital Flow Intelligence Platform
### Version 4.25 — July 2026

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

## SECTION 6 — PHASE BUILD STATUS (2026-07-09)

**ALL 25 CORE PHASES + A/B/C/D/FPI/KU/AF/CH/TI/SH/UI-S COMPLETE**

| Phase | Name                          | Status   | Notes |
|-------|-------------------------------|----------|-------|
| 1     | Foundation Layer              | COMPLETE | bhavcopy import, equity master, cache |
| 2     | Classification Layer          | COMPLETE | 2123 symbols, 27 sectors, 4C = 99.53% |
| 3     | Index Intelligence            | COMPLETE | 139 indices, index_membership.csv |
| 4A-4D | Fundamentals + Industry       | COMPLETE | 4A company fundamentals, 4B industry master, 4C classif V4, 4D constituents |
| 5A-5C | Participant Intelligence      | COMPLETE | F&O 2016-2026, Cash 2024-2026, 2581 rows |
| 6A-6C | Sector Intelligence           | COMPLETE | 74269 rows sector capital flows |
| 7A-7C | Corporate Intelligence        | COMPLETE | block/bulk deals, event calendar, corp action signals |
| 8A-8B | Bull Run Engine               | COMPLETE | 2441 symbols, 225 EMERGING |
| 9     | Alert System (Telegram)       | COMPLETE | 10 alert types P1-P10, APScheduler |
| 10    | FastAPI Backend               | COMPLETE | 20 endpoints, port 8001, WebSocket |
| 11    | React GUI                     | COMPLETE | 15 pages, KLineChart Pro OHLCV, inline styles |
| 12    | ML Intelligence               | COMPLETE | XGBoost+LightGBM, 24 features, 4 outputs |
| 13    | RAG Knowledge Base            | COMPLETE | FAISS+BM25, 6 domain indexes |
| 14    | Chatbot (multi-provider LLM)  | COMPLETE | Groq primary, 11 tools, /api/chat |
| 15    | Financial Results + SHP       | COMPLETE | 4181 XBRL rows; 76170 shareholding rows (8 quarters) |
| 16    | Management Intelligence       | COMPLETE | holding trends, announcements, sentiment |
| 17    | Symbol Change History         | COMPLETE | 1038 symbol renames |
| 18    | Corporate Announcements       | COMPLETE | NSE XBRL announcement fetcher |
| 19    | Daily Refresh Scheduler       | COMPLETE | APScheduler 18:00 IST weekday pipeline |
| 20    | Portfolio Engine              | COMPLETE | transactions.csv, P&L, allocation |
| 21    | Backtesting Framework         | COMPLETE | 3 strategies, 5 horizons, Sharpe metrics |
| 22    | Broker Adapter (R/O)          | COMPLETE | Dhan + CSV adapters; broker sync |
| 23    | Research Platform             | COMPLETE | 2406-symbol screener, comparator, notes |
| 24    | Execution Platform            | COMPLETE | risk engine, paper/live orders, signal recommender |
| 25    | Commercial Platform           | COMPLETE | SQLite sessions, roles, API keys |
| A     | Technical + F&O Intelligence  | COMPLETE | technical_indicators.csv 2718 rows, fno_intelligence.csv 211 rows |
| B     | Trade Intelligence Card       | COMPLETE | 7-factor TradeIntelligenceCard.tsx |
| C     | Trade Conviction Alerts       | COMPLETE | trade_conviction_scores.csv 2406 rows, alerts P9/P10 |
| D     | Chat UI                       | COMPLETE | ChatPage.tsx, session-aware, 6 suggested prompts |
| FPI   | Sector FPI Fortnightly        | COMPLETE | 8690 rows sector-level FPI data |
| KU    | Kundli + Gann Intelligence    | COMPLETE | astro/gann engines |
| AF    | AstroFinance                  | COMPLETE | planetary_intelligence_layer.py, 209 rows |
| CH    | KLineChart Pro Charts         | COMPLETE | klinecharts v9.8.12, custom indicators |
| TI    | Technical Indicators          | COMPLETE | RSI/MACD/ATR/BB/OBV/ADX columns added |
| SH    | Shareholding XBRL Fix + 8-score| COMPLETE | fraction-scale fix, 8-panel shareholding UI |
| UI-S  | Sectors + Social Pulse UI     | COMPLETE | updated sector dashboard |

**INVESTMENT OPERATING SYSTEM is live.** See `docs/PROJECT_MASTER_STATE.md` for current intelligence output row counts.

---

## SECTION 7 — CRITICAL PATH (2026-07-09)

**ALL PHASES COMPLETE.** The platform is a fully operational Investment Operating System.

Current development focus: incremental intelligence improvements, data quality, new ADRs (next: ADR-022).

Known open issues (low priority):
- ADANIPORTS classifies as AEROSPACE (wrong) — Industry Master override coverage limited
- Cash market flows 2026-02-19 tz-aware/naive mixing in NSE API response — fix pending
- Extended shareholding backfill pre-Q1FY24 limited by NSE XBRL archive availability
- Order Book Intelligence not yet built (future module)
- Concall audio/transcript AI analysis not yet built (future module)

For new development: always run `phase-gatekeeper` agent at start (architecture freeze) and end (completion ceremony).

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

**Next ADR: ADR-022**

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Raw Data Never Modified | Active |
| ADR-002 | NSE Data Structure | Active |
| ADR-003 | On Demand Cache | Active |
| ADR-004 | Listing Date Aware Processing | Active |
| ADR-005 | nselib First Policy | Active |
| ADR-006 | Gross Flow Preservation | Active |
| ADR-007 | Sector-Theme-Stock Capital Flow Model | Active |
| ADR-008 | Cache Maintenance Strategy | Active |
| ADR-009 | Intelligence Layer Separation | Active |
| ADR-010 | AI First User Experience | Active |
| ADR-011 | Infographic First Visualization | Active |
| ADR-012 | Research Before Development | Active |
| ADR-013 | Broker Independence Architecture | Active |
| ADR-014 | Module Driven Development | Active |
| ADR-015 | Documentation Mandatory Before Release | Active |
| ADR-016 | Participant Intelligence Framework | Accepted — IMPLEMENTED |
| ADR-017 | (see docs/decisions/) | Active |
| ADR-018 | Market Data Reliability Framework | Active |
| ADR-019 | Data Integrity, Recovery & Backup Framework | Active |
| ADR-020 | Corporate Intelligence Layer | Accepted — IMPLEMENTED |
| ADR-021 | Alert System Architecture | Accepted — IMPLEMENTED |

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

## SECTION 12 — PLATFORM COMPLETION NOTE (2026-07-09)

**ALL PHASES COMPLETE.** The Company Fundamentals Master Engine (Phase 4A) was completed
as part of the Phase 4A-4D sequence. All downstream intelligence layers are operational.

**Current canonical intelligence outputs** — see `docs/PROJECT_MASTER_STATE.md` for row counts and file list.

**Key architecture files:**
- `engines/common/config.py` — authoritative config and canonical data paths
- `engines/common/llm_client.py` — multi-provider LLM fallback chain (Groq → Cerebras → Gemini → OpenRouter)
- `engines/ai/chatbot/chat_engine.py` — chatbot using Groq llama-3.3-70b-versatile primary
- `engines/orchestration/refresh_scheduler.py` — daily 18:00 IST APScheduler pipeline
- `backend/main.py` — FastAPI app, port 8001, 20 endpoints + WebSocket
- `frontend/` — React 18 + TypeScript + Vite, port 5173, inline styles via C.* tokens
- `start.ps1` — idempotent launcher for both servers

---

## SECTION 13 — MODULE COMPLETION PERCENTAGES (2026-07-09)

```
Governance Layer           100%   (all docs complete)
Architecture Layer         100%   (all ADRs through ADR-021 complete; next ADR-022)
Data Foundation            100%   (bhavcopy, equity master, fundamentals, shareholding)
Participant Intelligence   100%   (5A/5B/5C complete, 2581 rows)
Institutional Intelligence 100%   (superseded by Phase 5 engines)
Sector Intelligence        100%   (6A/6B/6C complete, 74269 rows)
Theme Intelligence          35%   (heatmap/persistence done; rotation engines planned)
Stock Intelligence         100%   (8A/8B + Phase A technical + TI indicators)
Fundamental Intelligence   100%   (Phase 15/15B/16 complete)
AI Platform                100%   (Phase 12 ML + Phase 13 RAG + Phase 14 Chatbot)
GUI Platform               100%   (Phase 10 FastAPI + Phase 11 React, 15 pages)
Execution Platform         100%   (Phase 24 complete; paper + live orders)
Alert System               100%   (Phase 9 complete, 10 alert types P1-P10)
Portfolio / Backtest       100%   (Phase 20 + Phase 21 complete)
Broker Adapters            100%   (Phase 22 — Dhan + CSV adapters)
Research Platform          100%   (Phase 23 — 2406-symbol screener + notes)
Commercial Auth            100%   (Phase 25 — SQLite sessions + API keys)
AstroFinance / Gann        100%   (Phase KU + AF complete)
KLineChart Pro             100%   (Phase CH complete — custom indicators)
```

**Overall Platform: 100% complete** (Investment Operating System LIVE as of 2026-07-09)

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

## SECTION 15 — PLATFORM GENERATIONS STATUS (2026-07-09)

```
Generation 1 (COMPLETE)   Institutional Intelligence Platform
Generation 2 (COMPLETE)   Participant Intelligence Platform
Generation 3 (COMPLETE)   Capital Flow Intelligence Platform
Generation 4 (COMPLETE)   Investment Operating System (Phases 17-25)
Generation 5 (COMPLETE)   Commercial Platform (Phase 25 auth/API keys)
Generation 6 (COMPLETE)   AstroFinance + KLineChart Pro + TI + SH + UI-S phases
```

The Investment Operating System is LIVE:
- Tracks all participant capital flows (FII/DII/PRO/CLIENT, F&O + Cash)
- Detects sector/theme/stock rotation early (74269-row sector flows)
- Explains movement through fundamentals (4181 XBRL rows, 76170 shareholding rows)
- Scores management quality via AI sentiment (471 symbols, Claude API)
- Generates bull run probability scores (2441 symbols)
- Manages portfolios with risk controls (Phase 20/24)
- Executes through Dhan broker adapter (Phase 22/24)
- Delivers all intelligence through Groq-powered AI chat + KLineChart Pro dashboards

**Next generation**: Theme Intelligence expansion (35% only), concall transcript analysis,
Order Book Intelligence, BSE data layer.

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
