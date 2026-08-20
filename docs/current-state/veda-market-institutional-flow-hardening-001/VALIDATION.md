# Validation record

- Focused institutional, freshness, edge-case and guardrail tests: **40 passed**.
- API contract baseline and institutional tests after the additive endpoint:
  **43 passed**.
- Full FII suite: **1,306 passed, 1 warning in 932.90 seconds**. The first
  full run detected the expected stale API-contract fixture; the fixture and
  endpoint count were updated, then the complete suite passed.
- Python compilation of changed modules: **passed**.
- Independent real-file rebuild: **passed** over 2,618 F&O rows and 647 cash rows.
- Independent deterministic contract rebuild: **stable**, canonical SHA-256
  `360f1178d3dc5307bf75187fc4ad0f1ccfd5242ae97920a5f7944de80a572291` on
  both runs.
- Audited source dates: F&O `2026-08-19`; cash `2026-08-18`.
- Audited evidence quality: `LIMITED`, because cash windows are partial on
  the latest F&O date.

The existing VEDA adapter requires only legacy institutional fields `date` and
`Market_Regime`, validates provider `data_status`, and returns remaining
provider fields. No VEDA code change is required for this additive contract.

## VEDA and live validation

- VEDA platform suite: **72 passed**.
- Ruff check: **passed**.
- Ruff format check: **passed**.
- Mypy: **passed**, 40 source files.
- VEDA compileall: **passed**.
- FII `/health`, `/api/participant/latest`, `/api/participant/institutional`
  and `/api/market/context`: HTTP 200.
- VEDA `market.institutional-flow`: `SUCCEEDED`, provider
  `veda-market-intelligence`, contract `institutional-flow-1.0`.
- Local FII institutional endpoint benchmark: average **566.40 ms**, p50
  **635.08 ms**, p95 **799.22 ms**, max **799.22 ms** over 10 calls.
- VEDA institutional query benchmark: average **513.17 ms**, p50 **503.15
  ms**, max **547.35 ms** over 5 calls.

The only recorded test warnings are the existing FastAPI/Starlette httpx
deprecation warning. No provider calls were added to the contract itself.
