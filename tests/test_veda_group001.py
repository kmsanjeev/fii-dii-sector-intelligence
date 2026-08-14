import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import chat as chat_router
from engines.ai.chatbot.group_conversation import (
    AGREEMENT,
    CONFIDENCE,
    PARTICIPATION,
    analyze_group_transcript,
    analyze_group_turn,
)


def _benchmark():
    return json.loads(Path("tests/fixtures/veda_group001_benchmark.json").read_text(encoding="utf-8"))


def _people():
    return [
        {"participant_id": "ravi", "speaker_id": "ravi", "display_name": "Ravi"},
        {"participant_id": "meena", "speaker_id": "meena", "display_name": "Meena"},
        {"participant_id": "veda", "speaker_id": "veda", "display_name": "Veda", "speaker_role": "assistant"},
    ]


def test_group001_canonical_contract_and_bounded_enums():
    result = analyze_group_turn(
        "Ravi, what do you think?", conversation_id="g1", speaker_id="asha",
        participants=_people(), turn_id="t1", addressed_to=["ravi"],
    )
    payload = result.to_dict()
    assert payload["conversation_id"] == "g1"
    assert payload["turn"]["speaker_id"] == "asha"
    assert payload["turn"]["addressed_to_participant_ids"] == ("ravi",)
    assert result.speaker_confidence in CONFIDENCE
    assert result.participation_decision in PARTICIPATION
    assert result.agreement_state in AGREEMENT
    assert {"turn", "topic_id", "topic_owner", "conflict_state", "response_target"}.issubset(payload)


def test_group001_explicit_speaker_reply_and_addressee_are_not_conflated():
    result = analyze_group_turn(
        "Ravi, reply to the earlier point.", conversation_id="g1", speaker_id="meena",
        participants=_people(), turn_id="t2", reply_to_turn_id="t1", reply_to_speaker_id="ravi",
        addressed_to=["ravi"],
    )
    assert result.turn.speaker_id == "meena"
    assert result.turn.reply_to_speaker_id == "ravi"
    assert result.turn.addressed_to_participant_ids == ("ravi",)
    assert result.veda_address == "NOT_ADDRESSED"
    assert result.participation_decision == "OBSERVE"
    assert result.speaker_confidence == "EXPLICIT"


def test_group001_veda_address_and_participation_policy():
    direct = analyze_group_turn("@veda, summarize both positions.", speaker_id="ravi", participants=_people(), addressed_to=["veda"])
    other = analyze_group_turn("Meena, what do you think?", speaker_id="ravi", participants=_people(), addressed_to=["meena"])
    ambiguous = analyze_group_turn("What do you all think?", speaker_id="ravi", participants=_people())
    assert direct.veda_address == "DIRECTLY_ADDRESSED"
    assert direct.participation_decision == "RESPOND"
    assert other.veda_address == "NOT_ADDRESSED"
    assert other.participation_decision == "OBSERVE"
    assert ambiguous.participation_decision in {"OPTIONAL_RESPONSE", "OBSERVE"}


def test_group001_topics_ownership_and_shift_are_scoped_to_transcript():
    results = analyze_group_transcript([
        {"speaker_id": "ravi", "text": "Portfolio allocation is my concern.", "turn_id": "t1"},
        {"speaker_id": "meena", "text": "I want to discuss the tax impact.", "turn_id": "t2"},
        {"speaker_id": "ravi", "text": "Let us return to the portfolio allocation.", "turn_id": "t3"},
    ], conversation_id="g1")
    assert results[0]["topic_owner"] == "ravi"
    assert results[1]["topic_shift"] == "NEW_TOPIC"
    assert results[2]["topic_shift"] == "RETURN_TO_PRIOR_TOPIC"
    assert all(item["conversation_id"] == "g1" for item in results)


