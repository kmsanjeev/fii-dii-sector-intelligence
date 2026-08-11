# VEDA-P008 Source Explorer

Date: `2026-08-11`

The Source Explorer exposes research source observations through the P006/P007 source records already persisted in the platform.

## Displayed Source Fields

- source title
- author
- publisher
- source state
- authority level
- source type
- retrieval time
- candidate ids
- claims supported
- trust metadata
- raw reference metadata

## Important Current Implementation Note

The P008 source explorer uses the existing source-observation summaries returned alongside run views and candidate details. It does not introduce a second source store or duplicate the observation model.

## Security Posture

- evidence is rendered as data
- suspicious source metadata remains visible
- no source HTML execution path exists in the UI

