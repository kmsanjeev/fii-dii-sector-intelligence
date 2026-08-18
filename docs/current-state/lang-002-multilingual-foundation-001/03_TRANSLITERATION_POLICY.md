# Transliteration and Jyotisha Terminology Policy

The existing ontology records transliteration strings such as `Surya`,
`Chandra`, `Vimshamsha`, and `Navamsha`. These are retained as legacy ontology
values and are not silently relabelled as IAST.

For future reviewed Sanskrit presentation, VEDA uses **IAST when the source
edition or governed record verifies it**. Informal spellings remain aliases,
not competing canonical terms. IAST, ITRANS, Harvard-Kyoto, and casual Roman
spellings must not be mixed inside a new canonical value.

The registry preserves `sanskrit`, `transliteration`, and
`transliteration_status` separately. Missing source-verified forms remain
explicitly `NOT_RECORDED` or `LEGACY_ONTOLOGY_VALUE_NOT_IAST`; the renderer
does not invent derivations. Devanagari and IAST strings are presentation
fields only and cannot alter a canonical ID or rule.
