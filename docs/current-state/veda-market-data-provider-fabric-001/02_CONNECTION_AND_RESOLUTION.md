# Connection and resolution contract

`ProviderConnection` contains a connection ID, provider ID, scope, sanitized
credential reference, auth/entitlement/health state, authorized capability
set and bounded failure metadata. Raw tokens, API secrets, TOTP seeds and
passwords are prohibited.

`Resolution` returns the requested capability, selected provider/type,
authority, connection ID, reason, fallback state, freshness expectation,
limitations and alternatives. No network request is performed by the fabric.

Examples:

- no broker + `EOD_EQUITY_HISTORY` -> `local-governed`;
- no connected live provider + `LIVE_QUOTE` ->
  `AUTHORIZED_LIVE_PROVIDER_REQUIRED`;
- connected/entitled/healthy Dhan + `INTRADAY_HISTORY` -> Dhan;
- unconnected Zerodha/HDFC -> not selected;
- research candidates -> not selected by default.

The existing `get_adapter()` remains a compatibility wrapper for Dhan and CSV
portfolio flows. A future provider-specific adapter may be added without
changing this resolver contract.
