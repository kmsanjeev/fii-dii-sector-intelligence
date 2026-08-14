import json
from pathlib import Path

from engines.ai.chatbot.conversation_intelligence import analyze_conversation
from engines.ai.chatbot.response_adaptation import (
    LEVELS,
    adaptation_guidance,
    build_adaptation_profile,
)


def _benchmark():
    path = Path("tests/fixtures/veda_comm002_adaptation_benchmark.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _profile(record, history=None):
    context = analyze_conversation(record["text"], history=history)
    return context, build_adaptation_profile(context, user_message=record["text"], history=history)


def test_comm002_profile_contract_is_bounded_and_serializable():
    context, profile = _profile(_benchmark()[28])
    payload = profile.to_dict()
    for key in (
        "conversation_type", "primary_intent", "tone", "formality", "directness",
        "domain", "domain_proficiency", "language", "response_depth", "response_strategy",
        "explanation_level", "idiom_usage_level", "slang_usage_level", "jargon_usage_level",
        "clarification_need", "high_stakes_state", "repetition_avoidance",
    ):
        assert key in payload
    assert profile.response_depth in LEVELS["depth"]
    assert profile.formality in LEVELS["formality"]
    assert profile.directness in LEVELS["directness"]


def test_comm002_adaptation_benchmark_meets_property_gate():
    mapping = {
        "depth": "response_depth", "warmth": "warmth_level", "directness": "directness",
        "formality": "formality", "technicality": "technicality_level",
        "explanation": "explanation_level", "structure": "structure_preference",
        "playfulness": "playfulness_level", "reassurance": "reassurance_level",
        "idiom": "idiom_usage_level",
    }
    passed = 0
    for record in _benchmark():
        context, profile = _profile(record)
        ok = all(
            getattr(profile, mapping.get(key, key), None) == expected
            for key, expected in record.items()
            if key not in {"id", "text", "type", "language", "domain", "high_stakes", "clarification"}
        )
        ok &= record.get("type") == "UNKNOWN" or profile.conversation_type == record["type"]
        ok &= not record.get("domain") or profile.domain == record["domain"]
        ok &= not record.get("high_stakes") or profile.high_stakes_state == record["high_stakes"]
        ok &= not record.get("clarification") or profile.clarification_need == record["clarification"]
        passed += int(ok)
        assert context.conversation_type
    assert len(_benchmark()) >= 60
    assert passed / len(_benchmark()) >= 0.90


def test_comm002_explicit_style_overrides_are_strong_and_deterministic():
    cases = (
        ("Be brief and direct.", "CONCISE", "VERY_DIRECT"),
        ("Explain deeply, step by step.", "DEEP", "BALANCED"),
        ("Talk casually and keep it brief.", "CONCISE", "BALANCED"),
        ("Please answer in Hindi.", "STANDARD", "BALANCED"),
    )
    for message, depth, directness in cases:
        _, profile = _profile({"text": message}, history=None)
        assert profile.response_depth == depth
        assert profile.directness == directness
    _, hindi = _profile({"text": "Please answer in Hindi."})
    assert hindi.language == "HI"


def test_comm002_high_stakes_boundary_is_preserved():
    for message, state in (
        ("I am worried about this medical symptom.", "HEALTH"),
        ("I lost money in this investment and feel scared.", "FINANCE"),
    ):
        _, profile = _profile({"text": message})
        assert profile.high_stakes_state == state
        assert profile.playfulness_level == "NONE"
        assert profile.idiom_usage_level == "NONE"
        assert profile.slang_usage_level == "NONE"
        assert profile.reassurance_level == "NONE"
        assert "High-stakes context" in adaptation_guidance(profile)


def test_comm002_proficiency_and_domain_change_presentation_not_facts():
    novice = _profile({"text": "What is D9? Explain like a beginner."})[1]
    expert = _profile({"text": "D9 lord is afflicted and MD/AD activation is weak."})[1]
    assert novice.domain == expert.domain == "JYOTISHA"
    assert novice.explanation_level == "TEACHING"
    assert expert.technicality_level == "ADVANCED"
    assert novice.technicality_level != expert.technicality_level


def test_comm002_repetition_control_uses_recent_history():
    history = [
        {"role": "assistant", "content": "Based on your chart, the period looks mixed. Would you like me to continue?"},
        {"role": "assistant", "content": "Based on your chart, the period looks mixed. Would you like me to continue?"},
        {"role": "user", "content": "Please explain the timing."},
    ]
    profile = _profile({"text": "Give me a concise answer."}, history=history)[1]
    assert profile.repetition_avoidance == "STRICT"
    assert profile.repeated_openings
    assert profile.repeated_closings
    assert "Vary the response entry and close" in adaptation_guidance(profile)


def test_comm002_ambiguous_context_requests_only_material_clarification():
    context = analyze_conversation("I am fine.")
    profile = build_adaptation_profile(context, user_message="I am fine.")
    assert profile.ambiguity_state == "AMBIGUOUS"
    assert profile.clarification_need == "ASK_IF_MATERIAL"
    assert "one concise clarification" in adaptation_guidance(profile)


def test_comm002_fallback_guidance_preserves_existing_response_owner():
    profile = build_adaptation_profile(analyze_conversation("A normal question."), user_message="A normal question.")
    guidance = adaptation_guidance(profile)
    assert "Adapt presentation only" in guidance
    assert "preserve facts" in guidance
    assert "understand does not mean mirror" in guidance
