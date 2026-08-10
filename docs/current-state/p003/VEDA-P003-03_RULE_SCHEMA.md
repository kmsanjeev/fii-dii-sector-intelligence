# VEDA-P003-03 Rule Schema

## Purpose

P003 defines the canonical machine-readable representation of a Jyotisha rule without switching production execution to that schema.

## Core Fields

- `rule_id`
- `version`
- `title`
- `domain`
- `subdomain`
- `rule_type`
- `status`
- `source_class`
- `approval_status`
- `evidence_types`
- `authority`
- `provenance`
- `conditions`
- `modifiers`
- `exceptions`
- `confirmations`
- `activations`
- `outcomes`
- `depends_on_rule_ids`
- `cancelled_by_rule_ids`

## Lifecycle States Supported

- `DRAFT`
- `RESEARCHING`
- `SOURCE_VALIDATED`
- `APPROVED`
- `APPROVED_WITH_CONDITIONS`
- `IMPLEMENTATION_READY`
- `IMPLEMENTED`
- `VALIDATED`
- `DEPRECATED`
- `SUPERSEDED`
- `REJECTED`

## Current Pilot Rules

| Rule ID | Status | Provenance | Purpose |
| --- | --- | --- | --- |
| `VEDA-RUL-DASHA-000001` | `IMPLEMENTATION_READY` | governed | Vimshottari sequence + birth-balance baseline |
| `VEDA-RUL-DASHA-000002` | `APPROVED_WITH_CONDITIONS` | governed + conflict-linked | Vimshottari default-path coexistence policy |
| `VEDA-RUL-DIGNITY-000001` | `DRAFT` | legacy-unsourced | sample dignity mapping from current runtime |
| `VEDA-RUL-YOGA-000001` | `DRAFT` | legacy-unsourced | sample Gaja Kesari mapping from current runtime |

## Provenance Enforcement

The rule model now enforces:

- approved / implementation-ready rules must carry governed provenance references
- draft legacy mappings may use `legacy_provenance_status`
- approved rules may not substitute `legacy_provenance_status` for real provenance

## AstroFinance Separation

The schema supports `evidence_types` from P002, including:

- `CLASSICAL_TEXTUAL`
- `TRADITIONAL_INTERPRETIVE`
- `MODERN_ASTROLOGY`
- `EMPIRICAL_MARKET`
- `INTERNAL_HYPOTHESIS`

This preserves the required boundary between classical Jyotisha and AstroFinance-style hypotheses.
