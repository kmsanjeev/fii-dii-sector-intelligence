# Current Request Path

`POST /api/chat` → `detect_intent()` → `_get_or_create_session()` →
`ChatEngine.chat()` → `analyze_conversation()` / `AgentOrchestrator` →
`get_system_prompt()` → retrieval → optional external research → provider
fallback → output safety classifier → `ChatResponse`.

Configuration path:

`AdminPage` → `/api/veda/configuration` →
`engines.ai.capabilities.access_policy` → atomic JSON under ignored
`data/veda/conversation_access.json`.

Capability discovery remains `GET /api/chat/capabilities`; the response now
includes access, runtime, maturity, effective answer mode and protected-safety
metadata. One policy service owns the decision; maturity is not editable.
