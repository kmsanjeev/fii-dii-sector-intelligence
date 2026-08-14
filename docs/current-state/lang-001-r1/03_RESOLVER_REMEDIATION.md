# Resolver Remediation

The existing `language_intelligence.py` registry and resolver were extended.
No parallel resolver or provider fallback was created.

Changes include Unicode NFKC normalization, controlled Hindi inflection and
mixed-script aliases, language-aware duplicate precedence, longest-expression
selection, broader generalizable literal cues, Hindi/English metalinguistic
markers, domain-aware `MD` abbreviation typing, and safe unknown handling.

The existing ChatEngine, COMM-001 bridge, expression registry, and local
deterministic lookup remain the single production path.
