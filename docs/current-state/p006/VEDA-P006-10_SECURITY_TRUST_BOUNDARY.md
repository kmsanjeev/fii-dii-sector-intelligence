# VEDA-P006 Security Trust Boundary

Date baseline: `2026-08-10`

P006 adds research-specific trust boundaries without altering the existing P001 auth governance.

## Guarded Areas

- unsafe URI schemes are rejected
- external content is sanitized before use
- prompt-injection patterns are detected and recorded as metadata
- admin mutation routes require `require_admin`
- approval and promotion are separate states
- provider content cannot redefine system policy or tool permissions

Blocked URI schemes include:

- `file`
- `javascript`
- `data`
- `ftp`
- `gopher`
- `chrome`
- `vscode`

Prompt-injection handling:

- source content is treated as data
- prompt-like instructions from retrieved material are not trusted
- the security test suite proves malicious synthetic content is flagged rather than executed as instruction

Budget and loop protections:

- `max_queries`
- `max_sources`
- `max_provider_calls`
- `max_runtime_seconds`
- `max_model_calls`
- `max_cost`
- `max_follow_up_depth`
- `max_retries`
- `cooldown_seconds`

Security tests added by P006:

- unsafe URL rejection
- prompt-injection isolation
- admin-only decision endpoint enforcement
