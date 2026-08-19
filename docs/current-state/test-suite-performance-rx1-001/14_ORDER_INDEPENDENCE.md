# Order and isolation

The remediation does not change pytest ordering or add parallel execution.
The new inventory test proves deterministic sorted traversal and preserves
temporary-root behavior. The full suite completed from the normal collection
order after the change. A formal randomized-order campaign was not authorized
because repository tests write generated artifacts and use shared caches;
this remains a follow-up diagnostic, not a release claim.
