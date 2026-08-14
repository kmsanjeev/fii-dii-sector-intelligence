from engines.ai.chatbot.conversation_intelligence import ConversationContext, prompt_guidance


def test_evaluation_baseline_omits_only_adaptive_guidance():
    context = ConversationContext(
        conversation_type="SHOP_TALK",
        primary_intent="REQUEST_EXPLANATION",
        language="ENGLISH",
        domain="SOFTWARE",
        user_proficiency="EXPERT",
    )

    baseline = prompt_guidance(context, user_message="Explain the migration risk", include_adaptation=False)
    adaptive = prompt_guidance(context, user_message="Explain the migration risk", include_adaptation=True)

    assert "CONVERSATIONAL CONTEXT" in baseline
    assert "RESPONSE ADAPTATION PROFILE" not in baseline
    assert "RESPONSE ADAPTATION PROFILE" in adaptive
    assert "Preserve safety, factual boundaries, and uncertainty." in baseline
    assert "Preserve safety, factual boundaries, and uncertainty." in adaptive
