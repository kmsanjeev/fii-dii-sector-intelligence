# Runtime Validation

Focused LANG-001-R1, LANG-001, COMM-001, STD-003, and chat-router suites pass.
The deterministic resolver adds zero provider calls. Existing `/api/chat`
probes remain HTTP 200 and ChatEngine remains the response owner. RAG is
unchanged and language data remains outside general Jyotisha retrieval.

Performance remained local and deterministic; the final focused measurement is
1.17 ms average, 0.80 ms p50, and 2.49 ms p95, all below the 5 ms target. The
runtime probe returned HTTP 200 for five representative inputs and added zero
provider calls. Full Python collected 692 tests and retains the known external
research timeout condition at 300 seconds; it is not represented as a full
pass.
