# VEDA-P008 Evidence Review

Date: `2026-08-11`

Candidate detail explicitly exposes evidence instead of asking Admin to approve model summaries blindly.

## Candidate Detail Sections

- claim
- recommendation
- confidence
- current VEDA knowledge comparison
- contradictions
- supporting sources
- passages/evidence
- research history
- decision history
- admin decision panel

## Evidence Presentation Rules

The UI distinguishes:

- source text
- translation
- model summary
- model inference

The implementation uses plain text rendering only. No untrusted HTML is rendered.

## Source Detail Signals

- source title
- author
- state
- authority level
- retrieval timestamp
- raw reference metadata
- trust metadata

