# LANG-001 Architecture

`resolve_expressions()` is the single deterministic language lookup boundary.
It returns canonical records, literal/idiomatic/metalinguistic resolution,
confidence, usage permission, and unknown candidates. COMM-001 consumes this
result and ChatEngine remains the response owner.

Known expression resolution requires no provider call and does not write to
general Jyotisha RAG. Unknown expressions return `UNKNOWN_EXPRESSION` and a
governed research-required candidate instead of an invented definition.
