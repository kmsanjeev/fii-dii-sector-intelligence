# Expression Model

The canonical `ExpressionRecord` supports shared expression types, language,
script, variant, surface forms, meanings, alternate meanings, pragmatic
functions, register, sensitivity, domain, time relevance, confidence,
provenance, knowledge zone, status, and version metadata.

Hindi category names are normalized to the shared `IDIOM`, `PROVERB`, and
`COLLOQUIALISM` enums. Repeated surfaces are keyed by language plus canonical
expression, preserving cross-language context without duplicate systems.
