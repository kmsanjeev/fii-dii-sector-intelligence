# Chat Integration

Approved-core retrieval is integrated into the existing chat contract rather than replacing it.

Changes:
- `ChatEngine.last_local_evidence` now tracks knowledge classes, conflict counts, citation counts, and approved-core counts
- `ChatEngine.last_retrieval_audit` now includes approved-core and citation hit counts
- source-transparency prompt rules now mention governed Veda knowledge explicitly

Retrieval modes preserved:
- unified
- legacy
- shadow
