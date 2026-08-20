# Validation

Pre-change direct endpoint benchmark (five-symbol warm-up plus ten repeated RELIANCE samples): min `125.5 ms`, p50 `181.5 ms`, p90 `207.7 ms`, max `228.5 ms`.

Post-change direct benchmark (ten warm RELIANCE samples): min `194.6 ms`, p50 `256.3 ms`, p90 `347.2 ms`, max `354.1 ms`.

Post-change VEDA-adapter benchmark (ten warm RELIANCE samples): min `195.3 ms`, p50 `218.7 ms`, p90 `320.8 ms`, max `328.3 ms`. The observed VEDA p50 difference was `-37.6 ms` in separate runs; this is measurement noise/endpoint-path variance, not a claimed performance improvement. The contract adds bounded deterministic work to the already-large legacy endpoint, so no hard latency regression target is asserted by this phase.

Validation results:

- FII focused stock/sector/institutional/freshness/API tests: `18 passed`.
- FII full suite: `1316 passed, 1 warning` in `913.25 s` (`15:13`).
- VEDA focused provider/public foundation tests: `34 passed`.
- VEDA full suite from the correct `platform` test root: exited `0`, warnings only.
- New FII and VEDA files: Ruff clean; FII compileall clean; scoped `git diff --check` clean.
- Direct runtime probes passed for RELIANCE, LT and 20MICRONS. VEDA adapter propagation passed with `stock-intelligence-1.1` and the formal allowlist excluded legacy recommendation/LLM/prediction fields.

The first VEDA full-suite attempt from the repository root produced `ModuleNotFoundError: app`; it was a test invocation-root error, not a product failure. The suite was rerun from `D:\Projects\VEDA\platform` and passed.

No semantic RAG rebuild was expected or performed. Existing generated/data/RAG working-tree modifications were pre-existing or runtime-generated and were not staged.
