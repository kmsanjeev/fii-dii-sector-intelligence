# VEDA Astrology Source Authority Standard

Status: P002 baseline  
Contract version: `2026-08-10`

Current extension: `VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001` adds linked
work/witness/edition/passage/layer/assertion/variant/rights/lineage metadata
without replacing this P002 registry. Its implementation and pilots are in
`docs/current-state/knowledge-source-witness-standard-001/`.

## Purpose

This standard defines how VEDA registers astrology sources as machine-readable artifacts before any source is allowed to influence future rule migration, RAG, or ML work.

## Source of Truth

- Machine-readable records: `data/veda/research/astrology/sources/*.json`
- Schema: `schemas/astrology/source.schema.json`
- Validator: `scripts/validate_p002_astrology_registry.py`

## Controlled Source Classes

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

## Required Authority Dimensions

Each source record carries a structured `authority_profile` with separate scores for:

- `textual_authority`
- `traditional_authority`
- `translation_reliability`
- `cross_source_support`
- `empirical_support`
- `implementation_confidence`

`authority_score` is allowed only as an advisory summary value. It must never replace the dimensional profile.

## Authority Tiers

- `TIER_A`: primary classical source with verified usable edition or passage
- `TIER_B`: authoritative translation, commentary, or stable reference edition
- `TIER_C`: respected traditional or practitioner interpretation
- `TIER_D`: academic or empirical support source
- `TIER_E`: tertiary or internal synthesis
- `TIER_F`: informal weak support
- `TIER_U`: unknown or unverified

## Legal / Access Policy

Every source must declare one of:

- `PUBLIC_DOMAIN`
- `LICENSED_OR_COPYRIGHTED`
- `LIMITED_QUOTATION_ONLY`
- `METADATA_ONLY`
- `UNKNOWN`

P002 does not assume that public discoverability implies public-domain reuse rights.

## Evidence Type Separation

Every source must declare an `evidence_type`:

- `CLASSICAL_TEXTUAL`
- `TRADITIONAL_INTERPRETIVE`
- `MODERN_ASTROLOGY`
- `EMPIRICAL_MARKET`
- `INTERNAL_HYPOTHESIS`

This is the baseline rule that prevents AstroFinance hypotheses from being mislabeled as classical textual evidence.
