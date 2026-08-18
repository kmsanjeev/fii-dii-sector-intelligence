# VEDA-LANG-002-MULTILINGUAL-FOUNDATION-001 — Baseline Reconciliation

Starting commit: `cc91fbd1cd3adf28fd7a70235acd67c46bcbbc9a` on `main`.

The tracked tree contains one pre-existing unrelated edit in
`data/reference/city_coords_cache.csv`. It is preserved and excluded from
LANG-002 staging.

| Existing capability | State | LANG-002 decision |
| --- | --- | --- |
| LANG-001 expression understanding | IMPLEMENTED / FROZEN | Reuse; do not replace its resolver |
| LANG-001-R1 resolution hardening | IMPLEMENTED / FROZEN | Reuse its canonical expression boundary |
| Voice locale casting | Existing `en`, `hi`, `ta`, `te`, `bn`, `mr`, `gu` | Treat as TTS capability, not content-language authorization |
| Jyotisha ontology IDs and aliases | Existing curated ontology | Reuse as presentation vocabulary inputs |
| Source/citation metadata | Existing governed records | Preserve unchanged in structured payloads |
| Language-neutral structured output | Partial | Extend with a deterministic presentation wrapper |
| Locale resource loader/fallback | Not found | New, bounded foundation required |
| Translation review state | Not found for this layer | Add metadata; do not claim human review |

Authoritative roadmap state before this activity: `LANG-002+ = PLANNED` and no
explicit target-language list is present. Starting decision:
`PARTIAL_LANGUAGE_INFRASTRUCTURE_EXISTS`.

The implementation therefore provides the canonical English baseline and a
future-language-compatible locale boundary, while returning
`LANGUAGE_TARGET_SELECTION_REQUIRED` for additional content packs.
