# Hybrid Retrieval

The unified path now fuses:
- BM25 results
- FAISS results when enabled
- direct approved-core matches

Fusion behavior:
- approved-core matches are injected through a dedicated approved-core query path
- superseded, deprecated, and withdrawn approved-core versions are excluded from active retrieval
- approved-core signals receive authority-aware post-rank boosts
- non-astrology queries do not trigger approved-core astrology retrieval

This preserves the existing unified retrieval contract while making governed knowledge first-class.
