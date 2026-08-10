# VEDA-P003-01 Ontology Standard

## Purpose

P003 defines the canonical vocabulary VEDA will use for:

- research governance
- calculation facts
- rule conditions
- future rule evaluation
- future RAG metadata
- future ML feature IDs

## Canonical Naming

Each entity record carries:

- `entity_id`
- `canonical_name`
- `entity_type`
- `sanskrit_name`
- `transliteration`
- `aliases`
- `description`
- `source_status`
- `deprecated_aliases`
- `version`

## Stable ID Patterns

- Grahas: `VEDA-GRAHA-*`
- Rashis: `VEDA-RASHI-*`
- Bhavas: `VEDA-BHAVA-01` ... `VEDA-BHAVA-12`
- Nakshatras: `VEDA-NAK-*`
- Vargas: `VEDA-VARGA-D09`
- Dashas / timing: `VEDA-DASHA-*`, `VEDA-TIMING-*`
- Rule IDs: `VEDA-RUL-AREA-000001`
- Legacy mappings: `VEDA-LMP-000001`

## Entity Types Present

- `GRAHA`
- `RASHI`
- `BHAVA`
- `NAKSHATRA`
- `VARGA`
- `DASHA`
- `TIMING`
- `RELATIONSHIP`
- `DIGNITY`
- `DOMAIN`
- `HOUSE_CLASSIFICATION`
- `YOGA`

## Storage Layout

- ontology data: `data/veda/ontology/`
- ontology relations: `data/veda/ontology/relations/`
- governed rules: `data/veda/rules/approved/`
- draft legacy mappings: `data/veda/rules/draft/`
- legacy mapping records: `data/veda/rules/legacy_mappings/`
- contract samples: `data/veda/rules/contracts/`

## Source Status Policy

- `CURATED_CANONICAL`: normalized canonical vocabulary, not yet a research claim
- `SOURCE_VALIDATED`: tied to governed source evidence
- `LEGACY_UNGOVERNED`: present because current runtime uses or references it
- `UNKNOWN`: intentionally reserved for future validation

## Repository Governance Note

`.gitignore` was updated in P003 so that governed machine-readable artifacts under:

- `data/veda/research/astrology/`
- `data/veda/ontology/`
- `data/veda/rules/`

remain reviewable, while other runtime/cache content under `data/veda/` stays ignored.
