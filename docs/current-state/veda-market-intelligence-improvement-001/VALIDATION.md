# Validation

## Completed

- Deterministic freshness contract tests: 5 passed, including delayed data, future-dated
  non-scheduled data, scheduled future events, optional unavailable sources and
  missing numeric values.
- Existing FII API/guardrail focused suite: 19 passed before the change.
- FII full suite: 1,303 passed in 975.99s with one existing warning.
- VEDA Market/public/legacy focused suite after the contract change: 40 passed.
- VEDA full platform suite: 70 passed with existing Authlib/Starlette warnings.
- VEDA changed-provider Ruff check: passed.
- VEDA Ruff, format, mypy and compileall: passed.
- FII changed-surface import/compile and new-test format validation: passed.
- No RAG rebuild: governed semantic content was unchanged.

## Conditions

The FII repository contains pre-existing generated/data changes and legacy
lint findings outside the bounded improvement. Those files were not staged.
Live FII endpoint validation passed for health, Market, participant, sector,
stock and corporate routes. Direct VEDA adapter calls against that service
also passed. A standalone VEDA Core process did not bind port 8010 in the
shell invocation used for this check; this remains a runtime-start condition,
not a claimed Core HTTP pass. Ten-sample endpoint latency was measured with
Market context p50 12.9 ms, participant 7.6 ms, sectors 23.7 ms, stock
231.1 ms and corporate 26.0 ms.
