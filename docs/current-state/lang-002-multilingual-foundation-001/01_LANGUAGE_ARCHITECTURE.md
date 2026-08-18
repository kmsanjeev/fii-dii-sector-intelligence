# Language Architecture

The dependency direction is fixed:

`canonical ontology/governed facts -> language-neutral structured output -> locale presentation -> user display`

`engines/ai/knowledge/language_foundation.py` is a deterministic presentation
boundary. It loads `data/veda/localization/canonical_term_registry.json` and
locale packs under `data/veda/localization/locales/`. It does not calculate a
chart, evaluate a rule, retrieve knowledge, select a source, or call a model.

`render_structured()` returns `fact_payload` and `display` separately. The
canonical payload retains IDs, enums, numbers, dates, source metadata,
confidence, and governance states. Display fields are additive and may never
be used as calculation inputs.

Existing LANG-001, COMM-001, COMM-002, ChatEngine, voice/TTS, P023/P030/P032,
and RAG boundaries remain owners of their existing responsibilities. No
parallel Jyotisha engine, response owner, retriever, or language-specific
knowledge store was created.
