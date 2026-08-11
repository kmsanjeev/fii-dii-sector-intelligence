# Passage Retrieval

Approved-core results now retain:
- claim IDs
- passage IDs
- source IDs
- rule IDs
- citation excerpts

Passage lookup behavior:
- direct passage citations are preferred when passage IDs exist
- source-only fallback is used only when no governed passage record is available
- conflict details remain linked beside the supporting passage lineage

The goal is to let VEDA answer from governed passage support rather than only from synthesized claim text.
