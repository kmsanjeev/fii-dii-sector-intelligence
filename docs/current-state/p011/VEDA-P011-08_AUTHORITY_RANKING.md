# Authority Ranking

Approved-core ranking does not use lexical overlap alone.

Current scoring inputs:
- query token overlap
- ontology-expanded token overlap
- approved-core authority confidence
- cross-source confidence
- provenance confidence
- domain confidence
- current-version boost

Unified post-rank then gives additional preference to approved-core current versions over weaker or non-current items.
