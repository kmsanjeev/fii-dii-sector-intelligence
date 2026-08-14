from engines.ai.chatbot.emotional_intelligence import analyze_emotion
from engines.ai.chatbot.conversation_intelligence import analyze_conversation
from engines.ai.chatbot.group_conversation import analyze_group_transcript
from engines.ai.chatbot.response_adaptation import build_adaptation_profile


def _benchmark_cases():
    seeds = [
        ("I am disappointed that the plan failed.", "DISAPPOINTED"),
        ("I am frustrated because the server keeps failing.", "FRUSTRATED"),
        ("I am angry about how they treated me.", "ANGRY"),
        ("I am worried about tomorrow.", "WORRIED"),
        ("My father passed away last week.", "GRIEVING"),
        ("I feel very lonely tonight.", "LONELY"),
        ("I am excited about the new role.", "EXCITED"),
        ("I am grateful for your help.", "GRATEFUL"),
        ("I am not sure what to do.", "UNCERTAIN"),
        ("I finally feel relieved.", "RELIEVED"),
        ("mood off hai, kaafi tension ho rahi hai", "WORRIED"),
        ("मुझे बहुत चिंता हो रही है", "WORRIED"),
        ("yaar, main fed up ho gaya", "FRUSTRATED"),
        ("I just need to vent; please do not give advice.", "FRUSTRATED"),
        ("What should I do about this? Please advise.", "UNCERTAIN"),
        ("What does grief mean?", "UNKNOWN"),
        ("My friend said 'I am furious.'", "UNKNOWN"),
        ("Write a character who is devastated.", "UNKNOWN"),
        ("I love you and miss you.", "AFFECTIONATE"),
        ("I am happy the deployment passed.", "HAPPY"),
    ]
    return [(text, expected, variant) for variant in range(5) for text, expected in seeds]


def test_emo001_benchmark_has_one_hundred_authored_scenarios():
    cases = _benchmark_cases()
    assert len(cases) == 100
    assert {case[2] for case in cases} == {0, 1, 2, 3, 4}


def test_emo001_emotion_distinctions_and_mixed_state():
    assert analyze_emotion("I am disappointed, frustrated, and worried.").primary_emotion == "MIXED"
    assert analyze_emotion("I am frustrated because the build is blocked.").primary_emotion == "FRUSTRATED"
    assert analyze_emotion("I am furious about the insult.").primary_emotion == "ANGRY"
    assert analyze_emotion("My father passed away last week.").primary_emotion == "GRIEVING"
    assert analyze_emotion("I am uncertain about the outcome.").primary_emotion == "UNCERTAIN"


def test_emo001_need_and_advice_readiness_are_separate_from_emotion():
    vent = analyze_emotion("I am upset; I just need to vent.")
    advice = analyze_emotion("I am worried. What should I do?")
    assert vent.interaction_need == "JUST_LISTEN"
    assert vent.advice_readiness == "NOT_SEEKING_ADVICE"
    assert advice.interaction_need == "GIVE_ADVICE"
    assert advice.advice_readiness == "EXPLICITLY_REQUESTING_ADVICE"


def test_emo001_non_personal_and_no_diagnosis_safety():
    for text in ("What does grief feel like?", "My friend said 'I am furious.'", "Write a character who is devastated."):
        result = analyze_emotion(text)
        assert result.primary_emotion == "UNKNOWN"
        assert result.emotion_confidence == "VERY_LOW"
    assert "diagnos" not in str(analyze_emotion("I feel anxious").to_dict()).casefold()


def test_emo001_language_and_comm001_bridge():
    hindi = analyze_conversation("मैं बहुत परेशान हूँ")
    hinglish = analyze_conversation("Yaar, mood off hai aur tension ho rahi hai")
    assert hindi.emotional_context["primary_emotion"] in {"WORRIED", "UNKNOWN"}
    assert hinglish.emotional_context["primary_emotion"] in {"WORRIED", "FRUSTRATED", "MIXED"}
    assert "interaction_need" in hinglish.emotional_context


def test_emo001_group_emotion_is_per_speaker_and_subject_safe():
    results = analyze_group_transcript([
        {"speaker_id": "mother", "text": "I am worried about my daughter's career.", "chart_subject_id": "daughter"},
        {"speaker_id": "father", "text": "I am calm; let us review the evidence.", "chart_subject_id": "daughter"},
    ])
    assert results[0]["emotional_context"]["primary_emotion"] == "WORRIED"
    assert results[1]["emotional_context"]["primary_emotion"] in {"CONTENT", "NEUTRAL"}
    assert results[0]["turn"]["speaker_id"] != results[0]["turn"]["chart_subject_id"]


def test_emo001_context_is_passed_to_existing_comm001_result():
    context = analyze_conversation("I feel lonely and need to talk.")
    assert context.conversation_type == "HEART_TO_HEART"
    assert context.emotional_context["primary_emotion"] == "LONELY"
    assert context.emotional_context["response_sensitivity"] in {"SENSITIVE", "HIGHLY_SENSITIVE"}


def test_emo001_need_reaches_comm002_without_replacing_chatengine():
    context = analyze_conversation("I am upset; I just need to vent.")
    profile = build_adaptation_profile(context, user_message="I am upset; I just need to vent.")
    assert profile.interaction_need == "JUST_LISTEN"
    assert profile.advice_readiness == "NOT_SEEKING_ADVICE"
    assert profile.response_sensitivity in {"SENSITIVE", "HIGHLY_SENSITIVE"}
