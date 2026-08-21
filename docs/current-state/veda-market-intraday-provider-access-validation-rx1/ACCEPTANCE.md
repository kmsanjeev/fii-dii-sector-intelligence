# Acceptance

| Gate | Result | Evidence |
|---|---|---|
| A Manifest truth | PASS_WITH_CONDITION | Capability states and inherited overclaims repaired |
| B Authentication | PASS | Dhan TOTP/profile HTTP 200 |
| C Entitlement | BLOCKED | Dhan profile `DataPlan=Deactive`; historical `DH-902` |
| D Real data | BLOCKED | No candles/quotes/options accepted |
| E Live | PASS_WITH_CONDITION | `LIVE_SESSION_VALIDATION_PENDING`; market closed and entitlement inactive |
| F Foundation | PASS_WITH_CONDITION | Existing deterministic foundation remains intact; real sample unavailable |
| G Platform | PASS_WITH_CONDITION | Resolver fail-closed; no-broker local EOD preserved |
| H Engineering | PASS_WITH_CONDITION | Focused, regression, full FII and VEDA platform suites pass; live provider access remains entitlement-blocked |

Foundation state:
`VEDA_MARKET_INTRADAY_DATA_FOUNDATION_OPERATIONAL_WITH_CONDITIONS`.

RX1 state:
`VEDA_MARKET_INTRADAY_PROVIDER_ACCESS_VALIDATION_RX1_OPERATIONAL_WITH_CONDITIONS`.

Next activity: `DHAN_DATA_ENTITLEMENT_REQUIRED` bounded provider-specific
validation. Intraday Intelligence remains not started.
