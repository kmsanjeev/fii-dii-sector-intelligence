# VEDA Astrology Contradiction Policy

Status: P002 baseline  
Contract version: `2026-08-10`

## Purpose

Jyotisha sources do not always agree. VEDA must preserve disagreement instead of flattening it into a false consensus.

## Storage

- Conflicts: `data/veda/research/astrology/conflicts/*.json`
- Schema: `schemas/astrology/conflict.schema.json`

## Supported Conflict Types

- `DIRECT_CONTRADICTION`
- `PARTIAL_CONTRADICTION`
- `DIFFERENT_SCOPE`
- `DIFFERENT_CONDITION`
- `DIFFERENT_SCHOOL`
- `TRANSLATION_VARIANCE`
- `COMMENTARIAL_VARIANCE`
- `TEMPORAL_OR_TRADITION_VARIANCE`
- `APPARENT_ONLY`
- `UNRESOLVED`

## Resolution States

- `UNRESOLVED`
- `COEXIST`
- `CONTEXT_DEPENDENT`
- `SOURCE_A_PREFERRED`
- `SOURCE_B_PREFERRED`
- `COMPOSITE_RULE`
- `INSUFFICIENT_EVIDENCE`

## Mandatory Practice

- Never silently discard a conflicting rule.
- Never treat a commentarial gloss as if it cancelled a verified classical passage.
- Record whether the disagreement affects implementation, research, or only wording.
- If the current runtime already behaves one way, record that as implementation context, not as proof of authority.
