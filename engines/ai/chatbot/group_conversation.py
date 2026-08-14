"""Deterministic multi-speaker context for the existing VEDA ChatEngine.

This module analyzes supplied turn metadata and bounded in-session history. It
does not create agents, persist a second conversation store, or generate text.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


PARTICIPANT_KINDS = ("USER", "VEDA", "HUMAN_PARTICIPANT", "UNKNOWN_PARTICIPANT")
CONFIDENCE = ("EXPLICIT", "HIGH", "MODERATE", "LOW", "UNKNOWN")
PARTICIPATION = ("RESPOND", "OPTIONAL_RESPONSE", "OBSERVE", "DO_NOT_RESPOND")
AGREEMENT = ("AGREES", "PARTIALLY_AGREES", "DISAGREES", "STRONGLY_DISAGREES", "NEUTRAL", "UNCLEAR")
CONFLICT = ("NONE", "LOW", "RISING", "HIGH", "DE_ESCALATING", "RESOLVED")


@dataclass(frozen=True, slots=True)
class GroupParticipant:
    participant_id: str
    speaker_id: str
    display_name: str | None = None
    speaker_role: str = "unknown"
    relationship: str = "unknown"
    identity_confidence: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GroupTurn:
    conversation_id: str
    turn_id: str
    speaker_id: str
    timestamp: str | None
    message_text: str
    reply_to_turn_id: str | None = None
    reply_to_speaker_id: str | None = None
    addressed_to_participant_ids: tuple[str, ...] = ()
    mentions: tuple[str, ...] = ()
    quoted_turn_id: str | None = None
    chart_subject_id: str | None = None
    subject_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GroupAnalysis:
    conversation_id: str
    turn: GroupTurn
    speaker_confidence: str = "UNKNOWN"
    veda_address: str = "AMBIGUOUS"
    participation_decision: str = "OBSERVE"
    response_target: str = "TARGET_GROUP"
    topic_id: str = "topic-1"
    topic_label: str = "general conversation"
    topic_owner: str | None = None
    topic_shift: str = "TOPIC_CONTINUATION"
    agreement_state: str = "UNCLEAR"
    agreement_with: tuple[str, ...] = ()
    disagreement_with: tuple[str, ...] = ()
    conflict_state: str = "NONE"
    conflict_participants: tuple[str, ...] = ()
    consensus_state: str = "NO_CONSENSUS"
    position: str = "UNKNOWN"
    previous_position: str | None = None
    claim_attribution: str | None = None
    quoted_speech: bool = False
    pronoun_ambiguity: bool = False
    language: str = "UNKNOWN"
    conversation_type: str = "UNKNOWN"
    intent: str = "UNKNOWN"
    confidence: str = "LOW"
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["turn"] = self.turn.to_dict()
        return payload


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _participants(raw: Iterable[dict[str, Any]] | None, speaker_id: str, speaker_name: str | None) -> list[GroupParticipant]:
    result: list[GroupParticipant] = []
    for item in raw or ():
        pid = str(_value(item, "participant_id", _value(item, "speaker_id", "unknown")))
        result.append(GroupParticipant(
            participant_id=pid,
            speaker_id=str(_value(item, "speaker_id", pid)),
            display_name=_value(item, "display_name", _value(item, "speaker_name")),
            speaker_role=str(_value(item, "speaker_role", "unknown")),
            relationship=str(_value(item, "relationship", "unknown")),
            identity_confidence="EXPLICIT",
        ))
    if not any(item.speaker_id == speaker_id for item in result):
        result.append(GroupParticipant(speaker_id, speaker_id, speaker_name, "unknown", "unknown", "EXPLICIT" if speaker_id else "UNKNOWN"))
    return result


def _name_map(participants: list[GroupParticipant]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in participants:
        result[item.speaker_id.casefold()] = item.speaker_id
        if item.display_name:
            result[item.display_name.casefold()] = item.speaker_id
    return result


def _resolve_addresses(text: str, participants: list[GroupParticipant], explicit: Iterable[str] | None) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    if explicit:
        ids = tuple(str(item) for item in explicit)
        return ids, tuple(), "EXPLICIT"
    names = _name_map(participants)
    mentions: list[str] = []
    addressed: list[str] = []
    for raw in re.findall(r"@([\w-]+)|\b([A-Z][a-z]{2,})\b", text):
        token = next((part for part in raw if part), "").casefold()
        if token in names:
            mentions.append(names[token])
            addressed.append(names[token])
    return tuple(dict.fromkeys(addressed)), tuple(dict.fromkeys(mentions)), "HIGH" if addressed else "UNKNOWN"


def _topic(text: str) -> tuple[str, str]:
    value = text.casefold()
    topics = {
        "jyotisha": ("jyotisha", "dasha", "d9", "chart", "kundli", "nakshatra"),
        "portfolio allocation": ("portfolio", "allocation", "stock", "shares", "buy", "sell"),
        "software design": ("api", "software", "server", "bug", "code", "migration"),
        "health question": ("health", "symptom", "medical", "doctor"),
        "tax impact": ("tax", "taxes", "deduction"),
    }
    label, terms = max(topics.items(), key=lambda item: sum(term in value for term in item[1]))
    return (f"topic-{label.replace(' ', '-')}", label) if any(term in value for term in terms) else ("topic-general", "general conversation")


def _agreement(text: str) -> str:
    value = text.casefold()
    if re.search(r"\b(strongly disagree|absolutely not|you're wrong|you are wrong)\b", value):
        return "STRONGLY_DISAGREES"
    if re.search(r"\b(i disagree|disagree|not convinced|but that ignores)\b", value):
        return "DISAGREES"
    if re.search(r"\b(partly agree|partially agree|yes, but|i agree .* however)\b", value):
        return "PARTIALLY_AGREES"
    if re.search(r"\b(i agree|agree|exactly|that's right|that is right|yes)\b", value):
        return "AGREES"
    return "NEUTRAL"


def _conflict(text: str, previous: str | None) -> tuple[str, tuple[str, ...]]:
    value = text.casefold()
    if re.search(r"\b(apolog|sorry|let's calm|let us calm|i understand your point|meet halfway)\b", value):
        return ("DE_ESCALATING" if previous in {"RISING", "HIGH"} else "RESOLVED", ("softening_or_reconciliation",))
    if re.search(r"\b(idiot|shut up|loser|stupid|you always|you never|hate you|threat)\b", value):
        return ("HIGH", ("hostile_language",))
    if re.search(r"\b(disagree|wrong|ridiculous|nonsense|stop)\b", value):
        return ("RISING" if previous in {"LOW", "RISING"} else "LOW", ("contradiction_or_frustration",))
    return (previous if previous in CONFLICT else "NONE", ())


def _participation(veda_address: str, addresses: tuple[str, ...], text: str) -> tuple[str, str]:
    value = text.casefold()
    if veda_address == "DIRECTLY_ADDRESSED":
        return "RESPOND", "TARGET_GROUP" if len(addresses) > 1 else "TARGET_SINGLE_PARTICIPANT"
    if veda_address == "GROUP_ADDRESSED":
        return "RESPOND", "TARGET_GROUP"
    if veda_address == "NOT_ADDRESSED":
        return "OBSERVE", "TARGET_GROUP"
    if "?" in text or re.search(r"\b(what do you think|should we|can someone summarize|veda)\b", value):
        return "OPTIONAL_RESPONSE", "TARGET_GROUP"
    return "OBSERVE", "TARGET_GROUP"


def analyze_group_turn(
    message_text: str,
    *,
    conversation_id: str = "conversation-1",
    speaker_id: str = "user",
    speaker_name: str | None = None,
    speaker_role: str = "unknown",
    participants: Iterable[dict[str, Any]] | None = None,
    turn_id: str = "turn-1",
    timestamp: str | None = None,
    reply_to_turn_id: str | None = None,
    reply_to_speaker_id: str | None = None,
    addressed_to: Iterable[str] | None = None,
    chart_subject_id: str | None = None,
    subject_label: str | None = None,
    quoted_turn_id: str | None = None,
    history: Iterable[dict[str, Any]] | None = None,
    veda_id: str = "veda",
) -> GroupAnalysis:
    """Analyze one turn using trusted transport metadata plus conservative cues."""
    text = str(message_text or "")
    people = _participants(participants, speaker_id, speaker_name)
    addresses, mentions, address_confidence = _resolve_addresses(text, people, addressed_to)
    veda_names = {veda_id.casefold(), "veda", "assistant"}
    address_names = {item.casefold() for item in addresses}
    if veda_id.casefold() in address_names or "veda" in address_names or re.search(r"\b(veda|assistant)\b", text.casefold()):
        veda_address = "DIRECTLY_ADDRESSED"
    elif "group" in address_names or (addressed_to and len(addresses) > 1):
        veda_address = "GROUP_ADDRESSED"
    elif addressed_to:
        veda_address = "NOT_ADDRESSED"
    elif "everyone" in text.casefold() or "all of you" in text.casefold():
        veda_address = "GROUP_ADDRESSED"
    else:
        veda_address = "AMBIGUOUS" if "?" in text else "NOT_ADDRESSED"
    participation, target = _participation(veda_address, addresses, text)
    prior = next((str(_value(item, "conflict_state", "")) for item in reversed(list(history or ())) if _value(item, "conflict_state")), None)
    conflict, conflict_evidence = _conflict(text, prior)
    topic_id, topic_label = _topic(text)
    previous_topic = next((str(_value(item, "topic_id", "")) for item in reversed(list(history or ())) if _value(item, "topic_id")), None)
    prior_topics = {str(_value(item, "topic_id", "")) for item in (history or ())}
    if previous_topic == topic_id:
        topic_shift = "TOPIC_CONTINUATION"
    elif topic_id in prior_topics:
        topic_shift = "RETURN_TO_PRIOR_TOPIC"
    else:
        topic_shift = "NEW_TOPIC"
    agreement = _agreement(text)
    quoted = bool(re.search(r"(?:said|says|quote|according to)\s*[:\"]", text.casefold()) or re.search(r"['\"]+[^'\"]+['\"]+", text))
    pronoun_ambiguity = bool(re.search(r"\b(he|she|they|them|the others)\b", text.casefold())) and not addresses
    language = "HI" if re.search(r"[\u0900-\u097f]", text) else "HINGLISH" if re.search(r"\b(yaar|hai|kya|mujhe|scene|mood|batao)\b", text.casefold()) else "EN"
    position = "SUPPORTS" if agreement == "AGREES" else "OPPOSES" if agreement in {"DISAGREES", "STRONGLY_DISAGREES"} else "UNDECIDED"
    previous_position = next(
        (str(_value(item, "position")) for item in reversed(list(history or ()))
         if _value(item, "speaker_id") == speaker_id and _value(item, "position")),
        None,
    )
    if "consensus" in text.casefold() or "shared decision" in text.casefold():
        consensus = "STRONG_CONSENSUS"
    elif agreement == "AGREES" and any(_value(item, "agreement_state") == "AGREES" for item in (history or ())):
        consensus = "EMERGING_CONSENSUS"
    elif agreement == "PARTIALLY_AGREES":
        consensus = "PARTIAL_CONSENSUS"
    else:
        consensus = "NO_CONSENSUS"
    veda_turn = speaker_id.casefold() == veda_id.casefold()
    if veda_turn:
        veda_address = "NOT_ADDRESSED"
        participation = "OBSERVE"
    turn = GroupTurn(
        conversation_id=conversation_id, turn_id=turn_id, speaker_id=speaker_id,
        timestamp=timestamp, message_text=text, reply_to_turn_id=reply_to_turn_id,
        reply_to_speaker_id=reply_to_speaker_id, addressed_to_participant_ids=addresses,
        mentions=mentions, quoted_turn_id=quoted_turn_id, chart_subject_id=chart_subject_id,
        subject_label=subject_label,
    )
    return GroupAnalysis(
        conversation_id=conversation_id, turn=turn,
        speaker_confidence="EXPLICIT" if speaker_id else address_confidence,
        veda_address=veda_address, participation_decision=participation,
        response_target=target, topic_id=topic_id, topic_label=topic_label,
        topic_owner=speaker_id if topic_shift == "NEW_TOPIC" or not previous_topic else None,
        topic_shift=topic_shift, agreement_state=agreement,
        conflict_state=conflict, conflict_participants=(speaker_id,) if conflict != "NONE" else (),
        consensus_state=consensus,
        agreement_with=addresses if agreement in {"AGREES", "PARTIALLY_AGREES"} else (),
        disagreement_with=addresses if agreement in {"DISAGREES", "STRONGLY_DISAGREES"} else (),
        position=position, previous_position=previous_position,
        claim_attribution=None if quoted else speaker_id,
        quoted_speech=quoted, pronoun_ambiguity=pronoun_ambiguity, language=language,
        confidence="HIGH" if speaker_id and (reply_to_turn_id or addresses) else "MODERATE",
        evidence=tuple(conflict_evidence) + (("explicit_reply_metadata",) if reply_to_turn_id else ()) + (("explicit_addressee",) if addressed_to else ()),
    )


def analyze_group_transcript(turns: Iterable[dict[str, Any]], *, conversation_id: str = "conversation-1", veda_id: str = "veda") -> list[dict[str, Any]]:
    """Analyze a bounded transcript without retaining state outside the call."""
    history: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for index, raw in enumerate(turns, 1):
        analysis = analyze_group_turn(
            str(_value(raw, "message_text", _value(raw, "text", ""))),
            conversation_id=str(_value(raw, "conversation_id", conversation_id)),
            speaker_id=str(_value(raw, "speaker_id", "unknown")), speaker_name=_value(raw, "speaker_name", _value(raw, "display_name")),
            participants=_value(raw, "participants"), turn_id=str(_value(raw, "turn_id", f"turn-{index}")),
            timestamp=_value(raw, "timestamp"), reply_to_turn_id=_value(raw, "reply_to_turn_id"),
            reply_to_speaker_id=_value(raw, "reply_to_speaker_id"), addressed_to=_value(raw, "addressed_to"),
            chart_subject_id=_value(raw, "chart_subject_id"), subject_label=_value(raw, "subject_label"),
            quoted_turn_id=_value(raw, "quoted_turn_id"),
            history=history, veda_id=veda_id,
        )
        payload = analysis.to_dict()
        results.append(payload)
        history.append(payload)
    return results


__all__ = ["PARTICIPANT_KINDS", "CONFIDENCE", "PARTICIPATION", "AGREEMENT", "CONFLICT", "GroupParticipant", "GroupTurn", "GroupAnalysis", "analyze_group_turn", "analyze_group_transcript"]
