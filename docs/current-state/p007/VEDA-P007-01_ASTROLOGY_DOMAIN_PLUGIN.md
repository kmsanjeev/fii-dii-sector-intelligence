# VEDA-P007 Astrology Domain Plugin

Primary files:

- `engines/ai/research/domains/vedic_astrology/plugin.py`
- `engines/ai/research/domains/vedic_astrology/provider.py`
- `engines/ai/research/domains/vedic_astrology/mission_templates.py`

## Responsibilities

- classify source authority using P002 source classes
- normalize extracted claims into machine-readable candidate payloads
- map candidate text to the P003 ontology
- compare candidates against approved core and legacy knowledge
- detect contradiction against approved core and pending candidates
- classify safety, including high-stakes inheritance
- generate follow-up missions without bypassing Admin approval

## Domain Registration

- domain id: `VEDA-DOMAIN-VEDIC-ASTROLOGY`
- status: `ACTIVE`
- ontology namespace: `VEDA`
- auto promotion: `false`
- approval policy: `HUMAN_APPROVAL_REQUIRED`

## Provider Boundary

The plugin contains Jyotisha-specific research logic only. Mission persistence, approvals, ledgering, validation stages, and scheduling remain in the generic P006 platform.
