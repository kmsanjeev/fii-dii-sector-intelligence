# Conflict-Aware Retrieval

Conflict metadata is now carried from approved-core lineage into retrieval results and context assembly.

Current behavior:
- known approved-core conflicts render in a dedicated `KNOWN CONFLICTS` section
- conflict details include type, status, and clipped analysis
- chat prompt rules require disagreement to stay visible instead of being flattened
- diagnostics expose conflict counts and known conflict payloads

This preserves P002 contradiction governance inside runtime retrieval.
