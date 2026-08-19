from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import chat as chat_router
from backend.routers import voice as voice_router
from engines.ai.capabilities import access_policy
from engines.ai.chatbot.chat_engine import TOOL_FUNCTIONS, ChatEngine, _tool_names_for_intent
from engines.ai.chatbot.intent_router import detect_intent
from engines.common import config as cfg


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(chat_router.router)
    app.include_router(voice_router.router)
    return TestClient(app)


def test_capability_guard_is_central_and_typed(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_CONVERSATIONAL_ACCESS_CONFIG", tmp_path / "access.json")
    access_policy.set_access("ATTACHMENTS", access_policy.DISABLED)
    with pytest.raises(access_policy.CapabilityAccessError) as exc:
        access_policy.require_capability_access("ATTACHMENTS")
    assert exc.value.code == "CONFIG_ACCESS_DENIED"
    assert exc.value.status_code == 403
    assert _client().post("/api/chat/attachments", files={"file": ("a.txt", b"x", "text/plain")}).status_code == 403


def test_capabilities_expose_voice_and_effective_policy(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_CONVERSATIONAL_ACCESS_CONFIG", tmp_path / "access.json")
    access_policy.set_access("VOICE", access_policy.DISABLED)
    payload = _client().get("/api/chat/capabilities").json()
    assert payload["voice_enabled"] is False
    assert next(row for row in payload["capability_states"] if row["capability_id"] == "VOICE")["effective_access"] == "DISABLED"
    assert _client().post("/api/voice/tts", json={"text": "hello", "language": "en"}).status_code == 403


def test_research_subject_context_preserves_specialist_routing():
    assert detect_intent("research latest NIFTY market sources").subject_intent == "MARKET"
    assert detect_intent("research latest evidence on D20").subject_intent == "ASTRO"
    assert detect_intent("research latest Muhurta sources").subject_intent == "MUHURTA"


def test_domain_tool_sets_are_bounded_and_cover_registry():
    assert _tool_names_for_intent("GENERAL") == set()
    assert _tool_names_for_intent("ASTRO") == set()
    assert _tool_names_for_intent("MUHURTA") == set()
    assert _tool_names_for_intent("RESEARCH", "MARKET") == _tool_names_for_intent("MARKET")
    assert _tool_names_for_intent("RESEARCH", "ASTRO") == set()
    scoped = set().union(*(_tool_names_for_intent(intent) or set() for intent in (
        "KUNDLI", "MARKET", "SECTOR", "STOCK", "CORPORATE", "ASTRO_FINANCE",
    )))
    assert scoped == set(TOOL_FUNCTIONS)


def test_execution_guard_blocks_forbidden_tool_call():
    engine = ChatEngine()
    engine._tool_names_for_turn = set()
    called = []
    original = TOOL_FUNCTIONS["get_market_regime"]
    TOOL_FUNCTIONS["get_market_regime"] = lambda **kwargs: called.append(kwargs) or {"unexpected": True}
    try:
        result = engine._call_tool("get_market_regime", {})
    finally:
        TOOL_FUNCTIONS["get_market_regime"] = original
    assert result["code"] == "OUT_OF_SCOPE_TOOL_CALL"
    assert called == []
    assert engine.last_telemetry["event"] == "OUT_OF_SCOPE_TOOL_CALL"
