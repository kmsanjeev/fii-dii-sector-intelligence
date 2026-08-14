# COMM-002 Existing-State Audit

## Ownership

The existing `ChatEngine` remains the only response generator and final response owner. COMM-001 owns conversational understanding; LANG-001 and LANG-001-R1 own Wave-1 expression resolution; COMM-002 owns deterministic presentation adaptation. The chat router, session history, safety controls, RAG composition, and provider boundary are reused.

## Reuse Decision

| Component | Existing | Reuse/extend | New | Reason |
|---|---|---|---|---|
| ChatEngine | `engines/ai/chatbot/chat_engine.py` | Reuse and extend | No | Preserve response ownership and legacy requests. |
| Conversation analyzer | `conversation_intelligence.py` | Reuse | No | COMM-001 already provides typed context. |
| Language resolver | LANG-001/R1 | Reuse | No | Expression evidence and usage controls remain canonical. |
| Prompt guidance | Existing context guidance | Extend | No | Add bounded adaptation instructions only. |
| Response profile | Not previously present | New small value object | Yes | One serializable contract for adaptation dimensions. |
| Conversation memory | Existing ChatEngine history | Reuse | No | Repetition and continuity use available recent turns. |

No parallel chatbot, response owner, conversation store, RAG corpus, or provider call was created.
