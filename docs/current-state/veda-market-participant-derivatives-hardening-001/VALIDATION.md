# Validation

Focused FII contract tests: `5 passed`.

Focused VEDA provider tests: `21 passed` (including preservation of the
additive derivatives contract without recalculation).

Full FII repository suite: `1308 passed, 1 warning` in `911.45s`. The warning
is the existing Starlette/httpx deprecation warning.

Separate VEDA platform suite: all collected tests passed; Ruff, format, mypy
and compileall passed (`40` source files for mypy).

The installed nselib source functions were inspected directly and one current
sample was fetched for schema confirmation. No raw provider output was stored
or committed.

Required boundaries are covered by tests for level versus change, missing
windows, persistence, acceleration, reversal, same-basis participant
divergence, explicit date alignment, options non-support and VEDA pass-through.

Live FII endpoint and formal VEDA capability both returned success. Ten-sample
local latency: FII direct average `499.11ms`, p50 `496.57ms`, p95/max
`561.56ms`; VEDA average `559.46ms`, p50 `536.12ms`, p95/max `669.62ms`.
Two canonical endpoint payload hashes matched:
`6a65a68be8a015cb353566ba4f165d753e7b9400ccd49cc98ace92df271f0dfe`
(SHA-256).

Full-suite, live HTTP, performance and Git results are also recorded in the
final acceptance record after selective staging.
