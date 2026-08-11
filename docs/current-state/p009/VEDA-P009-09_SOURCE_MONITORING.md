# Source Monitoring

P009 adds observation version awareness through canonical URI comparison.

Each new observation now records:
- canonical URI
- content hash
- change status

Current change classifications:
- `NEW`
- `UNCHANGED`
- `UPDATED`

Removed-source monitoring is not yet fully operationalized in this phase and remains future work.
