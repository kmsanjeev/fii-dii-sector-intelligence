# tests/ — Directory Context for Claude

## Purpose
Pytest-based test suite for all guardrail utility functions and domain edge cases.
Every test logs at DEBUG level to `tests/logs/pytest_debug.log` via `pytest.ini`.

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures (project_root, nse_holidays, sample DataFrames)
├── logs/                    # Test log output (git-ignored)
│   ├── pytest_debug.log     # Full DEBUG log from every pytest run
│   └── test_session.log     # Session-level fixture boundaries
├── guardrails/              # One file per guardrail section
│   ├── test_g_d_data_integrity.py      # G-D-01 to G-D-07 (7 rules)
│   ├── test_g_a_api_acquisition.py     # G-A-01 to G-A-06 (6 rules)
│   ├── test_g_s_symbol_universe.py     # G-S-01 to G-S-06 (6 rules)
│   ├── test_g_p_price_data.py          # G-P-01 to G-P-06 (6 rules)
│   ├── test_g_c_classification.py      # G-C-01 to G-C-05 (5 rules)
│   ├── test_g_ca_corporate_actions.py  # G-CA-01 to G-CA-04 (4 rules)
│   ├── test_g_i_intelligence_scoring.py # G-I-01 to G-I-05 (5 rules)
│   ├── test_g_f_financial_results.py   # G-F-01 to G-F-04 (4 rules)
│   ├── test_g_tc_trading_calendar.py   # G-TC-01 to G-TC-07 (7 rules)
│   ├── test_g_id_institutional_data.py # G-ID-01 to G-ID-05 (5 rules)
│   ├── test_g_sys_system.py            # G-SYS-01 to G-SYS-05 (5 rules)
│   └── test_g_perf_performance.py      # G-PERF-01 to G-PERF-04 (4 rules)
└── edge_cases/              # Domain-specific edge cases beyond standard guardrails
    ├── test_ec_symbol_edge_cases.py         # Mergers, delistings, IPOs, conglomerates
    ├── test_ec_price_edge_cases.py          # Circuit breakers, CA price drops, Mahurat
    ├── test_ec_classification_edge_cases.py # PSUs, holding cos, known bugs (ADANIPORTS)
    └── test_ec_institutional_edge_cases.py  # T+1 lag, pre-2016 OI gap, Budget Day, F&O expiry
```

## Running Tests

```bash
# Run all tests with debug logging
pytest

# Run only guardrail tests
pytest tests/guardrails/

# Run only edge case tests
pytest tests/edge_cases/

# Run specific section
pytest tests/guardrails/test_g_d_data_integrity.py -v

# View debug log after run
cat tests/logs/pytest_debug.log
```

## pytest.ini Configuration
- `testpaths = tests`
- `log_file = tests/logs/pytest_debug.log` (DEBUG level)
- `addopts = -v --tb=short`
- Session log also at `tests/logs/test_session.log` (via conftest fixture)

## Fixtures (conftest.py)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `test_logger` | session | Writes to `tests/logs/test_session.log` |
| `project_root` | session | `Path` to repo root |
| `nse_holidays` | session | 13 NSE holidays for 2024 |
| `tmp_dir` | function | Temp dir per test (cleaned after each test) |
| `sample_bhavcopy_df` | function | 5-row OHLCV DataFrame (TCS, INFY, etc.) |
| `sample_equity_master` | function | 5-row master (includes ADANIPORTS with null sector/confidence=0.40) |
| `sample_institutional_df` | function | FII/DII BUY+SELL+NET rows |
| `sample_results_df` | function | Financial results with India FY quarters |
| `mock_env_vars` | function | Sets TEST_TELEGRAM_TOKEN + TEST_GOOGLE_CREDS |
| `missing_env` | function | Clears env vars to test missing-var guards |
| `log_test_boundaries` | function (autouse) | Logs TEST START/END for every test |

## Adding New Tests

1. Place guardrail tests in `tests/guardrails/test_g_<section>.py`
2. Place edge case tests in `tests/edge_cases/test_ec_<topic>.py`
3. Every test must call `logger.debug(...)` with `[<rule-code>]` prefix
4. Tests must import from `engines.common.guardrails` only (no engine imports)
5. Use fixtures from `conftest.py` — do NOT create test-local fixtures that duplicate them

## Rules
- Never import engines directly in tests — only guardrails.py utilities
- Never use real API calls in tests — mock at the guardrail boundary
- Never write to `data/` directories from tests — use `tmp_dir` fixture
- Test names must follow: `test_<happy_path|guard|edge>_<description>`
- Reference guardrail rule code in every test docstring: `"""GUARD: G-D-01 — ..."""`
