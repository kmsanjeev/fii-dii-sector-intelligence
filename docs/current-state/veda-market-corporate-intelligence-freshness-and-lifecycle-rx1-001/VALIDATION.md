# Validation record

## Focused validation

`py -3.11 -m pytest -q tests/test_corporate_freshness_lifecycle_rx1.py tests/test_corporate_intelligence.py tests/test_cross_layer_intelligence.py tests/test_market_freshness_contract.py`

Result: **16 passed in 3.48s**.

`ruff check` passed for the RX1 implementation and test files. The existing
`data_loader.py` has five baseline lint findings (broad exception handling and
silent exception paths); the findings predate RX1 and were not expanded by this
change. Targeted `compileall` passed for all changed Python modules.

## Controlled source validation

`py -3.11 -m engines.corporate.corporate_event_calendar_engine` completed with
three official NSE windows, 330 source rows, 297 net new rows after merge,
35,745 final rows and no source errors. The generated refresh state was
`SUCCESS`.

## Runtime contract validation

An audited `RELIANCE` Corporate response retained contract version
`corporate-intelligence-1.0`, exposed 11 bounded events, separated fundamental
freshness from result-event linkage, reported partial filing-date coverage and
reported partial event-calendar retrieval coverage. No quantitative metrics
were inlined into Corporate.

## Adapter and full-suite status

FII-DII full suite: **1345 passed, 1 warning in 595.07s**. The warning is the
existing Starlette/httpx deprecation warning.

VEDA focused market-provider suite: **25 passed**. VEDA platform suite:
**1298 passed**, with existing Authlib and Starlette/httpx deprecation warnings.

Live HTTP validation on an isolated local port returned `200` for `/health`
and `/api/corporate/summary?symbol=RELIANCE&days=30&limit=10`; the response
retained `corporate-intelligence-1.0`, separate retrieval/lifecycle metadata,
and event-level build provenance.

Warm direct contract timing (12 samples, Windows/Python 3.11): global Corporate
average **662.57 ms**, p50 **612.47 ms**, p90 **718.17 ms**; symbol Corporate
average **307.57 ms**, p50 **70.52 ms**, p90 **77.40 ms**. The symbol maximum
was an isolated first-load/cache outlier; all requests remained bounded.
