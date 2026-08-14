# COMM-001 Existing-State Audit

COMM-001 reuses the existing `engines/ai/chatbot/conversation_intelligence.py`
analyzer, `ChatEngine`, `/api/chat` context, STD-003 expression metadata, and
bounded conversation history. No parallel classifier, response generator,
memory store, knowledge store, or provider call was added.

Existing: deterministic analyzer, prompt guidance, ChatEngine hook, diagnostic
context, tests, and benchmark fixture.

Reuse: shared ChatEngine, RAG, orchestration, and STD-003 contracts.
Extend: confidence, secondary types, intent/pragmatic fields, state stability,
benchmark coverage, and failure isolation.
Wrap: the ChatEngine analyzer call with neutral fallback.
New required: COMM-001 tests, transition fixture, and evidence records.

The gap was execution depth, not a missing subsystem.
