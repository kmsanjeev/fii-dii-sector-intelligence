# VEDA-P003-05 Provenance Model

## Required Traceability Chain

P003 preserves the P002 governance boundary:

`RULE -> CLAIM -> PASSAGE -> SOURCE`

## Provenance Fields

Every governed rule can link to:

- `source_ids`
- `passage_ids`
- `claim_ids`
- `conflict_ids`

## Current Governed Usage

- `VEDA-RUL-DASHA-000001`
  - linked to P002 claims `VEDA-CLM-000001` and `VEDA-CLM-000002`
- `VEDA-RUL-DASHA-000002`
  - linked to P002 claims `VEDA-CLM-000005` and `VEDA-CLM-000006`
  - linked to conflict `VEDA-CNF-000001`

## Legacy Mapping Boundary

Where provenance is not yet governed:

- rules remain `DRAFT`
- `legacy_provenance_status` is used explicitly
- no false classical attribution is added retroactively

That is the current state for:

- `VEDA-RUL-DIGNITY-000001`
- `VEDA-RUL-YOGA-000001`

## High-Stakes Inheritance

The rule schema supports:

- `high_stakes`
- `requires_safety_review`
- `allowed_output_mode`

This preserves the P002 policy boundary for:

- health
- longevity
- death
- fertility
- finance
- remedies

No new high-stakes production rule was added in P003.
