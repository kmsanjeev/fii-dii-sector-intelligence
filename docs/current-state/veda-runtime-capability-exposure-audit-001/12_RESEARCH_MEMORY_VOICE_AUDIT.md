# Research, memory and voice

Research has a Chat intent, research service, API/admin platform and Research
UI. DDGS is available in the current environment; MCP is not available. A
research request that contains only `research` routes correctly, but explicit
research phrases combined with Jyotish terms can tie with ASTRO and lose the
research route. This should be corrected by explicit research precedence in a
future remediation.

Attachments and reviewed-memory workflows have API, UI and environment gates.
Their central access-policy records are not consulted by the endpoint/runtime
checks. MIT repository intake has the same mismatch. Voice requests use the
same ChatEngine intent and safety flow, but the VOICE access-policy state is not
enforced by the voice surface. These are configuration-binding gaps; no memory
was mutated and no provider was contacted by this audit.
