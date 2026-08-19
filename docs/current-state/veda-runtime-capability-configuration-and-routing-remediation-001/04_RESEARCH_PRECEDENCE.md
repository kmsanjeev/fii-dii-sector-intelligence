# Research Precedence and Subject Context

Explicit research language is detected before domain scoring. A research request retains a `subject_intent` such as `ASTRO`, `MUHURTA`, `MARKET`, `STOCK` or `GENERAL`.

This prevents “research latest evidence on D20” from becoming ordinary Jyotish and prevents “research latest NIFTY market sources” from losing market context. The research capability remains the primary access decision; the subject capability is checked separately. Research mode cannot bypass a disabled or unavailable specialist capability.

Research tool execution is bounded to the subject domain. Provider availability and MCP fallback remain runtime-qualified and no provider configuration is introduced.
