# Session Log — 2026-06-29 | Phase 3B: Guardrails + Test Suite

## Session Summary

This session completed **Phase 3B** of the FII-DII-SECTOR-INTELLIGENCE development roadmap:
implementing the full guardrail utility library and its complete test suite.

---

## What Was Accomplished

### 1. Master Claude Guide Created
- `docs/CLAUDE_MASTER_DEV_GUIDE.md` — 16-section master reference (all architecture, phases, ADRs)

### 2. Skill Files Created (13 CLAUDE.md files)
All directory-level context files so Claude never needs to re-read the master guide:
- Root `CLAUDE.md`, `engines/CLAUDE.md`, `engines/common/CLAUDE.md`
- `engines/fundamentals/CLAUDE.md`, `engines/acquisition/CLAUDE.md`
- `engines/intelligence/CLAUDE.md`, `engines/foundation/CLAUDE.md`
- `data/CLAUDE.md`, `fetchers/CLAUDE.md`, `docs/CLAUDE.md`
- `alerts/CLAUDE.md`, `sheets/CLAUDE.md`, `storage/CLAUDE.md`

### 3. Guardrails Document
- `docs/governance/GUARDRAILS.md` — 55 named rules across 12 sections (G-D through G-PERF)

### 4. Guardrail Utility Library
- `engines/common/guardrails.py` — all 55 guardrail utility functions (~400 lines)
- Every function logs at DEBUG level
- Covers: data integrity, API, symbols, prices, classification, corporate actions,
  intelligence scoring, financial results, trading calendar, institutional data, system, performance

### 5. Test Infrastructure
- `pytest.ini` — DEBUG logging to `tests/logs/pytest_debug.log`
- `tests/conftest.py` — 10 shared fixtures including autouse boundary logger

### 6. Guardrail Test Files (12 files, ~400 test cases)
```
tests/guardrails/
├── test_g_d_data_integrity.py      (G-D-01 to G-D-07)
├── test_g_a_api_acquisition.py     (G-A-01 to G-A-06)
├── test_g_s_symbol_universe.py     (G-S-01 to G-S-06)
├── test_g_p_price_data.py          (G-P-01 to G-P-06)
├── test_g_c_classification.py      (G-C-01 to G-C-05)
├── test_g_ca_corporate_actions.py  (G-CA-01 to G-CA-04)
├── test_g_i_intelligence_scoring.py (G-I-01 to G-I-05)
├── test_g_f_financial_results.py   (G-F-01 to G-F-04)
├── test_g_tc_trading_calendar.py   (G-TC-01 to G-TC-07)
├── test_g_id_institutional_data.py (G-ID-01 to G-ID-05)
├── test_g_sys_system.py            (G-SYS-01 to G-SYS-05)
└── test_g_perf_performance.py      (G-PERF-01 to G-PERF-04)
```

### 7. Edge Case Test Files (4 files)
```
tests/edge_cases/
├── test_ec_symbol_edge_cases.py         (mergers, IPOs, delistings, SME)
├── test_ec_price_edge_cases.py          (circuit breakers, corporate action drops, Mahurat)
├── test_ec_classification_edge_cases.py (ADANIPORTS bug, PSUs, holding cos, conglomerates)
└── test_ec_institutional_edge_cases.py  (T+1 lag, pre-2016 OI, Budget Day, F&O expiry)
```

### 8. Supporting Files
- `tests/CLAUDE.md` — test directory context for future sessions
- `requirements.txt` — added `pytest>=8.0.0` and `pytest-mock>=3.0.0`

---

## Key Technical Decisions

- All guardrail functions use `DEBUG` logging so failures are traceable
- Tests follow pattern: HAPPY PATH → GUARD → EDGE CASE
- India-specific edge cases explicitly tested: IST timezone, India FY quarters (Q1=Apr), 
  NSE holidays, F&O expiry (last Thursday), Budget Day (Feb 1), OI data gap pre-2016
- All tests are isolated using `tmp_dir` fixture — no writes to actual `data/` directory

---

## Critical Path Reminder (for Next Session)

**Phase 4 = CRITICAL BOTTLENECK.**
Do not start any other engine until `engines/fundamentals/company_fundamentals_master_engine.py` is complete.

Next steps in order:
1. Build `company_fundamentals_master_engine.py` (Phase 4 Step 1)
2. Build `industry_master_engine.py` (fixes ADANIPORTS → AEROSPACE bug)
3. Classification V4 completion (reach 95%+ symbol coverage)
4. NSE Constituents auto-downloader (139 indices)

---

## Active ADRs Referenced This Session
- ADR-001: Raw data immutability
- ADR-003: On-demand cache
- ADR-004: Listing-date-aware processing
- ADR-005: nselib-first policy
- ADR-006: Gross flow preservation
- ADR-014: Module-driven development
- ADR-016: Participant intelligence (FII+DII+PRO+CLIENT)
- ADR-020: Corporate intelligence

---

## How to Resume in Next Session
1. Claude auto-loads `CLAUDE.md` files from each directory
2. Memory at `~/.claude/projects/.../memory/` has project context
3. Run `pytest` to verify test suite is green before starting new code
4. Primary task: `engines/fundamentals/company_fundamentals_master_engine.py`
