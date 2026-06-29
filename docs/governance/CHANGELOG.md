# CHANGELOG

## Project

Capital Flow Intelligence Platform

---

# Purpose

This document records all major project milestones, architecture decisions, strategic changes, documentation updates, and development achievements.

The changelog serves as the historical record of the platform's evolution.

---

# Versioning Philosophy

The platform follows milestone-based versioning.

Major versions are created when:

* Architecture changes significantly
* New intelligence layers are introduced
* Strategic direction changes
* Major modules are completed

---

# Version 2.6

Phase 4C — Classification Engine V4 Completion

Date:

2026-06-30

Status:

Completed

---

## Summary

Rewrote `classification_engine_v4.py` as a proper 5-level hierarchical classifier using
industry_master as primary lookup. Applied symbol-level corrections for all 71 previously
OTHER symbols, reducing OTHER from 71 to 10 (genuinely miscellaneous businesses).
Coverage improved from 96.7% → 99.53% non-OTHER. Also writes `company_classification_v4.csv`
with source tracking (INDUSTRY_MASTER / SYMBOL_CORRECTION / KEYWORD_MATCH / MANUAL_OVERRIDE).

---

## Deliverables

### Engine
- `engines/fundamentals/classification_engine_v4.py` — complete rewrite (hierarchical, 5 levels, all guardrails)

### Outputs
- `data/reference/company_classification_v4.csv` — 2123 rows, 7 cols (with SOURCE tracking)
- `data/NSE/equity_master/company_fundamentals_master.csv` — UPDATED (99.53% coverage)
- `data/NSE/equity_master/classification_coverage_report.csv` — metrics snapshot
- `data/NSE/equity_master/classification_review_queue.csv` — 10 symbols needing manual review
- `data/NSE/equity_master/classification_sector_counts.csv` — per-sector counts

### Key Corrections in SYMBOL_CORRECTIONS Dict (60 symbols reclassified from OTHER)
- ICICIAMC / NAM-INDIA / UTIAMC → AMC / FINANCIALISATION
- SUPRAJIT / MAJESAUT / PTL → AUTO / EV_TRANSITION
- HARSHA / INTLCONV / SANGHVIMOV / DYNAMATECH / OMNI / TEXINFRA → CAPITAL_GOODS
- INDIQUBE / NESCO / NIRLON / SMARTWORKS / EFCIL / HEMIPROP / WEWORK / MERCANTILE → REALTY
- CYBERTECH / GENESYS / SASKEN / DSSL / REDINGTON → IT / DIGITAL_INDIA
- SPCENET → TELECOM / DIGITAL_INDIA
- DEVYANI / ADVENTHTL → HOSPITALITY / PREMIUMISATION
- GICL / TARACHAND / TVSSCS → LOGISTICS / LOGISTICS_MODERNISATION
- DBSTOCKBRO / ALANKIT / CMSINFO / RADIANTCMS / PRUDENT / ICDSLTD → FINANCIAL_SERVICES
- SOUTHWEST / KOTYARK → ENERGY; SHIVAUM / GOYALALUM / MSTCLTD → METAL
- RUCHINFRA / ELITECON → INFRASTRUCTURE; VIKASLIFE / FLEXITUFF / RUBFILA / SICAGEN / IWP → CHEMICALS
- KOTHARIPRO / VINCOFE / GOLDIAM → FMCG; UMAEXPORTS → AGRICULTURE; LAHOTIOV → TEXTILES
- TOUCHWOOD → MEDIA; ACEINTEG → DEFENCE; CNL → RETAIL; BLUSPRING → POWER
- STCINDIA / MMTC → DIVERSIFIED / PSU_REVIVAL

### Remaining OTHER (10 — genuinely miscellaneous, no dominant sector)
AARVI, AKG, DEVX, KAPSTON, KRYSTAL, LANDSMILL, METROGLOBL, QUESS, SIS, UDS
(staffing / facility management / export trading / startup incubator)

