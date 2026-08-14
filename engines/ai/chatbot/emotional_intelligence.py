"""Deterministic emotional and relational context for VEDA conversations.

This module recognizes conversational signals conservatively. It is not a
clinical classifier, therapist, or response generator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


EMOTIONS = (
    "NEUTRAL", "CONTENT", "HAPPY", "EXCITED", "HOPEFUL", "RELIEVED",
    "SAD", "DISAPPOINTED", "GRIEVING", "LONELY", "WORRIED", "ANXIOUS_SIGNAL",
    "FEARFUL", "UNCERTAIN", "FRUSTRATED", "ANGRY", "HURT", "RESENTFUL",
    "CONFUSED", "OVERWHELMED", "EMBARRASSED", "GUILTY", "ASHAMED_SIGNAL",
    "AFFECTIONATE", "GRATEFUL", "VULNERABLE", "GUARDED", "CURIOUS", "MIXED", "UNKNOWN",
)
LEVELS = ("VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH")


@dataclass(slots=True)
class EmotionalContext:
    primary_emotion: str = "UNKNOWN"
    secondary_emotions: list[str] = field(default_factory=list)
    emotion_confidence: str = "LOW"
    emotional_intensity: str = "LOW"
    emotional_direction: str = "STABLE"
    emotional_stability: str = "STABLE"
    vulnerability_state: str = "NONE"
    distress_state: str = "NONE"
    frustration_state: str = "NONE"
    relationship_context: str = "UNKNOWN"
    interaction_need: str = "UNKNOWN"
    support_need: str = "UNKNOWN"
    advice_readiness: str = "UNKNOWN"
    reassurance_need: str = "NONE"
    validation_need: str = "NONE"
    clarification_need: str = "NONE"
    response_sensitivity: str = "NORMAL"
    escalation_risk: str = "NONE"
    emotional_ambiguity: str = "UNKNOWN"
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _lower(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().casefold())


def _has(value: str, *terms: str) -> bool:
    return any(term in value for term in terms)


def _score(value: str, terms: tuple[str, ...]) -> int:
    return sum(value.count(term) for term in terms)


def analyze_emotion(text: str, history: list[dict[str, Any]] | None = None, *, relationship_context: str = "UNKNOWN") -> EmotionalContext:
    value = _lower(text)
    evidence: list[str] = []
    scores = {
        "GRIEVING": _score(value, ("passed away", "died", "funeral", "bereaved", "loss of my father", "loss of my mother")),
        "LONELY": _score(value, ("lonely", "alone", "no one to talk", "isolated")),
        "SAD": _score(value, ("sad", "down", "heartbroken", "crying", "unhappy", "upset", "दुखी", "उदास")),
        "DISAPPOINTED": _score(value, ("disappointed", "didn't work out", "did not work out", "let down", "expected more")),
        "WORRIED": _score(value, ("worried", "worry", "concerned", "tension", "preshan", "pareshan", "chinta", "परेशान", "चिंता", "चिन्ता")),
        "FEARFUL": _score(value, ("afraid", "scared", "fear", "darr", "terrified", "threat", "डर", "भय")),
        "UNCERTAIN": _score(value, ("not sure", "uncertain", "don't know", "do not know", "confused about")),
        "FRUSTRATED": _score(value, ("frustrated", "fed up", "blocked", "stuck", "keeps failing", "mood off", "band baja")),
        "ANGRY": _score(value, ("angry", "furious", "rage", "shut up", "idiot", "hate")),
        "HURT": _score(value, ("hurt", "that really affected me", "betrayed")),
        "OVERWHELMED": _score(value, ("overwhelmed", "too much", "can't cope", "cannot cope")),
        "HAPPY": _score(value, ("happy", "glad", "great news", "so good")),
        "EXCITED": _score(value, ("excited", "can't wait", "cannot wait", "thrilled")),
        "HOPEFUL": _score(value, ("hopeful", "looking forward", "things can improve")),
        "RELIEVED": _score(value, ("relieved", "what a relief", "finally over")),
        "GRATEFUL": _score(value, ("grateful", "thank you", "thanks", "appreciate")),
        "AFFECTIONATE": _score(value, ("love you", "miss you", "dear", "yaar")),
        "CURIOUS": _score(value, ("curious", "wondering", "what does", "how does")),
        "EMBARRASSED": _score(value, ("embarrassed", "awkward", " शर्म ")),
        "GUILTY": _score(value, ("guilty", "my fault", "i regret")),
    }
    # Quoted, fictional, and metalinguistic language describes an emotion rather
    # than reporting the speaker's state.
    meta = bool(re.search(r"\b(what does|what is|define|meaning of)\b", value) and re.search(r"\b(grief|anger|sadness|fear|emotion)\b", value))
    quoted = bool(re.search(r"\b(said|says|told me)\b\s*['\"]", value))
    fictional = bool(re.search(r"\b(write|create|character|fiction|story)\b", value) and re.search(r"\b(devastated|angry|grieving|sad)\b", value))
    if meta or quoted or fictional:
        return EmotionalContext(primary_emotion="UNKNOWN", emotion_confidence="VERY_LOW", emotional_ambiguity="UNKNOWN", evidence=["non_personal_emotional_language"])

    ranked = sorted(((name, points) for name, points in scores.items() if points), key=lambda item: item[1], reverse=True)
    if not ranked:
        primary = "NEUTRAL" if value else "UNKNOWN"
        confidence = "MODERATE" if primary == "NEUTRAL" else "VERY_LOW"
        secondary: list[str] = []
    else:
        primary, top = ranked[0]
        secondary = [name for name, points in ranked[1:] if points and points >= top - 1][:2]
        confidence = "VERY_HIGH" if top >= 2 and not secondary else "HIGH" if top >= 1 else "LOW"
        if secondary:
            primary = "MIXED"
        evidence = [f"emotion_signal:{name}" for name, _ in ranked[:4]]

    explicit_vent = _has(value, "just need to vent", "only need to vent", "let me vent", "don't give advice", "do not give advice")
    advice = _has(value, "what should i", "what do i do", "please advise", "give me advice", "how should i", "help me decide")
    direct = _has(value, "straight answer", "be direct", "no fluff", "seedha batao")
    need = "JUST_LISTEN" if explicit_vent else "GIVE_ADVICE" if advice else "GIVE_DIRECT_ANSWER" if direct else "ACKNOWLEDGE" if primary not in {"NEUTRAL", "UNKNOWN"} else "UNKNOWN"
    readiness = "NOT_SEEKING_ADVICE" if explicit_vent else "EXPLICITLY_REQUESTING_ADVICE" if advice else "UNKNOWN"
    intensity = "VERY_HIGH" if _has(value, "devastated", "furious", "terrified", "completely overwhelmed") else "HIGH" if primary not in {"NEUTRAL", "UNKNOWN"} and ("!" in str(text) or len(value.split()) > 14) else "MODERATE" if primary not in {"NEUTRAL", "UNKNOWN"} else "LOW"
    vulnerability = "HIGH" if _has(value, "passed away", "heartbroken", "very alone", "ashamed", "scared to tell") else "LIKELY" if primary in {"SAD", "LONELY", "GRIEVING", "HURT", "OVERWHELMED"} else "POSSIBLE" if primary in {"WORRIED", "UNCERTAIN", "DISAPPOINTED"} else "NONE"
    distress = "HIGH" if primary in {"GRIEVING", "OVERWHELMED", "FEARFUL"} and intensity in {"HIGH", "VERY_HIGH"} else "POSSIBLE" if primary in {"WORRIED", "SAD", "LONELY", "HURT"} else "NONE"
    sensitivity = "HIGHLY_SENSITIVE" if distress == "HIGH" or vulnerability == "HIGH" else "SENSITIVE" if vulnerability in {"LIKELY", "POSSIBLE"} else "ATTENTIVE" if primary not in {"NEUTRAL", "UNKNOWN"} else "NORMAL"
    escalation = "HIGH" if primary == "ANGRY" and intensity in {"HIGH", "VERY_HIGH"} else "RISING" if primary in {"ANGRY", "FRUSTRATED", "RESENTFUL"} else "NONE"
    reassurance = "MODERATE" if primary in {"FEARFUL", "WORRIED", "LONELY"} and advice else "LIGHT" if primary in {"WORRIED", "SAD", "DISAPPOINTED"} else "NONE"
    validation = "MODERATE" if primary in {"HURT", "DISAPPOINTED", "FRUSTRATED", "SAD"} else "LIGHT" if primary not in {"NEUTRAL", "UNKNOWN"} else "NONE"
    ambiguity = "MIXED" if secondary or primary == "MIXED" else "CLEAR" if confidence in {"HIGH", "VERY_HIGH"} else "AMBIGUOUS"
    previous = []
    for item in (history or ())[-3:]:
        previous.append(str(item.get("primary_emotion") or item.get("emotion") or ""))
    direction = "STABLE"
    if previous and previous[-1] and previous[-1] != primary:
        direction = "SHIFTING"
    return EmotionalContext(
        primary_emotion=primary, secondary_emotions=secondary, emotion_confidence=confidence,
        emotional_intensity=intensity, emotional_direction=direction, emotional_stability="STABLE" if direction == "STABLE" else "CHANGING",
        vulnerability_state=vulnerability, distress_state=distress, frustration_state="HIGH" if primary == "FRUSTRATED" else "POSSIBLE" if "FRUSTRATED" in secondary else "NONE",
        relationship_context=relationship_context, interaction_need=need, support_need="EMOTIONAL_SUPPORT" if primary not in {"NEUTRAL", "UNKNOWN"} else "NONE",
        advice_readiness=readiness, reassurance_need=reassurance, validation_need=validation,
        clarification_need="ASK_IF_MATERIAL" if ambiguity in {"MIXED", "AMBIGUOUS"} else "NONE", response_sensitivity=sensitivity,
        escalation_risk=escalation, emotional_ambiguity=ambiguity, evidence=evidence,
    )


__all__ = ["EMOTIONS", "LEVELS", "EmotionalContext", "analyze_emotion"]
