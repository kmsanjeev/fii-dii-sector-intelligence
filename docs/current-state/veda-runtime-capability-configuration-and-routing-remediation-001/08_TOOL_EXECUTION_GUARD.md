# Tool Execution Guard

Provider-visible tool lists and execution-time authorization now share the same per-turn allowlist. `_call_tool()` rejects a tool absent from the current allowlist before invoking the function, records `OUT_OF_SCOPE_TOOL_CALL`, and returns a deterministic error object.

This protects against provider/tool-parser behavior that attempts to invoke a globally registered function not present in the current domain scope. The registered implementation inventory remains 23/23.
