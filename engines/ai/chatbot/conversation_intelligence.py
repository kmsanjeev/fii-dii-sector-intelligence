"""Lightweight conversational and language analysis for VEDA-STD-003.

This module is deliberately deterministic and conservative. It supplies
structured context to the existing ChatEngine; it does not become a second
response generator and does not claim certainty about private intent.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


CONVERSATION_TYPES = (
    "SMALL_TALK", "HEART_TO_HEART", "PILLOW_TALK", "SWEET_TALK", "PEP_TALK",
    "REAL_TALK", "STRAIGHT_TALK", "TRASH_TALK", "DOUBLE_TALK", "SHOP_TALK",
)

DOMAIN_TERMS = {
    "JYOTISHA": ("jyotisha", "jyotish", "kundli", "kundali", "dasha", "lagna", "nakshatra", "varga", "planet"),
    "SOFTWARE": ("code", "coding", "api", "python", "javascript", "bug", "deploy", "software", "repository"),
    "FINANCE": ("market", "stock", "fii", "dii", "portfolio", "share", "finance", "invest", "trading"),
}

_HINDI_MARKERS = (
    "yaar", "hai", "hoon", "kya", "kaise", "meri", "mera", "mujhe", "tum", "aap",
    "nahi", "nahin", "lagta", "mood", "paisa", "panga", "bakwaas", "scene", "suno",
    "batao", "chahiye", "accha", "theek", "kyun", "abhi", "bahut", "full",
)
_COMMON_ENGLISH = {
    "a", "an", "and", "are", "be", "break", "cake", "can", "code", "do", "explain",
    "for", "give", "how", "i", "is", "it", "market", "me", "my", "need", "no", "of",
    "on", "piece", "please", "the", "this", "today", "to", "under", "was", "weather",
    "what", "when", "will", "with", "you", "your",
}
_SLANG = {
    "bakwaas": "dismissive or low-quality; intensity depends on context",
    "yaar": "informal address expressing familiarity or emphasis",
    "jugaad": "improvised practical solution; sometimes mildly critical",
    "scene kya hai": "what is happening or what is the situation",
    "panga": "trouble, conflict, or an unnecessary risk",
    "funda": "basic idea or underlying principle",
    "chill": "relax or remain calm",
    "lit": "exciting or highly enjoyable in current informal usage",
    "ghosted": "someone stopped responding without explanation",
    "salty": "resentful or annoyed, often informally",
}
_IDIOMS = {
    "kick the bucket": "die; ordinarily an idiomatic expression, not a literal request",
    "break the ice": "make an awkward first interaction easier",
    "piece of cake": "easy or straightforward",
    "under the weather": "feeling unwell",
    "meri band baja di": "someone made things very difficult for me",
    "scene kya hai": "what is happening or what is the situation",
    "full paisa vasool": "excellent value or thoroughly worthwhile",
}
_SENSITIVE_SLANG = {"bakwaas", "panga", "trash", "shut up", "idiot", "stupid"}


@dataclass(slots=True)
class ConversationContext:
    language: str = "UNKNOWN"
    code_switching: bool = False
    conversation_type: str = "SHOP_TALK"
    primary_intent: str = "GENERAL"
    secondary_intent: str | None = None
    emotion: str = "neutral"
    tone: str = "neutral"
    formality: str = "NEUTRAL"
    directness: str = "BALANCED"
    relationship_context: str = "unknown"
    humour: str = "UNKNOWN"
    sarcasm: str = "UNKNOWN"
    persuasion: str = "NONE_DETECTED"
    conflict_level: str = "LOW"
    domain: str | None = None
    user_proficiency: str = "UNKNOWN"
    idioms: list[dict[str, str]] = field(default_factory=list)
    phrases: list[str] = field(default_factory=list)
    slang: list[dict[str, str]] = field(default_factory=list)
    pragmatic_interpretation: str = "literal meaning retained; context confidence is limited"
    response_strategy: str = "NEUTRAL_ADAPTIVE"
    expression_level: int = 1
    confidence: str = "LOW"
    understood_not_mirrored: bool = False
    transition_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _lower(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def detect_language(text: str) -> tuple[str, bool]:
    value = str(text or "")
    devanagari = bool(re.search(r"[\u0900-\u097f]", value))
    latin_tokens = re.findall(r"[a-zA-Z']+", value.lower())
    hindi_tokens = sum(token in _HINDI_MARKERS for token in latin_tokens)
    english_tokens = sum(token not in _HINDI_MARKERS for token in latin_tokens)
    if devanagari and english_tokens:
        return "HINGLISH", True
    if devanagari or (hindi_tokens >= 2 and hindi_tokens >= english_tokens):
        return "HI", bool(english_tokens)
    if hindi_tokens >= 2 and english_tokens:
        return "HINGLISH", True
    if english_tokens and any(token in _COMMON_ENGLISH for token in latin_tokens):
        return "EN", False
    return "UNKNOWN", False


def _domain_and_proficiency(text: str) -> tuple[str | None, str]:
    matches = [(domain, sum(term in text for term in terms)) for domain, terms in DOMAIN_TERMS.items()]
    domain, score = max(matches, key=lambda item: item[1])
    if not score:
        return None, "UNKNOWN"
    expert_markers = ("dasha", "nakshatra", "api", "schema", "varga", "derivative", "valuation")
    beginner_markers = ("what is", "meaning", "explain", "how do", "what does")
    if sum(term in text for term in expert_markers) >= 2:
        return domain, "ADVANCED"
    if _has_any(text, beginner_markers):
        return domain, "BEGINNER"
    return domain, "INTERMEDIATE"


def _extract_expressions(text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    idioms = [
        {"expression": expression, "contextual_meaning": meaning, "interpretation": "contextual"}
        for expression, meaning in _IDIOMS.items() if expression in text
    ]
    slang = [
        {"expression": expression, "contextual_meaning": meaning, "usage": "understand_only" if expression in _SENSITIVE_SLANG else "adaptive"}
        for expression, meaning in _SLANG.items() if expression in text
    ]
    return idioms, slang


def analyze_conversation(text: str, history: list[dict[str, Any]] | None = None) -> ConversationContext:
    value = _lower(text)
    language, switching = detect_language(text)
    domain, proficiency = _domain_and_proficiency(value)
    idioms, slang = _extract_expressions(value)
    scores = {kind: 0 for kind in CONVERSATION_TYPES}
    scores["SMALL_TALK"] += int(_has_any(value, ("hi", "hello", "hey", "how are you", "weather", "weekend", "commute", "what's up", "good morning")))
    scores["HEART_TO_HEART"] += 2 * int(_has_any(value, ("feel lonely", "i'm scared", "i am scared", "grief", "forgive", "worried", "heartbroken", "need to talk")))
    scores["PILLOW_TALK"] += 2 * int(_has_any(value, ("miss you", "love you", "sweet dreams", "our future", "cuddle")))
    scores["SWEET_TALK"] += int(_has_any(value, ("you are amazing", "you look great", "please do me a favour", "pretty please", "flatter")))
    scores["PEP_TALK"] += 2 * int(_has_any(value, ("motivate me", "pep talk", "i can do this", "encourage me", "give up")))
    scores["REAL_TALK"] += 2 * int(_has_any(value, ("real talk", "be honest", "reality check", "uncomfortable truth", "tell me straight")))
    scores["STRAIGHT_TALK"] += 2 * int(_has_any(value, ("straight answer", "just tell me", "no fluff", "be direct", "bottom line")))
    scores["TRASH_TALK"] += int(_has_any(value, ("trash talk", "you can't beat", "bring it on", "loser", "noob")))
    scores["DOUBLE_TALK"] += 2 * int(_has_any(value, ("revisit the strategic opportunity", "at the appropriate time", "circle back", "moving forward", "we will consider")))
    scores["SHOP_TALK"] += 2 * int(domain is not None)
    history_type = None
    if history:
        prior = analyze_conversation(str(history[-1].get("content") or ""))
        history_type = prior.conversation_type
        if prior.conversation_type == "SMALL_TALK" and scores["HEART_TO_HEART"]:
            scores["HEART_TO_HEART"] += 1
    conversation_type = max(scores, key=scores.get)
    if max(scores.values()) == 0:
        conversation_type = "UNKNOWN"
    emotion = "neutral"
    if _has_any(value, ("happy", "excited", "love", "great")):
        emotion = "happy"
    elif _has_any(value, ("sad", "lonely", "grief", "worried", "scared")):
        emotion = "vulnerable"
    elif _has_any(value, ("angry", "annoyed", "fed up", "bakwaas", "panga")):
        emotion = "frustrated"
    sarcasm = "LIKELY_SARCASM" if ("yeah right" in value or "great, just great" in value) else "UNKNOWN"
    tone = "playful" if conversation_type == "TRASH_TALK" else "supportive" if conversation_type in {"HEART_TO_HEART", "PEP_TALK", "PILLOW_TALK"} else "direct" if conversation_type in {"REAL_TALK", "STRAIGHT_TALK"} else "professional" if conversation_type == "SHOP_TALK" else "neutral"
    formality = "VERY_INFORMAL" if language == "HINGLISH" or _has_any(value, ("yaar", "dude", "bro")) else "NEUTRAL"
    directness = "VERY_DIRECT" if conversation_type in {"REAL_TALK", "STRAIGHT_TALK"} else "SOFT" if conversation_type in {"SWEET_TALK", "PILLOW_TALK"} else "BALANCED"
    strategy = {
        "SMALL_TALK": "LIGHT_SOCIAL", "HEART_TO_HEART": "SUPPORTIVE", "PILLOW_TALK": "WARM_PRIVATE",
        "SWEET_TALK": "WARM_BOUNDARIED", "PEP_TALK": "MOTIVATIONAL", "REAL_TALK": "DIRECT_FACTUAL",
        "STRAIGHT_TALK": "CONCISE", "TRASH_TALK": "PLAYFUL_DE_ESCALATING", "DOUBLE_TALK": "CLARIFYING",
        "SHOP_TALK": "PROFESSIONAL", "UNKNOWN": "NEUTRAL_ADAPTIVE",
    }[conversation_type]
    return ConversationContext(
        language=language, code_switching=switching, conversation_type=conversation_type,
        primary_intent="SOCIAL" if conversation_type not in {"SHOP_TALK", "UNKNOWN"} else "DOMAIN_QUERY" if conversation_type == "SHOP_TALK" else "GENERAL",
        emotion=emotion, tone=tone, formality=formality, directness=directness,
        relationship_context="close_or_familiar" if conversation_type in {"PILLOW_TALK", "SWEET_TALK"} else "unknown",
        humour="POSSIBLE_PLAYFULNESS" if conversation_type == "TRASH_TALK" else "UNKNOWN",
        sarcasm=sarcasm, domain=domain, user_proficiency=proficiency, idioms=idioms, slang=slang,
        phrases=[item["expression"] for item in idioms],
        pragmatic_interpretation="literal and contextual readings retained; no private intent asserted",
        response_strategy=strategy, expression_level=2 if language == "HINGLISH" else 1,
        confidence="MODERATE" if max(scores.values()) >= 2 else "LOW",
        understood_not_mirrored=bool(slang), transition_from=history_type if history_type and history_type != conversation_type else None,
    )


def prompt_guidance(context: ConversationContext) -> str:
    """Return compact instructions for the existing response owner."""
    slang_rule = "Understand slang semantically; do not mirror hostile/offensive wording." if context.understood_not_mirrored else "Use natural language; do not force idioms or slang."
    return (
        "\n\nCONVERSATIONAL CONTEXT (inferred, not fact):\n"
        f"language={context.language}; code_switching={context.code_switching}; type={context.conversation_type}; "
        f"tone={context.tone}; formality={context.formality}; directness={context.directness}; "
        f"strategy={context.response_strategy}; domain={context.domain or 'unknown'}; proficiency={context.user_proficiency}.\n"
        f"Use a {context.response_strategy.lower().replace('_', ' ')} response. {slang_rule} "
        "Preserve safety, factual boundaries, and uncertainty."
    )


__all__ = ["CONVERSATION_TYPES", "ConversationContext", "analyze_conversation", "detect_language", "prompt_guidance"]
