# Language Targets

The authoritative roadmap has no explicit content-language target list. It
only identifies LANG-002+ as additional language packs requiring language-
specific authorization. Existing voice support (`en`, `hi`, `ta`, `te`, `bn`,
`mr`, `gu`) and LANG-001's English/Hindi/Hinglish expression corpus do not
authorize full translated Jyotisha content.

Current implementation:

- `en`: canonical English baseline, deterministic and complete for the seed
  registry/messages, `REVIEW_PENDING` for presentation review.
- Other locales: not implemented as content packs; requests fall back to
  English with explicit `fallback_used` metadata.

Decision: `LANGUAGE_TARGET_SELECTION_REQUIRED`. No founder priority was guessed,
and no language-specific semantic corpus was created.
