"""Deterministic response adaptation for the existing VEDA ChatEngine.

This module only builds bounded style guidance. ChatEngine remains the sole
response generator and all safety, factual, retrieval, and prediction rules
remain authoritative elsewhere.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


LEVELS = {
    "depth": ("MINIMAL", "CONCISE", "STANDARD", "DETAILED", "DEEP"),
    "formality": ("VERY_FORMAL", "FORMAL", "NEUTRAL", "INFORMAL", "VERY_INFORMAL"),
    "directness": ("INDIRECT", "SOFT", "BALANCED", "DIRECT", "VERY_DIRECT"),
    "technicality": ("PLAIN", "LIGHT_TECHNICAL", "TECHNICAL", "ADVANCED", "EXPERT"),
    "warmth": ("LOW", "MODERATE", "HIGH"),
    "reassurance": ("NONE", "LIGHT", "MODERATE"),
    "playfulness": ("NONE", "LIGHT", "MODERATE"),
    "idiom_usage": ("NONE", "SPARSE", "NATURAL", "EXPRESSIVE"),
    "slang_usage": ("NONE", "LIGHT", "CONTEXTUAL"),
    "jargon_usage": ("NONE", "LIGHT", "APPROPRIATE", "DENSE"),
}


@dataclass(frozen=True, slots=True)
class ResponseAdaptationProfile:
    conversation_type: str = "UNKNOWN"
    primary_intent: str = "UNKNOWN"
    secondary_intents: tuple[str, ...] = ()
    tone: str = "NEUTRAL"
    emotion: str = "NEUTRAL"
    formality: str = "NEUTRAL"
    directness: str = "BALANCED"
    domain: str | None = None
    domain_proficiency: str = "UNKNOWN"
    language: str = "UNKNOWN"
    script: str = "UNKNOWN"
    code_switching: bool = False
    expression_level: int = 1
    response_strategy: str = "NEUTRAL_ADAPTIVE"
    response_depth: str = "STANDARD"
    response_length_preference: str = "STANDARD"
    structure_preference: str = "PLAIN_PARAGRAPH"
    warmth_level: str = "MODERATE"
    technicality_level: str = "PLAIN"
    explanation_level: str = "NORMAL"
    challenge_level: str = "LOW"
    reassurance_level: str = "NONE"
    playfulness_level: str = "NONE"
    idiom_usage_level: str = "SPARSE"
    slang_usage_level: str = "NONE"
    jargon_usage_level: str = "NONE"
    clarification_need: str = "NONE"
    ambiguity_state: str = "CLEAR"
    high_stakes_state: str = "NONE"
    repetition_avoidance: str = "STANDARD"
    continuity_state: str = "NEW_TURN"
    explicit_overrides: tuple[str, ...] = ()
    repeated_openings: tuple[str, ...] = ()
    repeated_closings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _text(context: Any) -> str:
    return str(getattr(context, "_source_text", "") or "")


def _history_items(history: Iterable[dict[str, Any]] | None, role: str) -> list[str]:
    return [str(item.get("content") or "") for item in (history or []) if item.get("role") == role]


def _explicit_overrides(text: str) -> set[str]:
    value = text.casefold()
    found: set[str] = set()
    if re.search(r"\b(be brief|keep it brief|short answer|in one line|concise)\b", value):
        found.add("BRIEF")
    if re.search(r"\b(explain deeply|go deep|detailed explanation|step by step)\b", value):
        found.add("DEEP")
    if re.search(r"\b(talk casually|be casual|informal|casual tone)\b", value):
        found.add("CASUAL")
    if re.search(r"\b(use hindi|answer in hindi|hindi mein)\b", value):
        found.add("HINDI")
    if re.search(r"\b(be direct|brief and direct|straight answer|no fluff|seedha batao)\b", value):
        found.add("DIRECT")
    if re.search(r"\b(explain like a beginner|teach me|assume i am new)\b", value):
        found.add("TEACHING")
    return found


def _text_domain(text: str) -> str | None:
    value = text.casefold()
    terms = {
        "JYOTISHA": ("jyotisha", "jyotish", "dasha", "nakshatra", "varga", "d9", "d10", "kundli", "chart"),
        "SOFTWARE": ("software", "api", "race condition", "schema", "server", "debug", "migration", "idempotency"),
        "FINANCE": ("finance", "portfolio", "investment", "market", "drawdown", "liquidity", "risk-on", "risk off", "alpha", "beta"),
        "BUSINESS": ("business", "strategy", "revenue", "customer", "management"),
    }
    scores = {domain: sum(term in value for term in domain_terms) for domain, domain_terms in terms.items()}
    domain, score = max(scores.items(), key=lambda item: item[1])
    return domain if score else None


def _strong_type(text: str) -> str | None:
    value = text.casefold()
    if re.search(r"\b(look great|pretty please|do me a favour|do me a favor)\b", value):
        return "SWEET_TALK"
    if re.search(r"\b(noob|loser|your move|bring it on|cannot beat me)\b", value):
        return "TRASH_TALK"
    if re.search(r"\b(reality check|uncomfortable truth|be honest about|tell me the truth)\b", value):
        return "REAL_TALK"
    if re.search(r"\b(straight answer|no fluff|bottom line|seedha batao)\b", value):
        return "STRAIGHT_TALK"
    return None


def _openings(history: Iterable[dict[str, Any]] | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    replies = _history_items(history, "assistant")
    openings = [re.sub(r"\s+", " ", item.strip()).split(" ", 4)[0:4] for item in replies]
    opening_keys = [" ".join(words).casefold() for words in openings if words]
    repeated_openings = tuple(sorted({key for key in opening_keys if opening_keys.count(key) > 1}))
    endings = [re.sub(r"\s+", " ", item.strip()).split(" ")[-4:] for item in replies]
    ending_keys = [" ".join(words).casefold() for words in endings if words]
    repeated_closings = tuple(sorted({key for key in ending_keys if ending_keys.count(key) > 1}))
    return repeated_openings, repeated_closings


def build_adaptation_profile(context: Any, *, user_message: str = "", history: list[dict[str, Any]] | None = None) -> ResponseAdaptationProfile:
    """Build a bounded profile from COMM-001 context and explicit user asks."""
    kind = str(getattr(context, "conversation_type", "UNKNOWN"))
    kind = _strong_type(user_message) or kind
    intent = str(getattr(context, "primary_intent", "UNKNOWN"))
    domain = getattr(context, "domain", None) or _text_domain(user_message)
    proficiency = str(getattr(context, "user_proficiency", "UNKNOWN"))
    if kind == "UNKNOWN" and domain:
        kind = "SHOP_TALK"
    explicit = _explicit_overrides(user_message)
    high_stakes = "HEALTH" if re.search(r"\b(health|symptom|medical|fertility|longevity)\b", user_message.casefold()) else "FINANCE" if re.search(r"\b(lost money|money loss|financial loss|market loss|investment loss|portfolio loss)\b", user_message.casefold()) else "NONE"

    policy = {
        "SMALL_TALK": dict(depth="MINIMAL", length="SHORT", formality="INFORMAL", warmth="HIGH", playful="LIGHT", strategy="LIGHT_SOCIAL"),
        "HEART_TO_HEART": dict(depth="STANDARD", length="PACED", directness="SOFT", warmth="HIGH", reassurance="LIGHT", strategy="SUPPORTIVE"),
        "PILLOW_TALK": dict(depth="STANDARD", length="PACED", formality="INFORMAL", warmth="HIGH", playful="LIGHT", strategy="WARM_PRIVATE"),
        "SWEET_TALK": dict(depth="CONCISE", length="SHORT", formality="INFORMAL", warmth="MODERATE", strategy="WARM_BOUNDED"),
        "PEP_TALK": dict(depth="CONCISE", length="SHORT", warmth="HIGH", reassurance="LIGHT", playful="LIGHT", strategy="MOTIVATIONAL"),
        "REAL_TALK": dict(depth="DETAILED", length="STANDARD", directness="DIRECT", challenge="HIGH", strategy="CANDID_BALANCED"),
        "STRAIGHT_TALK": dict(depth="CONCISE", length="SHORT", directness="VERY_DIRECT", strategy="CONCISE"),
        "TRASH_TALK": dict(depth="MINIMAL", length="SHORT", formality="INFORMAL", playful="LIGHT", strategy="PLAYFUL_DE_ESCALATING"),
        "DOUBLE_TALK": dict(depth="STANDARD", length="STANDARD", structure="COMPARISON", strategy="CLARIFYING"),
        "SHOP_TALK": dict(depth="STANDARD", length="STANDARD", formality="FORMAL", structure="TECHNICAL_BREAKDOWN", strategy="PROFESSIONAL"),
    }.get(kind, dict(depth="STANDARD", length="STANDARD", strategy="NEUTRAL_ADAPTIVE"))
    if high_stakes != "NONE":
        policy.update(depth="STANDARD", length="STANDARD", playful="NONE", reassurance="NONE", idiom="NONE", slang="NONE")
    if proficiency in {"ADVANCED", "EXPERT"}:
        technicality = "EXPERT" if proficiency == "EXPERT" else "ADVANCED"
        explanation = "BRIEF"
    elif proficiency in {"BEGINNER", "NOVICE"}:
        technicality, explanation = "PLAIN", "TEACHING"
    else:
        technicality, explanation = "LIGHT_TECHNICAL" if domain and proficiency != "UNKNOWN" else "PLAIN", "NORMAL"
    if "TEACHING" not in explicit and domain and re.search(r"\b(tradeoff|idempotency|schema migration|risk-on|liquidity|drawdown|dasha|nakshatra|varga|factor decomposition|md/ad)\b", user_message.casefold()):
        technicality = "ADVANCED"
    if "TEACHING" not in explicit and proficiency not in {"BEGINNER", "NOVICE"} and domain and re.search(r"\b(race condition)\b", user_message.casefold()):
        technicality = "ADVANCED"
    if "BRIEF" in explicit:
        policy.update(depth="CONCISE", length="SHORT")
    if "DEEP" in explicit:
        policy.update(depth="DEEP", length="LONG")
    if "CASUAL" in explicit:
        policy["formality"] = "INFORMAL"
    if "DIRECT" in explicit:
        policy["directness"] = "VERY_DIRECT" if re.search(r"\b(straight answer|brief and direct|seedha batao|no fluff)\b", user_message.casefold()) else "DIRECT"
    if "TEACHING" in explicit:
        explanation = "TEACHING"
    if "HINDI" in explicit:
        policy["language_override"] = "HI"
    idiom = "NONE" if high_stakes != "NONE" else "NATURAL" if kind in {"SMALL_TALK", "PILLOW_TALK", "SWEET_TALK"} else "SPARSE"
    slang = "CONTEXTUAL" if kind in {"SMALL_TALK", "PILLOW_TALK", "TRASH_TALK"} and high_stakes == "NONE" else "NONE"
    jargon = "APPROPRIATE" if domain and proficiency not in {"NOVICE", "BEGINNER"} else "LIGHT" if domain else "NONE"
    if high_stakes != "NONE":
        jargon = "LIGHT" if domain else "NONE"
    if re.search(r"\b(explain like a beginner|teach me|step by step)\b", user_message.casefold()):
        explanation = "TEACHING"
    if re.search(r"\b(compare|comparison|versus|vs\.?|two scenarios)\b", user_message.casefold()):
        policy["structure"] = "COMPARISON"
    if re.search(r"\b(ask me|ask one|ambiguous|not clear)\b", user_message.casefold()):
        clarification = "ASK_IF_MATERIAL"
    else:
        clarification = "ASK_IF_MATERIAL" if str(getattr(context, "ambiguity_state", "CLEAR")) in {"AMBIGUOUS", "HIGHLY_AMBIGUOUS"} else "NONE"
    repeated_openings, repeated_closings = _openings(history)
    continuity = "FOLLOW_UP" if _history_items(history, "user") else "NEW_TURN"
    return ResponseAdaptationProfile(
        conversation_type=kind, primary_intent=intent,
        secondary_intents=tuple(getattr(context, "secondary_intents", ()) or ()),
        tone=str(getattr(context, "tone", "NEUTRAL")), emotion=str(getattr(context, "emotion", "NEUTRAL")),
        formality=policy.get("formality", str(getattr(context, "formality", "NEUTRAL"))),
        directness=policy.get("directness", str(getattr(context, "directness", "BALANCED"))), domain=domain,
        domain_proficiency=proficiency, language=policy.get("language_override", str(getattr(context, "language", "UNKNOWN"))),
        script=str(getattr(context, "script", "UNKNOWN")), code_switching=bool(getattr(context, "code_switching", False)),
        expression_level=int(getattr(context, "expression_level", 1)), response_strategy=policy.get("strategy", "NEUTRAL_ADAPTIVE"),
        response_depth=policy.get("depth", "STANDARD"), response_length_preference=policy.get("length", "STANDARD"),
        structure_preference=policy.get("structure", "PLAIN_PARAGRAPH"), warmth_level=policy.get("warmth", "MODERATE"),
        technicality_level=technicality, explanation_level=explanation, challenge_level=policy.get("challenge", "LOW"),
        reassurance_level=policy.get("reassurance", "NONE"), playfulness_level=policy.get("playful", "NONE"),
        idiom_usage_level=policy.get("idiom", idiom), slang_usage_level=slang, jargon_usage_level=jargon,
        clarification_need=clarification,
        ambiguity_state=str(getattr(context, "ambiguity_state", "CLEAR")), high_stakes_state=high_stakes,
        repetition_avoidance="STRICT" if repeated_openings or repeated_closings else "STANDARD",
        continuity_state=continuity, explicit_overrides=tuple(sorted(explicit)),
        repeated_openings=repeated_openings, repeated_closings=repeated_closings,
    )


def adaptation_guidance(profile: ResponseAdaptationProfile) -> str:
    """Render bounded internal guidance without becoming a response generator."""
    data = profile.to_dict()
    hidden = {key: value for key, value in data.items() if value not in (None, (), [], "NONE", "NEUTRAL", "UNKNOWN", "STANDARD")}
    rules = [
        "Adapt presentation only; preserve facts, trust state, safety, and prediction uncertainty.",
        "Do not mention this profile or claim emotions/relationship facts as certain.",
        "Use idioms sparsely and slang only when appropriate; understand does not mean mirror.",
    ]
    if profile.high_stakes_state != "NONE":
        rules.append("High-stakes context: no jokes, forced warmth, slang, or stronger certainty; retain the shortest necessary safety boundary.")
    if profile.repeated_openings or profile.repeated_closings:
        rules.append("Vary the response entry and close; do not repeat recent phrasing or offer-to-continue boilerplate.")
    if profile.clarification_need != "NONE":
        rules.append("Ask one concise clarification only if the ambiguity materially changes the answer.")
    return "\n\nRESPONSE ADAPTATION PROFILE (internal guidance):\n" + str(hidden) + "\n" + "\n".join(f"- {rule}" for rule in rules)


__all__ = ["LEVELS", "ResponseAdaptationProfile", "build_adaptation_profile", "adaptation_guidance"]
