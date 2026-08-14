# Runtime Validation

LANG-001-specific, COMM-001, STD-003, and chat-router focused suites pass:
35 passed, 1 existing Starlette/httpx deprecation warning. Known-expression
lookup is deterministic and provider-free. Frontend validation passes: 29
tests and production build. Runtime `/api/chat` probes returned HTTP 200 for
English, Hindi, Roman Hindi, Hinglish, abbreviation, and unknown-expression
inputs; no additional provider calls were introduced. Lookup timing measured
1.34 ms average, 0.92 ms p50, and 2.62 ms p95 in the local probe.

The full Python suite collected 688 tests but timed out at 300 seconds in the
known network/research-heavy path after reaching 76%; no LANG-001 failure was
reported before timeout. The existing ChatEngine response owner is unchanged.
