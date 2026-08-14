# LANG-001 Existing-State Audit

Existing: STD-003 dictionaries and language/script detection inside
`conversation_intelligence.py`, COMM-001 context contract, ChatEngine prompt
guidance, shared RAG and knowledge governance.

Reuse: the existing ChatEngine, COMM-001 analyzer, STD-001 knowledge-zone
principles, and local deterministic runtime path.

Extend: one canonical `language_intelligence.py` registry/resolver,
expression evidence in `ConversationContext`, seed corpus, benchmark, and
focused tests.

New required: the governed Wave-1 registry because no reusable language
registry existed. No parallel chatbot, conversation store, or language RAG
corpus was created.
