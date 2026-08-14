# COMM-001 Architecture

`analyze_conversation(message, history)` remains the single understanding
entrypoint. It returns one `ConversationContext`, serialized through the
existing ChatEngine/API context. `prompt_guidance` supplies compact metadata to
the existing response owner; it does not generate a response.

`message -> language/script -> type scores -> intent/pragmatics -> tone/state -> ChatEngine`

Analysis is deterministic and provider-free. If it raises, ChatEngine uses an
`UNKNOWN` / `VERY_LOW` / `NEUTRAL_ADAPTIVE` context and continues normally.
