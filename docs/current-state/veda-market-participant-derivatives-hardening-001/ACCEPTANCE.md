# Acceptance register

| Gate | Result | Evidence |
|---|---|---|
| Existing participant engines reused | PASS | Implementation inventory |
| NSE source semantics inspected | PASS | Source semantics and live schema sample |
| Participant taxonomy explicit | PASS | FII, DII, PRO, CLIENT |
| Futures aggregate level explicit | PASS | Contract and formula |
| Position change separated from level | PASS | Contract and focused tests |
| Persistence/acceleration/reversal bounded | PASS | Contract and focused tests |
| Like-for-like participant divergence | PASS | Same aggregate-futures OI-change basis |
| F&O/cash date alignment explicit | PASS | Date-alignment section and tests |
| Options boundary conservative | PASS_WITH_CONDITION | Source available but not persisted/contracted |
| Cash-versus-derivatives boundary | PASS_WITH_CONDITION | Units remain non-comparable |
| Minor contract compatibility | PASS | `institutional-flow-1.1`, legacy endpoint preserved |
| VEDA ownership boundary | PASS | Adapter preserves provider-owned output |
| No ML/PRED/EMP/RAG/Jyotish/BEBOS change | PASS | Scope audit |
| Focused FII tests | PASS | 5 passed; institutional edge/guardrail regression 37 passed |
| Full FII regression | PASS | 1308 passed, 1 warning, 911.45s |
| VEDA platform regression/static checks | PASS | Platform suite passed; Ruff, format, mypy and compileall passed |
| Live FII/ VEDA validation | PASS | FII HTTP 200 and VEDA SUCCEEDED; nested 1.1 contract preserved |
| Deterministic output | PASS | Two canonical SHA-256 hashes matched |
| Local performance | PASS_WITH_CONDITION | FII avg/p50/p95 499.11/496.57/561.56ms; VEDA 559.46/536.12/669.62ms |

Final decision: `VEDA_MARKET_PARTICIPANT_DERIVATIVES_HARDENING_OPERATIONAL_WITH_CONDITIONS`.
Conditions are provider freshness/coverage, deliberate options non-support,
non-comparable cash units, local-only performance measurements, and unrelated
pre-existing generated/data changes remaining unstaged.
