# COMM-002 Architecture

`USER MESSAGE -> COMM-001 CONTEXT -> COMM-002 PROFILE -> EXISTING CHATENGINE -> RESPONSE`

`engines/ai/chatbot/response_adaptation.py` contains `ResponseAdaptationProfile`, bounded level vocabularies, deterministic policy mapping, explicit style overrides, high-stakes restraint, and repetition signals. `adaptation_guidance()` renders internal guidance; it does not generate a response.

The profile is fallback-safe. If analysis fails, ChatEngine retains its existing neutral context path. No routine provider call is used to choose style. Facts, retrieval trust, prediction uncertainty, and safety remain authoritative above style adaptation.
