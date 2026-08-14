# VEDA-STD-003 Universal Conversational Intelligence Standard

Status: IMPLEMENTED / FROZEN

STD-003 extends the existing VEDA ChatEngine with conservative, structured
conversation and language context. It does not create a second chatbot,
replace the response owner, alter prediction infrastructure, or weaken
STD-001 trust and safety controls.

Inherited standards: STD-001, STD-002, and RM-001. Compatibility with
PRED-001 through PRED-003, EMP-001, and ADM-EMP-001 is preserved.

## Principles

- Understand more expressions than VEDA automatically uses.
- Keep literal meaning separate from possible pragmatic meaning.
- Treat emotion, sarcasm, persuasion, and relationship context as uncertain
  interpretations rather than facts.
- Adapt tone and explanation depth without weakening factual or high-stakes
  boundaries.
- Do not force idioms or mirror hostile slang.
- Keep the current ChatEngine as the sole normal response owner.
- Use lightweight analysis first; fall back to neutral adaptive behavior when
  confidence is low.

## V1 Scope

Conversation types: SMALL_TALK, HEART_TO_HEART, PILLOW_TALK, SWEET_TALK,
PEP_TALK, REAL_TALK, STRAIGHT_TALK, TRASH_TALK, DOUBLE_TALK, and SHOP_TALK.

Wave-1 languages: English, Hindi, Romanized Hindi, Devanagari Hindi, and
Hinglish code switching. Additional language packs remain planned.

## Runtime

`engines/ai/chatbot/conversation_intelligence.py` produces a structured
context and compact prompt guidance. `ChatEngine` consumes it; `/api/chat`
returns the context for diagnostics. Normal users do not see diagnostic
metadata by default.

## Governance

Unknown expressions follow the STD-001 source, validation, candidate, and
approval lifecycle. Language candidates may be available for understanding
before active usage is approved. STD-003 does not promote knowledge to
Approved Core automatically.
