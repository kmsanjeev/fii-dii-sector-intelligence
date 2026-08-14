# Architecture

`conversation_intelligence.py` returns a `ConversationContext` contract.
`ChatEngine` computes it before response generation, uses compact prompt
guidance, and retains the context for `/api/chat` diagnostics. The normal
response owner remains ChatEngine. The analyzer does not call a provider and
does not create knowledge, prediction, or empirical records.
