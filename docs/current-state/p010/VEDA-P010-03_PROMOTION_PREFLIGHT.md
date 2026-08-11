# VEDA-P010 Promotion Preflight

Every promotion request now runs a deterministic preflight before materialization.

Checks implemented:
- `P1` candidate status
- `P2` Admin approval validity
- `P3` evidence integrity
- `P4` source eligibility
- `P5` passage or evidence linkage
- `P6` claim normalization
- `P7` ontology mapping
- `P8` conflict state
- `P9` duplicate/core overlap
- `P10` version impact
- `P11` high-stakes policy
- `P12` schema validation readiness

Result states:
- `PASS`
- `PASS_WITH_CONDITIONS`
- `BLOCKED`

Preflight output records:
- blocking reasons;
- warnings;
- required actions;
- proposed operation (`ADD_CORE_KNOWLEDGE`, `MERGE_VERSION_UPDATE`, `PROMOTE_WITH_CONDITIONS`).

Preflight is exposed through both the service API and the Admin UI before promotion is attempted.
