"""
Chatbot Safety -- output-side reply classification.

The compliance addendum (intent_router.py's _COMPLIANCE_ADDENDUM) guides
the LLM's INPUT side -- what it should and shouldn't do. This module
checks the OUTPUT side, after a reply comes back, for two distinct
things:

  1. REFUSED   -- the model declined the request. Not something to hide
                  or replace (the refusal text itself is the correct,
                  safe thing to show the user) -- just worth flagging
                  for audit visibility, since nothing currently
                  distinguishes a refused turn from a normal one in
                  conversation_log.csv.
  2. PROMPT_LEAK -- the reply echoes back fragments of Veda's own system
                  prompt (e.g. a jailbreak attempt tricked a weaker
                  fallback provider into repeating its instructions).
                  This IS something to replace before it reaches the
                  user -- unlike a refusal, a leaked system prompt is an
                  information-disclosure problem regardless of framing.

Deliberately pattern-based (not a second LLM call) -- cheap, synchronous,
provider-agnostic across the 7-provider fallback chain.
"""

from __future__ import annotations
import re

REFUSAL_PATTERNS = [
    r"\bi can'?t assist\b",
    r"\bi cannot assist\b",
    r"\bi can'?t help with\b",
    r"\bi cannot help with\b",
    r"\bi'?m not able to\b",
    r"\bi won'?t (provide|help|assist)\b",
    r"\bi (can'?t|cannot) comply\b",
    r"\bagainst (my|the) guidelines\b",
    r"\bi (must|have to) decline\b",
    r"\bi'?m unable to (provide|help|assist)\b",
]
_REFUSAL_RE = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)

# Fragments unique enough to Veda's own system prompt that they should
# never legitimately appear in a normal reply to the user. Kept short and
# distinctive on purpose -- long enough to not false-positive on ordinary
# finance/astrology conversation, short enough to survive minor paraphrasing.
_LEAK_MARKERS = [
    "COMPLIANCE & SAFETY",
    "You are the Capital Flow Intelligence Assistant",
    "You are Veda, a warm and friendly voice assistant",
    "GENDER (Hindi/Hinglish)",
    "VOICE MODE -- you are Veda, speaking out loud",
    "ALWAYS call generate_personal_kundli()",
    "Never speculate beyond what the data shows",
]
_LEAK_RE = re.compile("|".join(re.escape(m) for m in _LEAK_MARKERS), re.IGNORECASE)

SAFE_FALLBACK_REPLY = (
    "I ran into an issue putting that response together -- could you "
    "rephrase your question? I'm happy to help with market, sector, "
    "stock, corporate, or astrology questions."
)


def classify_reply(reply: str) -> dict:
    """
    Returns {"flagged": bool, "reason": "refused" | "prompt_leak" | None}.
    Checked in this order: a leak is worse than a refusal, so if a reply
    somehow trips both (unlikely), prompt_leak wins.
    """
    if not reply:
        return {"flagged": False, "reason": None}

    if _LEAK_RE.search(reply):
        return {"flagged": True, "reason": "prompt_leak"}

    if _REFUSAL_RE.search(reply):
        return {"flagged": True, "reason": "refused"}

    return {"flagged": False, "reason": None}


def sanitize_reply(reply: str) -> tuple[str, dict]:
    """
    Classify the reply and, ONLY for a prompt_leak, replace it with
    SAFE_FALLBACK_REPLY before it reaches the user. A "refused" reply is
    left exactly as-is -- refusing is the correct, safe behavior, there
    is nothing to sanitize.

    Returns (possibly-replaced reply, classification dict).
    """
    result = classify_reply(reply)
    if result["reason"] == "prompt_leak":
        return SAFE_FALLBACK_REPLY, result
    return reply, result
