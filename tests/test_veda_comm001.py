import json
from pathlib import Path

from engines.ai.chatbot.conversation_intelligence import (
    INTENTS,
    SUPPORTED_CONVERSATION_TYPES,
    analyze_conversation,
)


def _benchmark():
    path = Path("tests/fixtures/veda_std003_conversation_benchmark.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_comm001_canonical_context_and_supported_states():
    context = analyze_conversation("Be honest: explain the Dasha evidence, no fluff.")
    payload = context.to_dict()
    for key in (
        "conversation_type_confidence", "secondary_types", "primary_intent", "secondary_intents",
        "script", "literal_meaning", "likely_pragmatic_meaning", "ambiguity_state", "evidence",
        "transition_confidence", "state_stable", "response_strategy",
    ):
        assert key in payload
    assert context.conversation_type in SUPPORTED_CONVERSATION_TYPES
    assert context.primary_intent in INTENTS
    assert context.domain == "JYOTISHA"


def test_comm001_benchmark_has_fifty_initial_type_examples():
    records = _benchmark()
    initial = records[:50]
    assert len(initial) >= 50
    assert {record["type"] for record in initial} == {
        "SMALL_TALK", "HEART_TO_HEART", "PILLOW_TALK", "SWEET_TALK", "PEP_TALK",
        "REAL_TALK", "STRAIGHT_TALK", "TRASH_TALK", "DOUBLE_TALK", "SHOP_TALK",
    }
    assert all(sum(record["type"] == kind for record in initial) >= 5 for kind in {
        "SMALL_TALK", "HEART_TO_HEART", "PILLOW_TALK", "SWEET_TALK", "PEP_TALK",
        "REAL_TALK", "STRAIGHT_TALK", "TRASH_TALK", "DOUBLE_TALK", "SHOP_TALK",
    })


def test_comm001_transition_benchmark_has_ten_sequences():
    path = Path("tests/fixtures/veda_comm001_transitions.json")
    records = json.loads(path.read_text(encoding="utf-8"))
    assert len(records) >= 10
    assert all({"before", "after", "from", "to"}.issubset(record) for record in records[:10])


def test_comm001_pragmatics_ambiguity_and_literal_separation():
    context = analyze_conversation("I am fine.")
    assert context.literal_meaning == "i am fine."
    assert context.ambiguity_state == "AMBIGUOUS"
    assert context.alternative_interpretation
    double_talk = analyze_conversation("We will revisit the opportunity at the appropriate time.")
    assert double_talk.literal_meaning == "future consideration"
    assert "deferral" in double_talk.likely_pragmatic_meaning
    assert "lying" not in double_talk.likely_pragmatic_meaning


def test_comm001_adversarial_sarcasm_and_non_sarcasm():
    assert analyze_conversation("Great. Another server crash.").sarcasm in {"POSSIBLE", "LIKELY"}
    assert analyze_conversation("Great, the deployment finally passed!").sarcasm == "NONE"


def test_comm001_multilabel_intent_and_hysteresis():
    context = analyze_conversation("Be direct: explain the API design, no fluff.")
    assert context.conversation_type == "STRAIGHT_TALK"
    assert "SHOP_TALK" in context.secondary_types
    assert context.primary_intent == "REQUEST_EXPLANATION"
    assert context.secondary_intents == ["LEARN"]
    stable = analyze_conversation("Okay", history=[{"role": "user", "content": "I feel lonely and need to talk."}])
    assert stable.conversation_type == "HEART_TO_HEART"
    assert stable.state_stable is True


def test_comm001_transition_metadata_and_domains():
    context = analyze_conversation(
        "I feel lonely and need to talk.",
        history=[{"role": "user", "content": "How was your weekend?"}],
    )
    assert context.conversation_type == "HEART_TO_HEART"
    assert context.transition_from == "SMALL_TALK"
    assert context.transition_confidence in {"HIGH", "MODERATE"}
    assert analyze_conversation("Research the evidence in this paper.").domain == "RESEARCH"
    assert analyze_conversation("What is the business strategy?").domain == "BUSINESS"


def test_comm001_chat_engine_falls_back_if_analyzer_fails(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    import engines.ai.chatbot.chat_engine as chat_module
    from engines.ai.chatbot.chat_engine import ChatEngine

    monkeypatch.setattr(chat_module, "analyze_conversation", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("broken")))
    engine = ChatEngine()
    monkeypatch.setattr(engine, "_get_rag_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(engine, "_get_external_research_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(engine, "_active_providers", lambda: [{"name": "stub", "model": "test", "env_var": "OPENAI_API_KEY", "base_url": "", "extra_headers": {}}])
    monkeypatch.setattr(engine, "_get_client", lambda provider: object())
    monkeypatch.setattr(engine, "_run_turn", lambda *args, **kwargs: {"status": "ok", "reply": "fallback"})
    assert engine.chat("unclear") == "fallback"
    assert engine.last_conversational_context["conversation_type"] == "UNKNOWN"
    assert engine.last_conversational_context["confidence"] == "VERY_LOW"
