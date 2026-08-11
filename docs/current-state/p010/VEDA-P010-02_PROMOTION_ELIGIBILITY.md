# VEDA-P010 Promotion Eligibility

Only candidates already in `PROMOTION_READY` can enter the promotion path.

The implemented eligibility gate requires:
- an existing candidate;
- a valid Admin approval event with `actor_type = ADMIN`;
- accepted evidence with observation linkage;
- at least one non-`discovery_only` source;
- promotable ontology/claim structure or a domain-appropriate generic core path.

The gate explicitly blocks:
- `PENDING`
- `UNDER_REVIEW`
- `REJECTED`
- `NEEDS_MORE_RESEARCH`
- `ARCHIVED`
- discovery-only evidence attempting to justify source-validated promotion by itself.

This is enforced both in service logic and in P010 tests. The blocked astrology legacy-provenance pilot proves the discovery-only restriction.