### Final State after Phase 4C
- Total symbols: 2,123
- Classified (non-OTHER): 2,113 (99.53%)
- OTHER: 10 (0.47%)
- UNCLASSIFIED: 0

---

# Version 2.5

Phase 4B — Industry Master Engine

Date:

2026-06-29

Status:

Completed

---

## Summary

Built the authoritative industry_nse → sector_platform + theme_platform lookup table covering
all 183 unique NSE industry classifications across 2123 symbols. Immediately applied the master
back to improve company_fundamentals_master.csv to 96.7% sector coverage and 100% theme coverage.

---

## Deliverables

### Engine
- `engines/fundamentals/industry_master_engine.py` — complete rewrite (class-based, all guardrails)

### Outputs
- `data/reference/mapping/industry_master.csv` — 183 rows, 10 columns (authoritative lookup table)
- `data/NSE/equity_master/company_fundamentals_master.csv` — UPDATED (96.7% sector, 100% theme)

### Bug Fixes (in engine development)
- `_manual_theme` column NaN propagation — fixed by initializing to "" before loop
- `float('nan')` is truthy in Python — fixed with `pd.notna()` guard

### Industry Groups (10 groups across 183 industries)
- MANUFACTURING: 59 industries
- CONSUMER: 31 industries
- INFRASTRUCTURE_ENERGY: 30 industries
- FINANCIAL_SERVICES: 20 industries
- TECHNOLOGY: 19 industries
- HEALTHCARE: 10 industries
- REAL_ESTATE: 6 industries
- OTHER: 5 industries (DISTRIBUTORS, DIVERSIFIED COMMERCIAL SERVICES, etc.)
- AGRICULTURE: 2 industries
- DIVERSIFIED: 1 industry

### Key Corrections Applied
- DIVERSIFIED COMMERCIAL SERVICES (37 cos): IT → OTHER (staffing/facility mgmt ≠ IT)
- COAL (3 cos): POWER → ENERGY with PSU_REVIVAL theme
- PACKAGING (31 cos): OTHER → CHEMICALS with CHINA_PLUS_ONE theme
- PAPER AND PAPER PRODUCTS (21 cos): OTHER → CHEMICALS
- FURNITURE HOME FURNISHING (10 cos): OTHER → REALTY
- HOUSEWARE (4 cos): OTHER → FMCG
- AMUSEMENT PARKS (3 cos): OTHER → HOSPITALITY

### Final State after Phase 4B
- ISIN: 100%
- Sector classified (non-OTHER): 96.7%
- Theme populated: 96.3% (strings only; 3.7% = OTHER sector → no theme, by design)
- No industries in review queue (all 183 at high confidence)

---

# Version 2.4

Phase 4A — Company Fundamentals Master Engine

Date:

2026-06-29

Status:

Completed

---

## Summary

Built the authoritative company master for all 2123 EQ active symbols.
Passes all 4 spec success criteria. Resolves the ADANIPORTS→LOGISTICS classification bug.
Output at `data/NSE/equity_master/company_fundamentals_master.csv`.

---

## Deliverables

### Engine
- `engines/fundamentals/company_fundamentals_master_engine.py` — complete rewrite (class-based, all guardrails)

### Outputs
- `data/NSE/equity_master/company_fundamentals_master.csv` — 2123 rows, 15 columns
- `data/NSE/equity_master/fundamentals_review_queue.csv` — 103 symbols for manual review
- `data/NSE/equity_master/fundamentals_coverage_report.csv` — coverage metrics

### Supporting Data
- `data/reference/mapping/manual_override.csv` — created with 8 known misclassification corrections

### Success Criteria (all PASS)
- industry_nse populated: 100% (spec: 95%+)
- ISIN null count: 0 (spec: ZERO)
- listing_date null count: 0 (spec: ZERO)
- ADANIPORTS sector: LOGISTICS (spec: LOGISTICS/PORTS not AEROSPACE)

