# Griha Pravesha Context Audit

The inspected primary house-building witness describes a sequence rather than
a modern property questionnaire: prepared ground and commencement, entry into
a half-built or wholly built house, foundation work after puja, and a later
house-entry passage. It does not clearly establish modern legal possession,
habitability certification, or first-residence semantics.

The diagnostic context schema therefore distinguishes:

- `construction_state`: required enum `HALF_BUILT` or `WHOLLY_BUILT`;
- `puja_completed`: required Boolean for the source-bounded post-puja entry
  context;
- `first_occupancy`: source variant / not validated;
- `habitable` and `legal_possession`: optional practical disclosure fields,
  never astrological predicates.

Missing required context abstains. Invalid or unknown context fails closed.
No production request schema was changed. The existing runtime taxonomy keeps
House Entry disabled and taxonomy-only.
