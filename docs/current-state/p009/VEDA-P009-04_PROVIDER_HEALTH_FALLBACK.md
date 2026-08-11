# Provider Health And Fallback

Provider runtime state now supports:
- `HEALTHY`
- `DEGRADED`
- `COOLDOWN`
- `DISABLED`
- `UNAVAILABLE`
- `ERROR`

Fallback behaviour:
- the run attempts the configured primary search provider;
- auth failures place that provider into cooldown;
- temporary failures degrade the provider and allow fallback providers to run;
- if all configured search providers fail, the run fails conservatively.

This phase does not auto-promote any provider result into Approved Core Knowledge.