### Coverage
- ISIN: 100%
- Sector classified (non-OTHER): 95.1%
- Theme classified: 94.8%
- Market cap known: 100%

### Key Fixes Applied
- ADANIPORTS: CHEMICALS (Screener error) → LOGISTICS via manual_override.csv
- ONGC: AGRI (Screener error) → ENERGY via manual_override.csv
- TCS + consulting firms: PROFESSIONAL_SERVICES → IT via SECTOR_NORMALIZE fix
- Packaging companies: mapped to CHEMICALS (packaging materials)
- Education companies: mapped to HEALTHCARE (theme alignment)

### Architecture
- SECTOR_NORMALIZE dict: 44 mappings (28 canonical + 16 legacy/alternate names)
- SECTOR_TO_THEME dict: 25 sector → theme mappings (basic; Phase 4B refines via industry_master)
- manual_override.csv applied last — immutable (G-C-02)
- All guardrails: atomic write, schema validation, empty df guard, universe size check

---

# Version 2.3

ML / AI / Chatbot Architecture — Modules 14, 15, 16 Added

Date:

2026-06-29

Status:

Completed

---

## Summary

Designed and documented ML Intelligence, AI Knowledge Base (RAG), and Chatbot Platform layers.
Added 3 new modules (14, 15, 16) to MODULE_REGISTRY. Platform now has a clear roadmap from raw
NSE data through ML scoring → RAG retrieval → conversational AI interface. Claude API
(claude-sonnet-4-6) selected as the LLM backbone. Chat history restructured to module-wise append files.

---

## Deliverables

### Architecture Document
- `docs/architecture/ML_AI_CHATBOT_ARCHITECTURE.md` — full ML/AI/Chatbot spec (8 sections)

### New Modules
- Module 14: ML Intelligence Layer (0%, Planned) — XGBoost/LightGBM accumulation, sector rotation, bull run, anomaly, NLP classification
- Module 15: AI Knowledge Base / RAG (0%, Planned) — FAISS + BM25 hybrid retrieval over all intelligence outputs
- Module 16: Chatbot Platform (0%, Planned) — 7 agents, tool registry, WebSocket, React chat UI

### Module Updates
- Module 07 (AI Platform): Architecture expanded with full Claude API integration spec

### Process Changes
- Chat history restructured to module-wise append files (`chat history/module_NN_<name>.md`)
- Old session-based files deprecated — all new entries append to module files

### ADR References
- ADR-021: ML Intelligence Layer
- ADR-022: RAG Knowledge Base
- ADR-023: Chatbot / Conversational AI

---

## Build Dependencies (ML/AI/Chatbot cannot start until)

1. Phase 4A (Company Fundamentals Master Engine) — unblocks ML-1 Feature Engineering
2. Phase 3B outputs (intelligence CSVs) — unblocks RAG-1 (available now for partial indexing)
3. Phase 6 (Sector Rotation Engines) — unblocks ML-4 Sector Rotation Model

---

# Version 2.2

GUI Architecture Planning — React + FastAPI Implementation Plan

Date:

2026-06-29

Status:

Completed

---

## Summary

Designed and documented the full React-based GUI for the Capital Flow Intelligence Platform.
Created `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` covering technology stack, design system,
13 pages, 13 build phases, FastAPI backend contract, state management, and IST-aware utilities.
Module 08 (GUI Platform) advances from 10% to 25%.

---

## Deliverables

### Architecture Document
- `docs/architecture/GUI_IMPLEMENTATION_PLAN.md` — 15-section complete build specification

### Technology Decisions (Locked)
- Frontend: React 18 + TypeScript + Vite
- Styling: Tailwind CSS + CSS Variables (dark terminal theme)
- Charts: Recharts (heatmaps/flows) + TradingView Lightweight Charts (OHLCV)
- Server State: TanStack Query v5
- Client State: Zustand
- Routing: React Router v6
- Backend: FastAPI + Uvicorn (already in requirements.txt)
- Real-time: WebSocket — live flow ticker during market hours only

