# EMO-001 Existing-State Audit

COMM-001 already supplied one coarse emotion label, tone, conflict, language,
intent, and multi-turn context. COMM-002 already consumed that context for
bounded response guidance, and GROUP-001 already owned speaker/subject/
addressee state.

| Capability | Existing | Reuse | Extend | New required | Why |
|---|---|---|---|---|---|
| Emotion signal | COMM-001 `emotion` | Yes | Yes | Structured EMO context | Multi-emotion and confidence are required |
| Interaction need | COMM-001 intent | Yes | Yes | No | Emotional need must remain separate from intent |
| Group emotion | GROUP-001 turn state | Yes | Yes | No | Keep emotion scoped to each speaker |
| Response guidance | COMM-002 / ChatEngine | Yes | Yes | No | ChatEngine remains response owner |
| Language cues | LANG-001 and COMM-001 | Yes | No | No | Use existing English/Hindi/Hinglish signals |

No parallel chatbot, response generator, conversation store, or provider call
was added.
