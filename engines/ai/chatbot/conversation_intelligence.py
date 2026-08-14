"""Deterministic conversational context for the existing VEDA ChatEngine.

COMM-001 extends the STD-003 analyzer in place.  It classifies conservatively,
keeps literal and pragmatic readings separate, and never generates replies.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


CONVERSATION_TYPES = (
    "SMALL_TALK", "HEART_TO_HEART", "PILLOW_TALK", "SWEET_TALK", "PEP_TALK",
    "REAL_TALK", "STRAIGHT_TALK", "TRASH_TALK", "DOUBLE_TALK", "SHOP_TALK",
)
SUPPORTED_CONVERSATION_TYPES = CONVERSATION_TYPES + ("UNKNOWN", "MIXED", "TRANSITIONING")
INTENTS = (
    "ASK_INFORMATION", "ASK_ADVICE", "REQUEST_ACTION", "REQUEST_EXPLANATION",
    "SEEK_REASSURANCE", "SEEK_VALIDATION", "VENT", "SHARE_EXPERIENCE",
    "SOCIAL_BONDING", "PERSUADE", "NEGOTIATE", "CHALLENGE", "DISAGREE",
    "CORRECT", "JOKE", "TEASE", "REFLECT", "EXPLORE", "BRAINSTORM",
    "DECIDE", "LEARN", "UNKNOWN",
)

DOMAIN_TERMS = {
    "JYOTISHA": ("jyotisha", "jyotish", "kundli", "kundali", "dasha", "lagna", "nakshatra", "varga", "planet"),
    "SOFTWARE": ("code", "coding", "api", "python", "javascript", "bug", "deploy", "software", "repository", "server"),
    "FINANCE": ("market", "stock", "fii", "dii", "portfolio", "share", "finance", "invest", "trading"),
    "BUSINESS": ("business", "strategy", "customer", "revenue", "sales", "company", "management"),
    "RESEARCH": ("research", "study", "paper", "evidence", "method", "source", "hypothesis"),
}
_HINDI_MARKERS = (
    "yaar", "hai", "hoon", "kya", "kaise", "meri", "mera", "mujhe", "tum", "aap",
    "nahi", "nahin", "lagta", "mood", "paisa", "panga", "bakwaas", "scene", "suno",
    "batao", "chahiye", "accha", "theek", "kyun", "abhi", "bahut", "full", "band",
)
_COMMON_ENGLISH = {"a", "an", "and", "are", "be", "break", "cake", "can", "code", "do", "explain", "for", "give", "how", "i", "is", "it", "market", "me", "my", "need", "no", "of", "on", "piece", "please", "the", "this", "today", "to", "under", "was", "weather", "what", "when", "will", "with", "you", "your"}
_SLANG = {
    "bakwaas": "dismissive or low-quality; intensity depends on context", "yaar": "informal address expressing familiarity or emphasis",
    "jugaad": "improvised practical solution; sometimes mildly critical", "scene kya hai": "what is happening or what is the situation",
    "panga": "trouble, conflict, or an unnecessary risk", "funda": "basic idea or underlying principle", "chill": "relax or remain calm",
    "lit": "exciting or highly enjoyable in current informal usage", "ghosted": "someone stopped responding without explanation", "salty": "resentful or annoyed, often informally",
}
_IDIOMS = {
    "kick the bucket": "die; ordinarily an idiomatic expression, not a literal request", "break the ice": "make an awkward first interaction easier",
    "piece of cake": "easy or straightforward", "under the weather": "feeling unwell", "meri band baja di": "someone made things very difficult for me",
    "scene kya hai": "what is happening or what is the situation", "full paisa vasool": "excellent value or thoroughly worthwhile",
}
_SENSITIVE_SLANG = {"bakwaas", "panga", "trash", "shut up", "idiot", "stupid"}


@dataclass(slots=True)
class ConversationContext:
    language: str = "UNKNOWN"
    script: str = "UNKNOWN"
    code_switching: bool = False
    conversation_type: str = "UNKNOWN"
    conversation_type_confidence: str = "LOW"
    secondary_types: list[str] = field(default_factory=list)
    primary_intent: str = "UNKNOWN"
    secondary_intent: str | None = None
    secondary_intents: list[str] = field(default_factory=list)
    emotion: str = "NEUTRAL"
    tone: str = "NEUTRAL"
    formality: str = "NEUTRAL"
    directness: str = "BALANCED"
    relationship_context: str = "UNKNOWN"
    humour: str = "NONE"
    sarcasm: str = "NONE"
    persuasion: str = "NONE_DETECTED"
    conflict_level: str = "NONE"
    domain: str | None = None
    user_proficiency: str = "UNKNOWN"
    idioms: list[dict[str, str]] = field(default_factory=list)
    phrases: list[str] = field(default_factory=list)
    slang: list[dict[str, str]] = field(default_factory=list)
    literal_meaning: str = ""
    likely_pragmatic_meaning: str = ""
    alternative_interpretation: str | None = None
    pragmatic_interpretation: str = "literal meaning retained; context confidence is limited"
    ambiguity_state: str = "CLEAR"
    response_strategy: str = "NEUTRAL_ADAPTIVE"
    expression_level: int = 1
    confidence: str = "LOW"
    transition_confidence: str = "LOW"
    transition_from: str | None = None
    state_stable: bool = True
    evidence: list[str] = field(default_factory=list)
    understood_not_mirrored: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _lower(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def detect_script(text: str) -> str:
    value = str(text or "")
    devanagari = bool(re.search(r"[\u0900-\u097f]", value))
    latin = bool(re.search(r"[a-zA-Z]", value))
    if devanagari and latin:
        return "MIXED"
    if devanagari:
        return "DEVANAGARI"
    if latin:
        return "LATIN"
    return "UNKNOWN"


def detect_language(text: str) -> tuple[str, bool]:
    value = str(text or "")
    devanagari = bool(re.search(r"[\u0900-\u097f]", value))
    tokens = re.findall(r"[a-zA-Z']+", value.lower())
    hindi = sum(token in _HINDI_MARKERS for token in tokens)
    english = sum(token not in _HINDI_MARKERS for token in tokens)
    if devanagari and english:
        return "HINGLISH", True
    if devanagari or (hindi >= 2 and hindi >= english):
        return "HI", bool(english)
    if hindi >= 2 and english:
        return "HINGLISH", True
    if english and any(token in _COMMON_ENGLISH for token in tokens):
        return "EN", False
    return "UNKNOWN", False


def _domain_and_proficiency(text: str) -> tuple[str | None, str]:
    matches = [(domain, sum(term in text for term in terms)) for domain, terms in DOMAIN_TERMS.items()]
    domain, score = max(matches, key=lambda item: item[1])
    if not score:
        return None, "UNKNOWN"
    expert = ("dasha", "nakshatra", "api", "schema", "varga", "derivative", "valuation", "hypothesis")
    if sum(term in text for term in expert) >= 2:
        return domain, "ADVANCED"
    if _has_any(text, ("what is", "meaning", "explain", "how do", "what does")):
        return domain, "BEGINNER"
    return domain, "INTERMEDIATE"


def _extract_expressions(text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    idioms = [{"expression": expression, "contextual_meaning": meaning, "interpretation": "contextual"} for expression, meaning in _IDIOMS.items() if expression in text]
    slang = [{"expression": expression, "contextual_meaning": meaning, "usage": "understand_only" if expression in _SENSITIVE_SLANG else "adaptive"} for expression, meaning in _SLANG.items() if expression in text]
    return idioms, slang


def _history_messages(history: list[dict[str, Any]] | None) -> list[str]:
    return [str(item.get("content") or "") for item in (history or []) if item.get("role") == "user"][-3:]


def _intent(value: str, kind: str) -> tuple[str, list[str]]:
    if _has_any(value, ("what is", "what does", "how does", "tell me about")):
        return "ASK_INFORMATION", ["LEARN"]
    if _has_any(value, ("explain", "why does", "how do i")):
        return "REQUEST_EXPLANATION", ["LEARN"]
    if _has_any(value, ("should i", "what should", "advice", "recommend")):
        return "ASK_ADVICE", ["DECIDE"]
    if _has_any(value, ("motivate me", "pep talk", "encourage", "give up")):
        return "SEEK_REASSURANCE", ["REFLECT"]
    if _has_any(value, ("feel lonely", "worried", "scared", "need to talk", "fed up")):
        return "VENT", ["SEEK_REASSURANCE"]
    if _has_any(value, ("be honest", "real talk", "reality check", "straight answer", "no fluff")):
        return "CHALLENGE", ["ASK_ADVICE"]
    if _has_any(value, ("please", "favour", "persuade", "convince")):
        return "PERSUADE", []
    if _has_any(value, ("thanks", "thank you", "hello", "hi", "how are you")):
        return "SOCIAL_BONDING", []
    if kind == "SHOP_TALK":
        return "ASK_INFORMATION", []
    if kind == "TRASH_TALK":
        return ("TEASE" if _has_any(value, ("noob", "loser", "can't beat", "bring it on")) else "CHALLENGE"), []
    return "UNKNOWN", []


def analyze_conversation(text: str, history: list[dict[str, Any]] | None = None) -> ConversationContext:
    value = _lower(text)
    language, switching = detect_language(text)
    script = detect_script(text)
    domain, proficiency = _domain_and_proficiency(value)
    idioms, slang = _extract_expressions(value)
    scores = {kind: 0 for kind in CONVERSATION_TYPES}
    markers = {
        "SMALL_TALK": ("hello", "hey", "how are you", "kaise hain", "weather", "weekend", "commute", "what's up", "good morning"),
        "HEART_TO_HEART": ("feel lonely", "i'm scared", "i am scared", "grief", "forgive", "worried", "heartbroken", "need to talk", "personal", "mood off", "darr lag"),
        "PILLOW_TALK": ("miss you", "love you", "sweet dreams", "our future", "cuddle", "yaad aa rahi"),
        "SWEET_TALK": ("you are amazing", "you look great", "please do me a favour", "pretty please", "flatter", "bahut acche", "madad karo"),
        "PEP_TALK": ("motivate me", "motivate karo", "pep talk", "i can do this", "encourage me", "give up", "you've got this", "keep going", "thoda encourage"),
        "REAL_TALK": ("real talk", "be honest", "reality check", "uncomfortable truth", "tell me straight", "sach sach", "candid assessment"),
        "STRAIGHT_TALK": ("straight answer", "just tell me", "no fluff", "be direct", "bottom line", "seedha batao"),
        "TRASH_TALK": ("trash talk", "you can't beat", "bring it on", "loser", "noob", "your move"),
        "DOUBLE_TALK": ("revisit the strategic opportunity", "at the appropriate time", "circle back", "moving forward", "we will consider", "baad mein consider"),
    }
    for kind, terms in markers.items():
        scores[kind] += 2 * int(_has_any(value, terms))
    scores["SHOP_TALK"] = 2 * int(domain is not None)
    if _has_any(value, ("great", "crash", "another server crash", "yeah right")) and _has_any(value, ("crash", "yeah right", "just great")):
        scores["REAL_TALK"] += 1
    prior_types = []
    for message in _history_messages(history):
        prior = analyze_conversation(message)
        if prior.conversation_type not in {"UNKNOWN", "MIXED"}:
            prior_types.append(prior.conversation_type)
    previous = prior_types[-1] if prior_types else None
    short_follow_up = value in {"ok", "okay", "yes", "haan", "hmm", "tell me more", "go on", "fine"}
    if short_follow_up and previous:
        scores[previous] = max(scores.values(), default=0) + 2
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_score = ranked[0][1]
    if not top_score:
        primary = "UNKNOWN"
        secondary = []
        confidence = "LOW"
    else:
        primary = ranked[0][0]
        secondary = [name for name, score in ranked[1:] if score and score >= top_score - 1][:2]
        confidence = "VERY_HIGH" if top_score >= 4 and not secondary else "HIGH" if top_score >= 2 else "MODERATE"
        if secondary and abs(top_score - ranked[1][1]) <= 1 and ranked[0][0] not in {"SHOP_TALK", "STRAIGHT_TALK", "REAL_TALK"}:
            primary = "MIXED"
    transition_from = previous if previous and previous != primary and primary not in {"UNKNOWN", "MIXED"} else None
    transition_confidence = "HIGH" if transition_from else "LOW"
    if transition_from and not short_follow_up:
        # Preserve the concrete current type for legacy callers; the explicit
        # transition fields expose the state change without breaking routing.
        secondary = [ranked[0][0]] if ranked[0][0] != primary else secondary
    kind_for_intent = secondary[0] if primary == "TRANSITIONING" and secondary else (primary if primary in CONVERSATION_TYPES else (previous or "UNKNOWN"))
    primary_intent, secondary_intents = _intent(value, kind_for_intent)
    literal = value or "empty user message"
    pragmatic = "literal meaning retained; no private intent asserted"
    alternative = None
    ambiguity = "CLEAR"
    if value.rstrip(".!?") in {"i'm fine", "im fine", "i am fine", "fine"}:
        pragmatic = "possible conversation closure, reluctance, or mild frustration"
        alternative = "literal report of being fine"
        ambiguity = "AMBIGUOUS"
    elif primary_intent == "UNKNOWN":
        ambiguity = "SLIGHTLY_AMBIGUOUS" if primary == "UNKNOWN" else "CLEAR"
    if "revisit the strategic opportunity" in value or "appropriate time" in value:
        literal = "future consideration"
        pragmatic = "possible non-commitment or deferral"
        alternative = "genuine future scheduling"
        ambiguity = "SLIGHTLY_AMBIGUOUS"
    sarcasm = "NONE"
    if _has_any(value, ("yeah right", "great, just great")) or ("crash" in value and "great" in value):
        sarcasm = "LIKELY"
    elif _has_any(value, ("sure", "great")) and _has_any(value, ("another", "fine", "really")):
        sarcasm = "POSSIBLE"
    humour = "LIKELY" if kind_for_intent == "TRASH_TALK" else "POSSIBLE" if _has_any(value, ("lol", "haha", "joke", "funny")) else "NONE"
    tone = "PLAYFUL" if kind_for_intent == "TRASH_TALK" else "WARM" if kind_for_intent in {"HEART_TO_HEART", "PEP_TALK", "PILLOW_TALK"} else "SERIOUS" if kind_for_intent in {"REAL_TALK", "STRAIGHT_TALK"} else "PROFESSIONAL" if kind_for_intent == "SHOP_TALK" else "NEUTRAL"
    emotion = "VULNERABLE" if _has_any(value, ("sad", "lonely", "grief", "worried", "scared")) else "FRUSTRATED" if _has_any(value, ("angry", "annoyed", "fed up", "bakwaas", "panga", "crash")) else "EXCITED" if _has_any(value, ("happy", "excited", "love", "great")) else "NEUTRAL"
    formality = "VERY_INFORMAL" if language == "HINGLISH" or _has_any(value, ("yaar", "dude", "bro")) else "NEUTRAL"
    directness = "VERY_DIRECT" if kind_for_intent in {"REAL_TALK", "STRAIGHT_TALK"} else "SOFT" if kind_for_intent in {"SWEET_TALK", "PILLOW_TALK"} else "BALANCED"
    conflict = "RISING" if _has_any(value, ("angry", "fed up", "shut up", "idiot")) else "LOW" if kind_for_intent == "TRASH_TALK" else "NONE"
    strategy = {
        "SMALL_TALK": "LIGHT_SOCIAL", "HEART_TO_HEART": "SUPPORTIVE", "PILLOW_TALK": "WARM_PRIVATE", "SWEET_TALK": "WARM_BOUNDED",
        "PEP_TALK": "MOTIVATIONAL", "REAL_TALK": "CANDID_BALANCED", "STRAIGHT_TALK": "CONCISE", "TRASH_TALK": "PLAYFUL_DE_ESCALATING",
        "DOUBLE_TALK": "CLARIFYING", "SHOP_TALK": "PROFESSIONAL", "UNKNOWN": "NEUTRAL_ADAPTIVE", "MIXED": "CONTEXTUAL", "TRANSITIONING": "CONTEXTUAL",
    }[primary]
    evidence = [f"type_marker:{name}" for name, score in ranked[:3] if score] + ([f"domain:{domain}"] if domain else [])
    return ConversationContext(
        language=language, script=script, code_switching=switching, conversation_type=primary,
        conversation_type_confidence=confidence, secondary_types=secondary, primary_intent=primary_intent,
        secondary_intent=secondary_intents[0] if secondary_intents else None, secondary_intents=secondary_intents,
        emotion=emotion, tone=tone, formality=formality, directness=directness,
        relationship_context="close_or_familiar" if kind_for_intent in {"PILLOW_TALK", "SWEET_TALK"} else "UNKNOWN",
        humour=humour, sarcasm=sarcasm, persuasion="POSSIBLE" if primary_intent == "PERSUADE" else "NONE_DETECTED",
        conflict_level=conflict, domain=domain, user_proficiency=proficiency, idioms=idioms, slang=slang,
        phrases=[item["expression"] for item in idioms], literal_meaning=literal, likely_pragmatic_meaning=pragmatic,
        alternative_interpretation=alternative, pragmatic_interpretation=pragmatic, ambiguity_state=ambiguity,
        response_strategy=strategy, expression_level=2 if language == "HINGLISH" else 1, confidence=confidence,
        transition_confidence=transition_confidence, transition_from=transition_from, state_stable=not bool(transition_from) or short_follow_up,
        evidence=evidence, understood_not_mirrored=bool(slang),
    )


def prompt_guidance(context: ConversationContext) -> str:
    slang_rule = "Understand slang semantically; do not mirror hostile/offensive wording." if context.understood_not_mirrored else "Use natural language; do not force idioms or slang."
    return (
        "\n\nCONVERSATIONAL CONTEXT (inferred, not fact):\n"
        f"language={context.language}; type={context.conversation_type}; intent={context.primary_intent}; tone={context.tone}; "
        f"formality={context.formality}; directness={context.directness}; strategy={context.response_strategy}; "
        f"domain={context.domain or 'unknown'}; proficiency={context.user_proficiency}; ambiguity={context.ambiguity_state}.\n"
        f"Use a {context.response_strategy.lower().replace('_', ' ')} response. {slang_rule} Preserve safety, factual boundaries, and uncertainty."
    )


__all__ = ["CONVERSATION_TYPES", "SUPPORTED_CONVERSATION_TYPES", "INTENTS", "ConversationContext", "analyze_conversation", "detect_language", "detect_script", "prompt_guidance"]
