# Runtime Integration

Normal ChatEngine remains the response owner. The context is additive and
backward-compatible in `/api/chat`. Small talk skips RAG retrieval; other
queries retain existing retrieval, research, orchestration, prediction, and
safety behavior. Conversational analysis is deterministic and adds no
provider calls.
