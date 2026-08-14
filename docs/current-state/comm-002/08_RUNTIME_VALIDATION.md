# Runtime Validation

COMM-002 uses the existing `/api/chat` path and ChatEngine. Runtime probes cover small talk, heart-to-heart, straight talk, expert and beginner Jyotisha, Hinglish, English/Hindi idioms, sarcasm, health/finance high-stakes prompts, and ambiguity. The response adaptation profile is observable through the existing ChatEngine diagnostic state in tests; it is not exposed to normal users.

No empirical cases are inserted. PRED-M3_OPERATIONAL_PLUS remains unchanged. The general Jyotisha RAG corpus is not modified or rebuilt.

The supported `powershell.exe -ExecutionPolicy Bypass -File .\start.ps1`
launcher reported the backend and frontend already listening. Direct probes
returned HTTP 200 for `http://localhost:8001/openapi.json` and
`http://localhost:5173`. Twelve deterministic `/api/chat` probes through the
existing router returned HTTP 200 using the repository's test provider boundary;
no real empirical data was created.
