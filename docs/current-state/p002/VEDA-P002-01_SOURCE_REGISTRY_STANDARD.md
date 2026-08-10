# VEDA-P002-01 Source Registry Standard

## Storage Model

P002 uses JSON as the authoritative machine-readable storage format.

- root: `data/veda/research/astrology/`
- sources: `sources/*.json`
- passages: `passages/*.json`
- claims: `claims/*.json`
- conflicts: `conflicts/*.json`
- approvals: `approvals/*.json`
- policies: `policies/*.json`
- legacy register: `legacy/*.json`

## Implementation Files

- model + validator: `engines/ai/knowledge/astrology_governance.py`
- schema export: `scripts/export_p002_astrology_schemas.py`
- registry validator: `scripts/validate_p002_astrology_registry.py`

## Controlled Source Classes

The registry now enforces the following classes:

- `CLASSICAL_PRIMARY`
- `CLASSICAL_COMMENTARY`
- `TRADITIONAL_SECONDARY`
- `MODERN_PRACTITIONER`
- `ACADEMIC_SECONDARY`
- `EMPIRICAL_RESEARCH`
- `REFERENCE_EDITION`
- `DERIVED_INTERNAL`
- `HYPOTHESIS`
- `FOLKLORE_OR_UNVERIFIED`

## Current Pilot Inventory

- `VEDA-SRC-000001` to `VEDA-SRC-000006`: external Jyotisha sources
- `VEDA-SRC-000007`: internal pilot synthesis artifact
