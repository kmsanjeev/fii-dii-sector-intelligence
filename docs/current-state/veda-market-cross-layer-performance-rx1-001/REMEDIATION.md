# Remediation

Changed file: `engines/participant/institutional_contract.py`.

1. Participant and cash snapshots are computed once per institutional-contract
   request and passed to the divergence and quality calculations.
2. The rolling-window helper retains only the largest requested window. This
   is equivalent for the current-window contract and preserves missing-value
   and completeness states.
3. The latest normalized rows are reused instead of repeatedly copying and
   sorting the same frames within the request.

This is request-scoped reuse, not a process-level cache. Therefore no cache
invalidation policy or restart requirement was introduced. The existing data
loader reload model and freshness metadata remain authoritative.

No semantic versions changed. No database migration, Redis, background worker,
Market source change, or external provider change was introduced.
