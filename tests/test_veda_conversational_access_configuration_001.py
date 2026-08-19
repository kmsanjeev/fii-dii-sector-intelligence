from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from engines.ai.capabilities import access_policy
from engines.ai.chatbot.intent_router import detect_intent, get_system_prompt
from engines.common import config as cfg
from backend.routers import chat as chat_router


def test_unmatched_messages_use_general_without_market_identity():
    for message in (
        "Explain photosynthesis in simple terms.",
        "Write a polite leave request for tomorrow.",
        "I want a quiet weekend plan.",
        "I feel lonely and need someone to talk to.",
        "How do I fix a Python race condition?",
    ):
        intent = detect_intent(message)
        assert intent.intent_type == "GENERAL"
        prompt = get_system_prompt(intent)
        assert "Capital Flow Intelligence Assistant" not in prompt
        assert "ordinary question directly" in prompt


def test_specialist_and_research_routes_remain_explicit():
    assert detect_intent("What are the latest FII and DII flows?").intent_type == "MARKET"
    assert detect_intent("Which sector is showing accumulation?").intent_type == "MARKET"
    assert detect_intent("What does D9 mean in Jyotish?").intent_type == "ASTRO"
    assert detect_intent("What is D20 validation status?").intent_type == "ASTRO"
    assert detect_intent("Please research the latest evidence and compare sources.").intent_type == "RESEARCH"


def test_greeting_detection_does_not_match_substrings():
    assert detect_intent("What does D9 mean in Jyotish?").intent_type == "ASTRO"
    assert detect_intent("Hi Veda").intent_type == "GREETING"


def test_access_policy_defaults_and_atomic_persistence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "conversation_access.json"
    monkeypatch.setattr(cfg, "VEDA_CONVERSATIONAL_ACCESS_CONFIG", path)
    states = access_policy.get_states()
    assert states
    assert all(row["admin_access_state"] == "ENABLED" for row in states)
    assert access_policy.get_state("GENERAL_CHAT").effective_access == "ENABLED"
    assert access_policy.resolve_intent("GENERAL").capability_id == "GENERAL_CHAT"
    assert access_policy.resolve_intent("ASTRO").capability_id == "ASTROLOGY"

    access_policy.set_access("MARKET_INTELLIGENCE", access_policy.DISABLED)
    assert access_policy.get_state("MARKET_INTELLIGENCE").effective_access == "DISABLED"
    assert path.exists()
    assert access_policy.resolve_intent("MARKET").effective_answer_mode == "UNAVAILABLE"
    assert access_policy.resolve_intent("GENERAL").effective_access == "ENABLED"

    with pytest.raises(ValueError):
        access_policy.set_access("GENERAL_CHAT", access_policy.DISABLED)
    access_policy.reset_defaults()
    assert access_policy.get_state("MARKET_INTELLIGENCE").effective_access == "ENABLED"


def test_runtime_policy_does_not_promote_maturity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cfg, "VEDA_CONVERSATIONAL_ACCESS_CONFIG", tmp_path / "access.json")
    state = access_policy.get_state("ASTROLOGY")
    assert state.capability_maturity == "IMPLEMENTED_WITH_CONDITIONS"
    assert state.effective_answer_mode == "QUALIFIED"


def test_disabled_specialist_returns_configuration_denial_before_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_CONVERSATIONAL_ACCESS_CONFIG", tmp_path / "access.json")
    access_policy.set_access("MARKET_INTELLIGENCE", access_policy.DISABLED)
    from engines.ai.chatbot.chat_engine import ChatEngine

    engine = ChatEngine()
    monkeypatch.setattr(engine, "_active_providers", lambda: [])
    reply = engine.chat("What are the latest FII flows?")
    assert "disabled by configuration" in reply
    assert engine.last_telemetry["event"] == "CONFIG_ACCESS_DENIED"
    assert engine.last_access_decision["effective_access"] == "DISABLED"


def test_capability_api_exposes_access_runtime_maturity_and_protected_safety(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(cfg, "VEDA_CONVERSATIONAL_ACCESS_CONFIG", tmp_path / "access.json")
    app = FastAPI()
    app.include_router(chat_router.router)
    client = TestClient(app)

    response = client.get("/api/chat/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_version"] == access_policy.POLICY_VERSION
    assert any(row["capability_id"] == "GENERAL_CHAT" for row in payload["capability_states"])
    assert payload["protected_safeguards"]["state"] == "ACTIVE"

    config = client.get("/api/veda/configuration")
    assert config.status_code == 200
    updated = client.put("/api/veda/configuration/access/MARKET_INTELLIGENCE", json={"state": "DISABLED"})
    assert updated.status_code == 200
    assert next(row for row in updated.json()["capabilities"] if row["capability_id"] == "MARKET_INTELLIGENCE")["effective_access"] == "DISABLED"
    restored = client.post("/api/veda/configuration/reset")
    assert restored.status_code == 200
