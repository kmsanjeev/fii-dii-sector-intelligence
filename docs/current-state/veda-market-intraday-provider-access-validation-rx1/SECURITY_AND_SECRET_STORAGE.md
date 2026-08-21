# Security and secret storage

- PIN, TOTP seed and access token are stored only through Windows Vault via
  `keyring` after local enrollment.
- Runtime output contains only booleans, masked/typed state, expiry metadata
  and provider error codes.
- VEDA receives provider ID, connection/auth/entitlement/health state and
  capabilities only.
- No callback listener, frontend secret field, raw auth URL, provider dump or
  raw credential file was created.
- No order endpoint, order adapter or execution API was called.
