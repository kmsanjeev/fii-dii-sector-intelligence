# VEDA-P010 Source and Passage Materialization

The astrology materializer converts approved candidate evidence into governed P002 artifacts without fabricating metadata.

Implemented behavior:
- deduplicate sources by requested ID, canonical URL, and normalized title;
- deduplicate passages by requested ID or stable `(source_id, citation_label, translation)` identity;
- preserve explicit `verification_status`;
- keep lineage to `evidence_id`, `observation_id`, `run_id`, and `mission_id`;
- preserve translator, commentator, edition, and citation fields when available;
- avoid creating duplicate source files when existing governed records already match.

This behavior is covered by the conditional astrology promotion test, including the case where governed passages are reused rather than recreated.