def test_group001_agreement_conflict_deescalation_and_consensus_signals():
    rising = analyze_group_turn("I disagree; that is wrong.", speaker_id="meena", history=[{"conflict_state": "LOW"}])
    high = analyze_group_turn("Stop calling me stupid.", speaker_id="ravi", history=[{"conflict_state": "RISING"}])
    calm = analyze_group_turn("Sorry, I understand your point. Let us meet halfway.", speaker_id="meena", history=[{"conflict_state": "HIGH"}])
    agree = analyze_group_turn("I agree with Ravi on the long-term plan.", speaker_id="meena", history=[{"agreement_state": "AGREES"}])
    assert rising.agreement_state == "DISAGREES"
    assert rising.conflict_state == "RISING"
    assert high.conflict_state == "HIGH"
    assert calm.conflict_state == "DE_ESCALATING"
    assert agree.agreement_state == "AGREES"
    assert agree.consensus_state == "EMERGING_CONSENSUS"


def test_group001_claim_quote_and_pronoun_safety():
    quoted = analyze_group_turn("Meena said 'sell it now', but I disagree.", speaker_id="ravi")
    pronoun = analyze_group_turn("She thinks the risk is low.", speaker_id="ravi")
    assert quoted.quoted_speech is True
    assert quoted.claim_attribution is None
    assert pronoun.pronoun_ambiguity is True


def test_group001_language_and_jyotisha_subject_triad():
    hindi = analyze_group_turn("मुझे लगता है हमें रुकना चाहिए।", speaker_id="meena")
    hinglish = analyze_group_turn("Yaar, scene kya hai?", speaker_id="ravi")
    chart = analyze_group_turn(
        "What do you think about my son's career?", speaker_id="father",
        addressed_to=["veda"], chart_subject_id="son", subject_label="son",
    )
    assert hindi.language == "HI"
    assert hinglish.language == "HINGLISH"
    assert chart.turn.speaker_id == "father"
    assert chart.turn.chart_subject_id == "son"
    assert chart.turn.addressed_to_participant_ids == ("veda",)
    assert chart.veda_address == "DIRECTLY_ADDRESSED"


def test_group001_benchmark_and_multiturn_fixtures_meet_minimum_size():
    records = _benchmark()
    transitions = json.loads(Path("tests/fixtures/veda_group001_transitions.json").read_text(encoding="utf-8"))
    assert len(records) >= 50
    assert len(transitions) >= 15
    assert {record["speaker"] for record in records} >= {"ravi", "meena", "sanjay", "veda"}
    assert any(record.get("chart_subject_id") for record in records)
    assert any(record.get("quoted") for record in records)


def test_group001_single_user_fallback_is_observe_and_no_extra_store():
    result = analyze_group_turn("What is the market outlook?", conversation_id="single", speaker_id="user")
    assert result.conversation_id == "single"
    assert result.turn.speaker_id == "user"
    assert result.participation_decision in {"OBSERVE", "OPTIONAL_RESPONSE"}
    assert not hasattr(result, "database")


def test_group001_chat_api_accepts_optional_group_contract_and_legacy_requests(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "group-test-key")

    class FakeEngine:
        last_symbols = []
        last_flag = {"flagged": False, "reason": None}
        last_research = {}
        last_local_evidence = {}
        last_retrieval_audit = {}
        last_orchestration = {}
        last_conversational_context = {}

        def chat(self, message, **kwargs):
            if kwargs.get("group_context"):
                self.last_conversational_context = {"group": {"speaker_id": kwargs["group_context"]["speaker_id"]}}
            return "Group-safe reply."

    monkeypatch.setattr(chat_router, "_get_or_create_session", lambda session_id: ("g1", FakeEngine()))
    app = FastAPI()
    app.include_router(chat_router.router)
    client = TestClient(app)
    legacy = client.post("/api/chat", json={"message": "Hello"})
    group = client.post("/api/chat", json={
        "message": "@veda, summarize.", "conversation_id": "g1", "speaker_id": "ravi",
        "participants": _people(), "addressed_to": ["veda"], "turn_id": "t1",
    })
    assert legacy.status_code == 200
    assert group.status_code == 200
