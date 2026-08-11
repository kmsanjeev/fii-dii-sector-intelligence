# Activation & Rollback

Activation remains separate from implementation. Only an Admin may move a capability from `ACTIVATION_READY` to `ACTIVE`.

Rollback restores the prior active version or returns the governed capability to `INACTIVE` while preserving:

- evidence
- validation history
- shadow history
- activation history
