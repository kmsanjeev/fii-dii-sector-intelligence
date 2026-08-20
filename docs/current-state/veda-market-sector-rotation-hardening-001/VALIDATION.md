# Validation record

## Focused and static checks

- Sector/market/institutional/classification focused set: 105 passed in 4.89s.
- `tests/test_sector_rotation_contract.py`: 5 passed in 0.81s.
- direct engine: completed; 27 sectors, price as-of 2026-08-20.
- `py_compile`: passed for engine, router and tests.
- Ruff check: passed.
- Ruff format check: passed after formatting.
- independent invariants: contract version, scope, date alignment, legacy index
  date, no duplicate `date_flow`, breadth bounds and evidence-quality values
  all passed.
- deterministic rebuild: snapshot SHA-256
  `41DA54F7814C34275BF6AC25D381CCB7C5878D4386AAFB21C4EA4D2E3C5CE4DE` and
  history SHA-256
  `3531FED79AA6DCE2112F1614379B9CA5CFBE348BB114097084587FD684BD624D` were
  identical across two consecutive builds.

## Repository regressions

- FII full suite: 1,313 passed, 1 warning, 878.67s (14m38s).
- VEDA full suite: passed, 14.73s.
- VEDA focused market/provider/public/conformance set: 44 passed.
- Existing warnings are dependency deprecations; no sector test failure was
  observed.

## Live HTTP

- FII `/health`: HTTP 200.
- FII `/api/sectors`: HTTP 200, contract `sector-rotation-1.1`, 27 sectors,
  institutional scope `MARKET_LEVEL_CONTEXT_ONLY`.
- VEDA `/api/v1/readiness`: HTTP 200.
- VEDA real `market.sector.intelligence` query: HTTP 200 / `SUCCEEDED`,
  provider `veda-market-intelligence`, contract `sector-rotation-1.1`.

## Warm performance

Ten measured samples after two warm-up requests:

| Surface | Min ms | P50 ms | P90 ms | Max ms | Average ms |
|---|---:|---:|---:|---:|---:|
| FII `/api/sectors` | 29.39 | 72.46 | not recorded | 90.96 | 66.43 |
| VEDA sector query | 93.84 | 115.77 | not recorded | 456.31 | 158.74 |

The engine itself completed in approximately four seconds on the local
current-data set. Provider calls added: zero.
