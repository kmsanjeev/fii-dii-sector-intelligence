# VEDA-P007 Source Intelligence Policy

P007 binds the P002 source-governance model into autonomous research.

## Active Source Classes

- `CLASSICAL_PRIMARY`
- `CLASSICAL_COMMENTARY`
- `TRADITIONAL_SECONDARY`
- `REFERENCE_EDITION`
- `MODERN_PRACTITIONER`
- `FOLKLORE_OR_UNVERIFIED`

## Runtime Behavior

- governed passages from `data/veda/research/astrology/` are treated as evidentiary sources
- local upload corpus under `data/veda/uploads/` is treated as discovery-only unless better provenance is verified
- discovery-only material can seed candidates, but those candidates remain lower-confidence and non-authoritative
- `REFERENCE_NOT_VERIFIED` is preserved rather than upgraded silently

## Pilot Corpus Use

Pilot A and Pilot C primarily use governed P002 passages. Pilot B uses upload-derived discovery material to exercise provenance recovery while preserving explicit discovery-only metadata.
