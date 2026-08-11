# VEDA-P007 Claim Ontology Mapping

P007 maps extracted claim text to the P003 canonical ontology instead of inventing new free-text concept labels at candidate time.

## Current Mapping Capabilities

- graha aliases, including Sanskrit and English names
- dasha and mahadasha vocabulary
- governed yoga and dignity labels already present in the ontology
- ontology-gap tagging for concepts not yet represented cleanly

## Current Gap Handling

When a concept cannot be mapped safely, P007 records an ontology gap rather than silently inventing a runtime concept.

Observed gap example:

- `PANCHA_MAHAPURUSHA_FAMILY`

This gap remains reviewable and can later become an ontology-extension candidate instead of being embedded directly in production code.
