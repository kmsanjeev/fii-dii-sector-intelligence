# VEDA Astrology Versioning Standard

Status: P002 baseline  
Contract version: `2026-08-10`

## Artifact IDs

- Sources: `VEDA-SRC-000001`
- Passages: `VEDA-PSG-000001`
- Claims: `VEDA-CLM-000001`
- Conflicts: `VEDA-CNF-000001`
- Approvals: `VEDA-APR-000001`
- Policies: `VEDA-PLC-000001`
- Legacy registers: `VEDA-LGC-000001`
- Legacy rule entries: `VEDA-LRY-000001`

IDs are immutable. Titles are not identifiers.

## Version Fields

Every governed artifact must carry:

- `version`
- `status`
- `created_at`
- `created_by`
- `updated_at`
- `updated_by`
- `change_reason`
- `supersedes`
- `superseded_by`

## Version Format

- `version` uses semantic versioning, for example `1.0.0`
- timestamps use ISO-8601 strings

## Change Policy

- No silent overwrite of approved research
- New evidence must update `change_reason`
- supersession must be explicit
- approved artifacts may be revised only through a new versioned record

## Legacy Boundary

Existing production astrology remains outside this governed layer until later migration.  
P002 marks those runtime rules as legacy rather than inventing backfilled provenance.
