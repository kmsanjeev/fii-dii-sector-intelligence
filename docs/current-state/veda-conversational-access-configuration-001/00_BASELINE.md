# VEDA-CONVERSATIONAL-ACCESS-CONFIGURATION-001 — Baseline

Starting commit: `8daae8a0c5bd21a6b2867b341d8551f0526c4940` on `main`.
Tracked tree was clean; ignored runtime data was preserved.

The defect was reproducible in `engines/ai/chatbot/intent_router.py`: every
unmatched message returned `RESEARCH` at confidence `0.3`. `get_system_prompt`
then supplied a market identity and research framing. `_is_greeting` also used
substring matching, so words such as `this` could be mistaken for `hi`.

The existing compliance addendum contains safety, privacy, prompt-injection,
copyright and high-stakes rules. No market-only prohibition was found in local
Claude memory or the addendum. The broad restriction was an application routing,
prompt and UI problem.
