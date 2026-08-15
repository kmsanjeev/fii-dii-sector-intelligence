# VEDA-AUTOLOOP-R2

Status: `IN IMPLEMENTATION`.

R2 reconciles the persistent controller lifecycle and autonomous activity
identity. Stable activity records now carry `activity_id`, `track`,
`activity_type`, and `title`; validation-only completion is distinct from
repository mutation; and final `VERIFYING` state is reconciled to `READY` on
healthy bounded exit.

The reconciliation pass classifies tracked and untracked outputs. The known
PRED-004 source-provenance report is validated as authoritative activity
output and is selectively staged and pushed; runtime logs remain ignored.
Unrelated files remain preserved and cause `REPAIR_REQUIRED` rather than
blind mutation.
