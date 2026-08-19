# Auxiliary Capability Policy Binding

`require_capability_access()` is the framework-neutral enforcement point. It evaluates administrator state before runtime availability and returns typed `CONFIG_ACCESS_DENIED`, `ADMIN_ONLY` or `CAPABILITY_UNAVAILABLE` errors.

The binding is now effective for:

- Attachments: inline chat context and upload endpoint.
- Reviewed Memory: draft, approve, discard and legacy/unified retrieval.
- MIT Repository Intake: draft, approve and retrieval.
- MCP: research-service fallback and direct provider availability/search.
- Voice: voice chat mode, direct ChatEngine voice calls, TTS and frontend mic/speech controls.

Effective state remains distinct from maturity. The policy does not promote a capability or change its answer mode. The frontend receives the effective capability snapshot and uses it for controls; backend enforcement remains authoritative.
