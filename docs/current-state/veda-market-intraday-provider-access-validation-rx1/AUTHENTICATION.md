# Authentication

Dhan provider-local authentication now supports:

- secure local enrollment via `py -3.11 scripts/provider_auth.py enroll dhan`;
- RFC6238 TOTP through `pyotp`;
- access-token generation through the documented Dhan endpoint;
- expiry-aware secure token reuse and refresh;
- explicit `SECURE_CREDENTIAL_ENROLLMENT_REQUIRED` failure;
- no token, PIN, TOTP seed or API secret in VEDA Core, frontend output, logs or
  Git.

Windows uses the `keyring` Windows Vault backend. The local validation run
confirmed the backend and cached the token securely. RenewToken is not used as
the primary lifecycle.

The existing Dhan SDK construction was corrected to use `DhanContext`, which
is required by installed `dhanhq==2.2.0`.
