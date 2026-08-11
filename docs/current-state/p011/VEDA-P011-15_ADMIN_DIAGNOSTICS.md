# Admin Diagnostics

P011 adds an Admin-only diagnostics surface at:
- `POST /api/research/rag/diagnostics`

Supported modes:
- `unified`
- `legacy`
- `shadow`

The Admin console now renders:
- ontology matches
- retrieval audit JSON
- retrieved result cards
- approved-core diagnostics payload
- final assembled context

This lets governance inspect retrieval before generation.
