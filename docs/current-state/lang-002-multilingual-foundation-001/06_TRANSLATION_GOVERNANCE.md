# Translation Governance

Translations are presentation artifacts, never independent astrology
knowledge. Every future pack must preserve the original canonical term/message
ID, source ID, proposition ID, locale, version, status, and review state.

Review states supported by the foundation are `MACHINE_DRAFT`,
`REVIEW_PENDING`, `HUMAN_REVIEWED`, `SOURCE_REVIEWED`, and
`APPROVED_PRESENTATION`. The current English pack is a canonical baseline with
`REVIEW_PENDING`; no human review is claimed.

Runtime translation is deterministic and provider-free. An AI-assisted draft,
if later used offline, remains a draft until governed review. No translated
text may promote a `RESEARCH_ONLY`, `NOT_VALIDATED`, `NOT_AUTHORIZED`, or
`PRED-M4`-blocked state.
