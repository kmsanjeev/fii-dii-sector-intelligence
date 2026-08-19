from engines.ai.chatbot.conversation_intelligence import (
    CONVERSATION_TYPES,
    analyze_conversation,
    detect_language,
)


def test_std003_taxonomy_covers_v1_types():
    assert CONVERSATION_TYPES == (
        "SMALL_TALK", "HEART_TO_HEART", "PILLOW_TALK", "SWEET_TALK", "PEP_TALK",
        "REAL_TALK", "STRAIGHT_TALK", "TRASH_TALK", "DOUBLE_TALK", "SHOP_TALK",
    )


def test_std003_classifies_required_conversation_examples():
    examples = {
        "How are you? The weekend was lovely.": "SMALL_TALK",
        "I feel lonely and need to talk about my fear.": "HEART_TO_HEART",
        "I miss you. Sweet dreams and our future.": "PILLOW_TALK",
        "You are amazing, please do me a favour.": "SWEET_TALK",
        "Give me a pep talk; I feel like giving up.": "PEP_TALK",
        "Real talk: give me an uncomfortable truth.": "REAL_TALK",
        "Just tell me the bottom line, no fluff.": "STRAIGHT_TALK",
        "Trash talk: you cannot beat me, noob.": "TRASH_TALK",
        "We will certainly revisit the strategic opportunity at the appropriate time.": "DOUBLE_TALK",
        "Explain the API deployment bug in this repository.": "SHOP_TALK",
    }
    for message, expected in examples.items():
        assert analyze_conversation(message).conversation_type == expected


def test_std003_language_and_code_switching():
    assert detect_language("What is the market mood today?") == ("EN", False)
    assert detect_language("yaar, market ka mood aaj bilkul off hai") == ("HINGLISH", True)
    assert detect_language("मेरा मूड आज ठीक नहीं है") == ("HI", False)
    assert analyze_conversation("yaar, market ka mood aaj bilkul off hai").code_switching is True


def test_std003_contextual_expressions_and_non_mirroring():
    context = analyze_conversation("Yaar, scene kya hai? This is a piece of cake, not bakwaas.")
    assert {item["expression"] for item in context.idioms} == {"piece of cake", "scene kya hai"}
    assert {item["expression"] for item in context.slang} == {"yaar", "scene kya hai", "bakwaas"}
    assert context.understood_not_mirrored is True


def test_std003_pragmatics_domain_and_proficiency():
    context = analyze_conversation("Be direct: explain how Dasha activation interacts with the Varga.")
    assert context.conversation_type == "STRAIGHT_TALK"
    assert context.directness == "VERY_DIRECT"
    assert context.domain == "JYOTISHA"
    assert context.user_proficiency == "ADVANCED"
    assert context.response_strategy == "CONCISE"


def test_std003_multiturn_transition_and_safe_fallback():
    context = analyze_conversation(
        "Actually, I feel worried and need to talk.",
        history=[{"role": "user", "content": "How are you? The weekend was lovely."}],
    )
    assert context.conversation_type == "HEART_TO_HEART"
    assert context.transition_from == "SMALL_TALK"
    fallback = analyze_conversation("xyzzy qwerty")
    assert fallback.language == "UNKNOWN"
    assert fallback.response_strategy == "NEUTRAL_ADAPTIVE"


def test_std003_chat_engine_consumes_context_without_extra_provider_call(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from engines.ai.chatbot.chat_engine import ChatEngine

    engine = ChatEngine()
    calls = {"rag": 0}
    captured = {}
    monkeypatch.setattr(engine, "_get_rag_context", lambda *args, **kwargs: calls.__setitem__("rag", calls["rag"] + 1) or "")
    monkeypatch.setattr(engine, "_get_external_research_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(engine, "_active_providers", lambda: [{"name": "OpenAI", "model": "test", "env_var": "OPENAI_API_KEY", "base_url": "", "extra_headers": {}}])
    monkeypatch.setattr(engine, "_get_client", lambda provider: object())

    def fake_run_turn(client, model, system_prompt, user_message, use_tools=True, voice_mode=False):
        captured["prompt"] = system_prompt
        return {"status": "ok", "reply": "I am here with you."}

    monkeypatch.setattr(engine, "_run_turn", fake_run_turn)
    assert engine.chat("I feel lonely and need to talk.") == "I am here with you."
    assert engine.last_conversational_context["conversation_type"] == "HEART_TO_HEART"
    assert "SUPPORTIVE" in captured["prompt"]
    # General conversation must not inherit market/RAG context merely because
    # it is not a specialist keyword match.
    assert calls["rag"] == 0

    engine.chat("How was your weekend?")
    assert engine.last_conversational_context["conversation_type"] == "SMALL_TALK"
    assert calls["rag"] == 0
