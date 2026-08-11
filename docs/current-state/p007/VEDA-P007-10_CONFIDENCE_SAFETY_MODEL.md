# VEDA-P007 Confidence And Safety Model

P007 keeps confidence multidimensional and preserves high-stakes controls from P002 and P005-R1.

## Confidence Dimensions

- `source_confidence`
- `authority_confidence`
- `cross_source_confidence`
- `provenance_confidence`
- `novelty_confidence`
- `contradiction_confidence`
- `domain_confidence`

## Safety Behavior

- `FINANCE`, `HEALTH`, `LONGEVITY`, `DEATH`, `FERTILITY`, and `REMEDIES` remain high-stakes
- high-stakes candidates require human approval
- auto promotion remains disabled
- discovery-only or provenance-only candidates are not upgraded into authoritative knowledge

## Security Coverage

P007 adds astrology-domain security tests for:

- prompt-injection isolation
- fabricated or unsupported source rejection
- discovery-only handling
