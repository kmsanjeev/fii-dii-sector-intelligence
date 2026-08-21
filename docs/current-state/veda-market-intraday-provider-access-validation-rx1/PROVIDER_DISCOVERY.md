# Provider discovery

| Provider | Configured connection | Authentication | Entitlement | Runtime health |
|---|---|---|---|---|
| local-governed | Always available for local EOD | Not required | Not required | Available |
| Dhan | Configured from secure local enrollment/environment | Validated | `ENTITLEMENT_REQUIRED` | `ENTITLEMENT_BLOCKED` |
| Zerodha Kite | Not configured | Not validated | Unknown | Unknown |
| HDFC Sky | Not configured | Not validated | Unknown | Unknown |
| CSV import | Capability only; no live connection | Not required | Not required | File-dependent |
| yfinance | Compatibility only | Not applicable | Policy-limited | Not production authority |
| nselib/nsepython | Research candidates | Not applicable | Policy review required | Not selected |

The Provider Fabric, not a provider name, owns selection. Dhan was selected as
the only configured broker candidate, then correctly rejected for live
capabilities by the entitlement/health gates.
