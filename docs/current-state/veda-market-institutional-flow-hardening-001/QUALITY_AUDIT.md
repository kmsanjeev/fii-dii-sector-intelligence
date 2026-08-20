# Quality and integrity audit

1. F&O history has complete date uniqueness for the observed 2,618 rows.
2. Cash history is a separate, shorter source and is one trading day behind
   F&O in the audited snapshot.
3. Cash nulls remain explicit and surface as `PARTIAL` or `UNAVAILABLE`
   windows rather than zero-flow observations.
4. Existing freshness metadata remains provider-local and is included in the
   additive institutional contract.
5. The older trend and one-row positioning outputs are not authoritative for
   the new contract because their as-of dates lag participant history.

Integrity rules: parse and order dates; preserve missing values; expose
observation count, expected count, coverage and state for every window; keep
F&O and cash units separate; do not infer unsupported options or cross-
instrument normalization.
