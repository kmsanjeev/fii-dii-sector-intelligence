# Existing-State Audit

| Area | Existing implementation | STD-003 action |
|---|---|---|
| Response owner | `engines/ai/chatbot/chat_engine.py` | Reused and extended |
| Intent routing | `intent_router.py` | Preserved; conversational context is additive |
| Session history | ChatEngine bounded history and chat history service | Reused for multi-turn context |
| Orchestration | `AgentOrchestrator` shadow trace | Preserved |
| RAG/research | Existing unified/legacy retrieval | Small talk avoids unnecessary retrieval |
| Safety | Existing safety and disclaimer deduplication | Preserved |
| Frontend/API | Existing ChatPage and `/api/chat` | Response diagnostic field added compatibly |

No existing universal conversational analyzer or language-pack store was
found. The new deterministic analyzer is the demonstrated execution gap.
