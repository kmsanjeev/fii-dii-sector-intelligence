# Refusal, Access and Telemetry

Chat responses now expose `access` and `telemetry` metadata. Events are
distinct: `NORMAL_ANSWER`, `CONFIG_ACCESS_DENIED`, `SAFETY_REFUSAL`,
`SOURCE_QUALIFIED`, `PROVIDER_UNAVAILABLE`, `PROMPT_LEAK_BLOCKED`, and policy
diagnostic errors. Output refusal classification remains intact; a refusal is
not treated as a configuration denial, and a source limitation is not treated
as a safety refusal.
