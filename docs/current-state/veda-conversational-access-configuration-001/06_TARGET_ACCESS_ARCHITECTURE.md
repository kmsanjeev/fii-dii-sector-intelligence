# Target Access Architecture

The runtime now separates four facts:

1. `CAPABILITY_MATURITY` — read-only governed maturity.
2. `ADMIN_ACCESS_STATE` — `ENABLED`, `DISABLED`, or `ADMIN_ONLY`.
3. `RUNTIME_AVAILABLE` — current config/provider/runtime availability.
4. `EFFECTIVE_ACCESS` and `EFFECTIVE_ANSWER_MODE` — the decision for this turn.

`GENERAL_CHAT` is always available and cannot be disabled. A disabled
specialist capability returns a clear configuration message and records
`CONFIG_ACCESS_DENIED`; it does not claim the capability is unsupported.
Safety and privacy safeguards remain outside this policy and cannot be toggled.
