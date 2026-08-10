# VEDA-P001-01 Security Governance

## Scope

This module addressed the P0 security findings identified during VEDA-P000 without expanding astrology capability or changing the existing kundli logic.

## Secret Inventory

| SECRET_ID | LOCATION | TYPE | TRACKED_BY_GIT | RUNTIME_REQUIRED | EXPOSURE_RISK | ROTATION_REQUIRED | TARGET_STORAGE | ACTION |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `env_runtime` | `.env` | local environment file | No | Yes | High if copied/shared | Case-by-case | OS environment / ignored `.env` | Keep untracked |
| `admin_bootstrap_email` | `ADMIN_EMAIL` env var | bootstrap credential | No | Optional local, required for empty production auth store | High | If previously shared | environment | Require explicit provisioning |
| `admin_bootstrap_password` | `ADMIN_PASSWORD` env var | bootstrap credential | No | Optional local, required for empty production auth store | Critical | Yes if historical fallback was ever used | environment | Enforce password policy |
| `auth_config_state` | `data/auth/auth_config.json` | auth state/config | No | Yes | Medium | No | ignored local file | Keep local-only |
| `auth_user_store` | `data/auth/users.db` | auth user/session store | No | Yes | High | If copied/shared | ignored local file | Keep local-only |
| `broker_runtime_secret` | `VEDA_BROKER_CREDENTIAL_SECRET` env var | broker encryption secret | No | Optional | High | Yes if exposed | environment | Preferred for stable encryption |
| `broker_local_key` | `data/auth/broker_credentials.key` | local broker encryption key | No | Fallback local | Medium | Recreate if workstation trust changes | ignored local file | Keep local-only |
| `broker_credential_blob` | `data/portfolio/broker_auth.json` | encrypted broker credential payload | No | Optional | High if key also exposed | Re-authorize if legacy plaintext existed | ignored local file | Encrypt at rest |
| `ai_provider_keys` | `.env` | LLM provider API keys | No | Optional per provider | High | Yes if exposed | environment | Keep untracked |
| `alert_keys` | `.env` | Telegram / alert credentials | No | Optional | High | Yes if exposed | environment | Keep untracked |

## Git Exposure Assessment

### Current tracking

- `.env` is gitignored and not tracked.
- `data/auth/auth_config.json` is gitignored and not tracked.
- `data/auth/users.db` is gitignored and not tracked.
- `data/portfolio/broker_auth.json` is gitignored and not tracked.

### Historical findings

| Finding | Evidence | Rotation Guidance |
| --- | --- | --- |
| Default admin fallback existed in source history | `git log -S "admin123" -- backend/auth/store.py` returned commit `f09ff0d5a0f39a2dda176a25047d37d44d619650` dated `2026-07-02` | Rotate any real admin credential derived from this pattern |
| Plaintext broker storage design existed in source history | `git log -S "broker_auth.json"` returned commits `d4077cd3c2884c0d859f08250345c0316c316c6a` and `16781cc634f718b022ee215c0d6d082e61181603` | Revoke/reconnect any real broker token persisted through the legacy plaintext path |

No active secret values were printed into the audit package.

## Authentication Policy

| Environment | Auth Enabled Default | External Access When Disabled | Setup Route | Production Safety |
| --- | --- | --- | --- | --- |
| `dev` | allowed to be off | blocked for non-loopback clients | allowed only via loopback | not production |
| `local` | allowed to be off | blocked for non-loopback clients | allowed only via loopback | not production |
| `test` | allowed to be off | blocked for non-loopback clients | allowed only via loopback | not production |
| `production` | must be on | not allowed | disabled | enforced at startup |

Runtime enforcement now occurs in `backend/auth/store.py` and `backend/main.py`.

## Admin Bootstrap Policy

- Historical fallback bootstrap credentials were removed.
- First-user bootstrap now requires explicit `ADMIN_EMAIL` and `ADMIN_PASSWORD` in environments where unattended provisioning is needed.
- Local/dev/test can still initialize an admin interactively through `/api/auth/setup`, but only from loopback clients.
- Production startup fails if auth is disabled.
- Production startup also fails if there are no existing users and no bootstrap credentials are provided.
- Password policy now requires at least `12` characters with uppercase, lowercase, and digit coverage.

## Broker Credential Handling

Previous behavior stored raw broker credentials in local JSON. Current behavior encrypts broker credentials before persistence:

- preferred mode: key material provided through `VEDA_BROKER_CREDENTIAL_SECRET`;
- fallback mode: local Fernet key file persisted to `data/auth/broker_credentials.key`;
- legacy plaintext credential files are detected and migrated forward on read.

This is an intentionally small-scope safety change. The broker subsystem itself was not redesigned.

## Tests Added

- `tests/test_auth_governance.py`
- `tests/test_broker_security.py`
- `tests/guardrails/test_secret_governance.py`

All three suites passed during P001 validation.
