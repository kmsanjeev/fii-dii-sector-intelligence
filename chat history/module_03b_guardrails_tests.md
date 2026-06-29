# Chat History — Phase 3B: Guardrails + Test Suite

> **Append-only. Add new entries at the bottom. Never overwrite.**
> Covers: engines/common/guardrails.py, pytest infrastructure, all 16 test files

---

## Session: 2026-06-29 — Phase 3B Implementation

### Context
Previous session had written guardrail infrastructure stubs; this session implemented the full guardrail library and all 16 test files.

### What Was Built

**Guardrail Utility Library:**
- `engines/common/guardrails.py` — 55 functions covering all 12 guardrail sections (G-D through G-PERF)
- All functions log at DEBUG level to `tests/logs/pytest_debug.log` in tests, `logs/guardrails.log` in production

**Test Infrastructure:**
- `pytest.ini` — DEBUG logging to `tests/logs/pytest_debug.log`
- `tests/conftest.py` — 10 shared fixtures + autouse `log_test_boundaries`
- `requirements.txt` — added `pytest>=8.0.0`, `pytest-mock>=3.0.0`

**Guardrail Tests (tests/guardrails/ — 12 files, ~350 test cases):**
| File | Covers |
|------|--------|
| `test_g_d_data_integrity.py` | G-D-01 raw immutability, G-D-02 atomic write, G-D-03 empty df check |
| `test_g_a_api_acquisition.py` | G-A-01 rate limit, G-A-02 exponential backoff, G-A-03 recovery queue |
| `test_g_s_symbol_universe.py` | G-S-01 EQ series filter, G-S-02 listing date, G-S-04 universe size |
| `test_g_p_price_data.py` | G-P-01 negative prices, G-P-02 OHLC consistency, G-P-03 zero volume |
| `test_g_c_classification.py` | G-C-01 null sectors, G-C-02 manual override always last |
| `test_g_ca_corporate_actions.py` | G-CA-01 split ratio, G-CA-02 extraordinary dividends |
| `test_g_i_intelligence_scoring.py` | G-I-01 min 5 sessions, G-I-02 80% coverage, G-I-03 score range |
| `test_g_f_financial_results.py` | G-F-01 India FY quarters (Q1=Apr–Jun, Q4=Jan–Mar) |
| `test_g_tc_trading_calendar.py` | G-TC-01 weekends, G-TC-02 NSE holidays, F&O expiry last Thursday |
| `test_g_id_institutional_data.py` | G-ID-01 T+1 lag, G-ID-02 pre-2016 OI gap, gross flows |
| `test_g_sys_system.py` | G-SYS-01 env var guard, G-SYS-02 credential scanning |
| `test_g_perf_performance.py` | G-PERF-01 chunk_symbol_list, G-PERF-03 market hours batch guard |

**Edge Case Tests (tests/edge_cases/ — 4 files, ~50 test cases):**
| File | Covers |
|------|--------|
| `test_ec_symbol_edge_cases.py` | HDFC-HDFCBANK merger, SME IPO SM series excluded, delistings |
| `test_ec_price_edge_cases.py` | Circuit breakers, bonus/split drops, Mahurat trading |
| `test_ec_classification_edge_cases.py` | ADANIPORTS→AEROSPACE bug (documented), ITC conglomerate, COALINDIA |
| `test_ec_institutional_edge_cases.py` | Pre-2016 OI blocked, Budget Day 2024/2025, COVID crash flows |

### Key Test Patterns (for reference)

```python
# ADANIPORTS classification override (G-C-02)
# Engine classifies ADANIPORTS as AEROSPACE (wrong — no Industry Master)
# Manual override must correct to LOGISTICS
result = apply_manual_overrides(df, override_file)
assert result.iloc[0]["sector_platform"] == "LOGISTICS"

# India FY quarter mapping (G-F-01)
@pytest.mark.parametrize("month,expected", [(4,"Q1"),(6,"Q1"),(1,"Q4"),(3,"Q4")])
def test_india_fy_quarter(month, expected):
    assert get_india_quarter(month) == expected

# Exponential backoff (G-A-02)
assert delays[0] == 1.0  # first retry
assert delays[1] == 2.0  # doubles each retry
```

### Supporting Files
- `tests/CLAUDE.md` — test rules: never import engines directly, never write to data/, always use tmp_dir fixture

### Known Issue Documented (NOT Fixed — needs Phase 4B)
ADANIPORTS → AEROSPACE misclassification. Test `test_override_beats_engine_classification` documents expected behavior. Fix unblocks after Industry Master Engine (Phase 4B).

### Next Actions for This Module
1. Run `pytest` to verify all tests pass
2. Add tests for Phase 4A outputs once Company Fundamentals Master Engine is built (new test file: `tests/fundamentals/`)

---
