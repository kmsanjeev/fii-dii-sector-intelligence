# VEDA Astrology Citation Standard

Status: P002 baseline  
Contract version: `2026-08-10`

## Citation Chain

VEDA must preserve the following chain:

`source -> passage -> claim -> future rule`

The four layers are not interchangeable.

## Storage

- Passages: `data/veda/research/astrology/passages/*.json`
- Claims: `data/veda/research/astrology/claims/*.json`
- Schemas:
  - `schemas/astrology/passage.schema.json`
  - `schemas/astrology/claim.schema.json`

## Passage Rules

Where available, a passage records:

- `source_id`
- `work`
- `chapter`
- `section`
- `verse_start`
- `verse_end`
- `page_start`
- `page_end`
- `original_text`
- `transliteration`
- `translation`
- `translator`
- `commentator`
- `citation_label`

If chapter / verse / page details are not fully verified, the record must state that explicitly through `verification_status` rather than inventing precision.

## Claim Rules

Claims must:

- reference one or more `source_passages`
- declare `interpretation_type`
- declare `support_level`
- declare `evidence_types`
- carry workflow and approval states

A claim is a research interpretation of evidence. It is not yet an implementation contract.

## Quotation Policy

- Do not fabricate Sanskrit.
- Do not fabricate chapter or verse references.
- Prefer paraphrase where direct quotation is unnecessary.
- If a passage comes from a translator note or editorial note, record that fact explicitly.
