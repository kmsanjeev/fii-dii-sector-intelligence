# VEDA-P007 Source Passage Extraction

P007 uses the generic P006 observation/evidence pipeline and adds Jyotisha-aware provider documents.

## Observation Sources

- governed passages from `data/veda/research/astrology/passages/`
- local discovery-only upload metadata from `data/veda/uploads/*.meta.json`

## Preserved Metadata

- `source_id`
- `passage_id`
- `source_class`
- `verification_status`
- `authority_score`
- `discovery_only`
- `prompt_injection_detected`
- `legacy_rule_id`
- `claim_ids`
- `conflict_ids`

## OCR Tolerance

The local-document provider now uses OCR-tolerant token scoring for upload discovery. This was required to make provenance-recovery missions work against noisy historical extracts without falsely upgrading them into primary evidence.
