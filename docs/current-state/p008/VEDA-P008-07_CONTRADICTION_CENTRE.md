# VEDA-P008 Contradiction Centre

Date: `2026-08-11`

P008 surfaces contradictions through the queue/contradiction views and candidate detail, backed by the P002 conflict model.

## Delivered Capability

- contradiction-only queue view
- candidate-level conflict visibility
- conflict ids, types, analysis, and resolution status shown in candidate detail
- admin decision payload may include conflict resolution metadata

## Decision Behavior

- if one conflict exists, the service can apply the selected conflict resolution without requiring a separate conflict id
- if multiple conflicts exist, an explicit conflict selection is required
- contradiction handling remains audited through approval and ledger records

## Important Constraint

P008 does not auto-resolve contradictions based on confidence alone.

