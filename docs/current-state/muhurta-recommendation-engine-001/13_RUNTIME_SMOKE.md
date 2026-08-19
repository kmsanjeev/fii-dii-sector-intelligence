# Runtime Smoke

The conformance gate was invoked against the accepted contracts.

| Probe | Expected | Result |
|---|---|---|
| Business valid facts | Fail closed | `MUHURTA_ACTIVITY_CONTRACT_IMPLEMENTATION_BLOCKED` |
| Education valid facts | Fail closed | `MUHURTA_ACTIVITY_CONTRACT_IMPLEMENTATION_BLOCKED` |
| Unsupported marriage | Abstain | `UNSUPPORTED_ACTIVITY` |
| Religious ceremony | Do not activate | `SOURCE_HARDENING_REQUIRED` |
| Missing machine binding | Block | `NO_MACHINE_EVALUATOR_BINDINGS_IN_ACCEPTED_CONTRACTS` |
| Hash mismatch | Fail closed | Loader raises validation error |

No recommendation, candidate window, score, ranking, or public API result was
created. P032 calculation facts remain available only through the existing
foundation layer.