### Design System (Defined)
- Dark terminal palette (#0A0D14 background)
- Participant colors: FII=Blue, DII=Indigo, PRO=Amber, CLIENT=Pink
- Score gradient: Red (0-30) → Amber (30-60) → Green (60-80) → Emerald (80-100)
- 3-Second Rule: market regime + FII net + top sector visible on landing

### Pages Designed (13 total)
Dashboard, Market, Sectors, SectorDetail, Themes, ThemeDetail,
Stocks (screener), StockDetail, Portfolio, Research, AI Assistant, Reports, Settings

### Build Phases Defined (GUI-1 through GUI-13)
GUI-1: AppShell → GUI-4: FastAPI data wiring (needs Phase 4A) → GUI-9: AI Assistant → GUI-13: Auth

### Key Components Specified
- `CapitalFlowCascade` — Sankey: Market → Sector → Theme → Stock
- `SectorHeatmap` — Recharts Treemap (size=market cap, color=flow score)
- `FlowCard` — FII/DII/PRO/CLIENT buy/sell/net with 7-day sparkline
- `OhlcvChart` — TradingView LC with delivery % + FII flow overlay panes

### FastAPI Contract
- 14 REST endpoints + 1 WebSocket (`/ws/live-flow`)
- Standard envelope: `{ status, data, meta: { generated_at, data_as_of, cache_hit } }`

### Session Protocol
- `chat history/session_2026_06_29_gui_plan.md` saved
- Memory updated in `memory/project_fii_dii.md`

---

# Version 2.1

Phase 3B: Guardrail Utility Library + Complete Test Suite

Date:

2026-06-29

Status:

Completed

---

## Summary

Implemented the complete guardrail utility library (`engines/common/guardrails.py`) with 55
functions covering all 12 guardrail sections, paired with a full pytest test suite across 16 test
files (~400 test cases). Introduced phased development protocol: every phase ends with a session
log saved to `chat history/`, memory update, and CHANGELOG entry.

---

## Deliverables

### Guardrail Library
- `engines/common/guardrails.py` — 55 utility functions, all logging at DEBUG level
- All 12 guardrail sections covered (Data, API, Symbol, Price, Classification, Corporate Actions,
  Intelligence, Financial Results, Trading Calendar, Institutional, System, Performance)

### Test Infrastructure
- `pytest.ini` — DEBUG logging to `tests/logs/pytest_debug.log`
- `tests/conftest.py` — 10 shared fixtures + autouse `log_test_boundaries`
- `requirements.txt` — added pytest>=8.0.0 and pytest-mock>=3.0.0

### Guardrail Test Files (tests/guardrails/)
12 files covering G-D-01 through G-PERF-04 (all 55 rules)

### Edge Case Test Files (tests/edge_cases/)
4 files covering India-specific edge cases: mergers/IPOs, circuit breakers,
PSU/holding co classification, institutional T+1 lag, Budget Day, F&O expiry

### Supporting Files
- `tests/CLAUDE.md` — test directory context for future sessions
- `chat history/session_2026_06_29_phase3b_guardrails_and_tests.md` — session log
- `memory/project_fii_dii.md` — updated with Phase 3B completion + phased dev protocol

### Process Improvements
- Phased development protocol established (session log + memory update + changelog after every phase)

---

# Version 2.0

Claude AI Development Infrastructure Release

Date:

2026-06-29

Status:

Completed

---

## Summary

Established complete AI-assisted development infrastructure: master Claude guide,
directory-level skill files (CLAUDE.md), platform guardrails, and edge case registry.
This release makes Claude a self-sufficient platform architect without re-reading project
docs on every session.

---

## Deliverables

### Claude Skill Files (CLAUDE.md)
- `CLAUDE.md` (root) — master project rules, critical path, guardrail summary
- `engines/CLAUDE.md` — engine directory map, template, compliance checklist
- `engines/common/CLAUDE.md` — shared utility reference card
- `engines/fundamentals/CLAUDE.md` — Phase 4 spec, classification edge cases
- `engines/acquisition/CLAUDE.md` — data download rules, recovery patterns
- `engines/intelligence/CLAUDE.md` — planned intelligence engine specs
- `engines/foundation/CLAUDE.md` — index/constituent management
- `data/CLAUDE.md` — canonical data paths, lifecycle, edge cases
- `fetchers/CLAUDE.md` — legacy context, migration roadmap
- `docs/CLAUDE.md` — documentation governance, ADR creation rules
- `alerts/CLAUDE.md` — Telegram delivery rules
- `sheets/CLAUDE.md` — Google Sheets integration rules
- `storage/CLAUDE.md` — atomic write patterns, storage managers

### Governance Documents
- `docs/CLAUDE_MASTER_DEV_GUIDE.md` — 16-section master reference
- `docs/governance/GUARDRAILS.md` — 12-section, 55 rules, full edge case registry

### Technical Debt Catalogued
- 5 files marked for removal (legacy/backup/stubs)
- Data path discrepancy documented (`data/NSE Data/` → `data/NSE/`)
- 8 known issues catalogued with root causes

---

# Version 1.0

Documentation Foundation Release

Date:

2026-06-03

Status:

Completed

---

## Summary

Established complete project governance and documentation framework.

The project evolved from an informal FII/DII analytics initiative into a formally documented Capital Flow Intelligence Platform.

---

## Deliverables

### Governance Layer

Completed:

PROJECT_SCOPE.md

MASTER_ROADMAP.md

MODULE_REGISTRY.md

MASTER_CHECKLIST.md

DEVELOPMENT_GOVERNANCE.md

RESEARCH_PIPELINE.md

CHANGELOG.md

---

### Architecture Layer

Completed:

MASTER_ARCHITECTURE.md

DATA_ARCHITECTURE.md

AI_ARCHITECTURE.md

GUI_ARCHITECTURE.md

BROKER_ARCHITECTURE.md

---

### Module Documentation

Completed:

INSTITUTIONAL_INTELLIGENCE.md

SECTOR_INTELLIGENCE.md

THEME_INTELLIGENCE.md

STOCK_INTELLIGENCE.md

FUNDAMENTAL_INTELLIGENCE.md

AI_PLATFORM.md

GUI_PLATFORM.md

EXECUTION_PLATFORM.md

---

### Architecture Decision Records

Completed:

ADR-001 Raw Data Never Modified

ADR-002 NSE Data Structure

ADR-003 On Demand Cache

ADR-004 Listing Date Aware Processing

ADR-005 Nselib First Policy

ADR-006 Gross Flow Preservation

ADR-007 Sector Theme Stock Capital Flow Model

ADR-008 Cache Maintenance Strategy

ADR-009 Intelligence Layer Separation

ADR-010 AI First User Experience

ADR-011 Infographic First Visualization

ADR-012 Research Before Development

ADR-013 Broker Independence Architecture

ADR-014 Module Driven Development

ADR-015 Documentation Mandatory Before Release

---

# Strategic Architecture Update

Date:

2026-06-03

Status:

Completed

---

## Change

Project positioning updated from:

```text
FII/DII Intelligence Platform
```

to:

```text
Capital Flow Intelligence Platform
```

---

## Reason

The platform is no longer focused solely on institutional activity.

The platform now tracks market participation across:

FII

DII

PRO

CLIENT

and analyzes how capital moves through the broader market ecosystem.

---

## New Strategic Framework

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
    ↓
Fundamental Validation
    ↓
Portfolio
    ↓
Execution
```

This framework now serves as the primary architectural model for all future development.

---

# Participant Intelligence Initiative

Date:

2026-06-03

Status:

Approved

---

## Objective

Expand Institutional Intelligence into Participant Intelligence.

---

## Participants

FII

DII

PRO

CLIENT

---

## Planned Outputs

Participation Scores

Conviction Scores

Divergence Scores

Smart Money Scores

Retail Sentiment Scores

Participant Reports

Participant Dashboards

Participant Infographics

---

## Planned Engines

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

## Planned AI Capability

AI Participant Analyst

---

# Institutional Intelligence Milestone

Date:

2026-06-01

Status:

Completed

---

## Achievement

Institutional historical dataset integrity reached:

100%

---

## Results

Coverage:

100%

Integrity:

100%

Missing Dates:

0

---

## Deliverables

Historical Engine

Backfill Engine

Integrity Engine

Regime Engine

Trend Engine Foundation

---

# Data Architecture Milestone

Date:

2026-06-02

Status:

Completed

---

## Achievement

Long-term data architecture finalized.

---

## Decisions

Year-wise Bhavcopy Storage

On-Demand Cache Generation

Listing Date Aware Processing

Raw Data Preservation

Cache Maintenance Strategy

---

## Final Structure

```text
data/

NSE Data/

    bhavcopy/

        equity/

            <YEAR>/

                bhavcopy_YYYYMMDD.csv

        f&o/

            <YEAR>/

                fo_YYYYMMDD.csv

    equity_master/

    corporate_actions/

    shareholding/

    results/

    announcements/

cache/

    stock_history/
```

---

# Research Governance Milestone

Date:

2026-06-03

Status:

Completed

---

## Achievement

Research-first development process adopted.

---

## Framework

```text
Idea
    ↓
Research
    ↓
Validation
    ↓
Architecture
    ↓
Development
    ↓
Testing
    ↓
Documentation
    ↓
Release
```

---

## Result

All future major development initiatives must follow the research pipeline.

---

# User Experience Milestone

Date:

2026-06-03

Status:

Completed

---

## Achievement

AI-first and infographic-first platform philosophy adopted.

---

## Principles

AI First User Experience

Infographic First Visualization

Three Second Understanding Rule

Progressive Disclosure

Broker Independence

Human Approval Required

---

# Current Development State

Date:

2026-06-03

---

## Completed

Governance Framework

Architecture Framework

Documentation Framework

Institutional Intelligence Foundation

Data Architecture

Research Framework

---

## Active Development

Sector Intelligence Expansion

Theme Intelligence Expansion

Participant Intelligence Planning

---

## Planned

Stock Intelligence

Fundamental Intelligence

AI Platform Expansion

GUI Platform

Execution Platform

Research Platform

Commercial Platform

---

# Next Milestone

Version 1.1

Participant Intelligence Foundation

---

## Planned Deliverables

ADR-016 Participant Intelligence Framework

PARTICIPANT_INTELLIGENCE.md

Participant Flow Engine

Participant Conviction Engine

Participant Divergence Engine

Smart Money Engine

Retail Sentiment Engine

---

## Expected Outcome

Transition from:

Institutional Intelligence

to

Participant Intelligence

as the primary capital flow analysis layer.

---

# Long-Term Vision

Build the world's most comprehensive Capital Flow Intelligence Platform capable of:

Tracking Participant Behavior

↓

Detecting Capital Flow

↓

Identifying Opportunities

↓

Explaining Opportunities

↓

Managing Portfolios

↓

Executing Trades

↓

Monitoring Outcomes

through a unified AI-powered investment operating system.

---

# Current Project Status

Overall Estimated Completion:

25%

---

## Strategic Focus

Current Priority:

```text
Participant
    ↓
Sector
    ↓
Theme
    ↓
Stock
```

capital flow discovery and opportunity identification.

This remains the central objective of the platform.

## Version 1.3

### Architecture

- Added ADR-018 Market Data Reliability Framework

### Key Decisions

- Runtime data integrity validation
- Self-healing data architecture
- Automated incremental backup strategy
- Weekly recovery point framework
- Secondary backup repository requirement
- Disaster recovery hierarchy
- Metadata-only registry architecture
