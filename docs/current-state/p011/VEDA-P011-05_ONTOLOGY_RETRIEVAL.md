# Ontology Retrieval

Approved-core retrieval expands queries through the P003 ontology registry.

Current behavior:
- alias resolution supports canonical and alternate names such as `Guru` and `Jupiter`
- ontology matches are returned in diagnostics
- query expansion feeds approved-core scoring
- non-matching queries remain allowed, but approved-core astrology retrieval is suppressed unless the query is astrology-like

Unresolved concepts are not silently turned into new ontology entities during answer generation.
