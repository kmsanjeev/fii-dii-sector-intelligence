from __future__ import annotations

import time

from engines.ai.research.schemas import ResearchResult, ResearchSource
from engines.ai.chatbot.chat_engine import ChatEngine
from engines.common import config as cfg


def test_chat_engine_attachment_prompt_explains_reviewed_save_flow(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_SAVE_TO_KNOWLEDGE_ENABLED", True)

    engine = ChatEngine()
    captured: dict[str, str] = {}

    monkeypatch.setattr(engine, "_get_rag_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(engine, "_get_external_research_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(
        engine,
        "_active_providers",
        lambda: [
            {
                "name": "OpenAI",
                "env_var": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "extra_headers": {},
            }
        ],
    )
    monkeypatch.setattr(engine, "_get_client", lambda provider: object())

    def fake_run_turn(client, model, system_prompt, user_message, use_tools=True, voice_mode=False):
        captured["system_prompt"] = system_prompt
        return {"status": "ok", "reply": "I studied the uploaded material."}

    monkeypatch.setattr(engine, "_run_turn", fake_run_turn)

    reply = engine.chat(
        "Please study this book and store the knowledge.",
        attachment_context="[Attachment 1] name=book.pdf\nExtracted text here.",
    )

    assert reply == "I studied the uploaded material."
    assert "Do not say you cannot read uploaded files in general" in captured["system_prompt"]
    assert "permanent knowledge storage happens through the reviewed save flow" in captured["system_prompt"]


def test_chat_engine_cools_down_provider_after_auth_failure(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_CHAT_PROVIDER_HARD_FAILURE_COOLDOWN_S", 3600)

    engine = ChatEngine()
    engine._cooldowns.clear()
    providers = [
        {
            "name": "OpenAI",
            "env_var": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "extra_headers": {},
        },
        {
            "name": "Backup",
            "env_var": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "extra_headers": {},
        },
    ]

    monkeypatch.setattr(engine, "_active_providers", lambda: providers)
    monkeypatch.setattr(engine, "_get_client", lambda provider: object())
    monkeypatch.setattr(engine, "_get_rag_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(engine, "_get_external_research_context", lambda *args, **kwargs: "")

    def fake_run_turn(client, model, system_prompt, user_message, use_tools=True, voice_mode=False):
        if user_message == "hello" and model == "gpt-4o-mini" and "Incorrect API key" not in system_prompt:
            current = getattr(fake_run_turn, "calls", 0)
            fake_run_turn.calls = current + 1
            if current == 0:
                return {"status": "error", "error": "Error code: 401 - Incorrect API key provided"}
        return {"status": "ok", "reply": "Fallback provider answered."}

    monkeypatch.setattr(engine, "_run_turn", fake_run_turn)

    reply = engine.chat("hello")

    assert reply == "Fallback provider answered."
    assert engine._cooldowns["OpenAI"] > time.time()


def test_chat_engine_bounds_history_and_message_size(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_CHAT_MAX_HISTORY_MESSAGES", 4)
    monkeypatch.setattr(cfg, "VEDA_CHAT_MAX_HISTORY_CHARS", 120)
    monkeypatch.setattr(cfg, "VEDA_CHAT_MAX_MESSAGE_CHARS", 40)

    engine = ChatEngine()
    engine.history = [
        {"role": "user", "content": "A" * 80},
        {"role": "assistant", "content": "B" * 80},
        {"role": "user", "content": "C" * 80},
        {"role": "assistant", "content": "D" * 80},
        {"role": "user", "content": "E" * 80},
        {"role": "assistant", "content": "F" * 80},
    ]

    bounded = engine._bounded_history()

    assert len(bounded) <= 4
    assert sum(len(item["content"]) for item in bounded) <= 120
    assert all(len(item["content"]) <= 40 for item in bounded)


def test_chat_engine_prefers_unified_retrieval(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_ENABLED", True)

    engine = ChatEngine()

    class FakeUnifiedRetriever:
        def build_context(self, query: str, *, top_k: int = 4) -> str:
            return "Unified evidence below blends local platform intelligence."

    engine._retriever = FakeUnifiedRetriever()

    context = engine._get_rag_context("What is the market regime?", intent=None)

    assert "Unified evidence below blends local platform intelligence." in context


def test_chat_engine_shadow_mode_compares_unified_and_legacy(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_SHADOW_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_SHADOW_WRITE_LOG", True)
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_SHADOW_LOG", tmp_path / "shadow.jsonl")

    engine = ChatEngine()

    class FakeUnifiedRetriever:
        def build_context_bundle(self, query: str, *, top_k: int = 4):
            return {
                "context": "Unified evidence below blends local platform intelligence.",
                "summary": {
                    "used": True,
                    "source_count": 1,
                    "evidence_kinds": ["platform_signal_snapshot"],
                    "predictive_ml_count": 0,
                    "platform_snapshot_count": 1,
                    "approved_memory_count": 0,
                    "attachment_memory_count": 0,
                    "repo_count": 0,
                    "top_date": "2026-08-04",
                    "sources": [
                        {
                            "source_id": "platform_ethosltd",
                            "source_type": "platform_intelligence",
                            "source_label": "platform intelligence",
                            "evidence_kind": "platform_signal_snapshot",
                            "evidence_label": "platform signal snapshot",
                            "domain": "STOCK",
                            "title": "ETHOSLTD",
                            "entity": "ETHOSLTD",
                            "date": "2026-08-04",
                            "summary": "Fresh platform view says ETHOSLTD remains supportive.",
                            "rank": 1,
                        }
                    ],
                    "conflict_note": None,
                    "freshness_note": None,
                },
                "results": [],
            }

    class FakeReviewService:
        def search(self, query: str, *, top_k: int = 3):
            return [
                {
                    "doc_id": "reviewed_ethosltd",
                    "source_type": "user_reviewed",
                    "domain": "RESEARCH",
                    "entity": "ETHOSLTD saved note",
                    "text": "Older saved note says ETHOSLTD looked strong.",
                    "summary": "Saved ETHOSLTD note.",
                    "saved_at": "2026-08-03T09:00:00Z",
                }
            ]

        def build_context(self, query: str, *, top_k: int = 2) -> str:
            return "Reviewed knowledge below was explicitly approved by the user before saving."

    class FakeRepoService:
        def search(self, query: str, *, top_k: int = 3):
            return []

        def build_context(self, query: str, *, top_k: int = 2) -> str:
            return ""

    class FakeLegacyRetriever:
        def retrieve(self, query: str, domain=None):
            return [
                {
                    "doc_id": "platform_ethosltd",
                    "domain": "STOCK",
                    "entity": "ETHOSLTD",
                    "text": "Legacy platform view says ETHOSLTD still has support.",
                    "summary": "Legacy platform view.",
                    "effective_date": "2026-08-04",
                }
            ]

    engine._retriever = FakeUnifiedRetriever()
    engine._knowledge_review_service = FakeReviewService()
    engine._repo_capability_service = FakeRepoService()
    engine._legacy_retriever = FakeLegacyRetriever()

    context = engine._get_rag_context("What is the latest ETHOSLTD view?", intent=None)

    assert "Unified evidence below blends local platform intelligence." in context
    assert engine.last_retrieval_audit["shadow_enabled"] is True
    assert engine.last_retrieval_audit["configured_primary_mode"] == "unified"
    assert engine.last_retrieval_audit["resolved_primary_mode"] == "unified"
    assert engine.last_retrieval_audit["shadow_mode"] == "legacy"
    assert engine.last_retrieval_audit["overlap_count"] == 1
    assert (tmp_path / "shadow.jsonl").exists()


def test_chat_engine_shadow_mode_can_keep_legacy_primary(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_ENABLED", False)
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_SHADOW_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_SHADOW_WRITE_LOG", False)

    engine = ChatEngine()

    class FakeUnifiedRetriever:
        def build_context_bundle(self, query: str, *, top_k: int = 4):
            return {
                "context": "Unified evidence below blends local platform intelligence.",
                "summary": _empty_local_summary(),
                "results": [],
            }

    class FakeLegacyRetriever:
        def retrieve(self, query: str, domain=None):
            return [
                {
                    "doc_id": "legacy_market",
                    "domain": "MARKET",
                    "entity": "MARKET_REGIME",
                    "text": "Legacy market regime context.",
                    "summary": "Legacy market regime context.",
                    "effective_date": "2026-08-04",
                }
            ]

    engine._retriever = FakeUnifiedRetriever()
    engine._legacy_retriever = FakeLegacyRetriever()

    context = engine._get_rag_context("What is the market regime?", intent=None)

    assert "Legacy market regime context." in context
    assert engine.last_retrieval_audit["configured_primary_mode"] == "legacy"
    assert engine.last_retrieval_audit["resolved_primary_mode"] == "legacy"
    assert engine.last_retrieval_audit["shadow_mode"] == "unified"


def _empty_local_summary():
    return {
        "used": True,
        "source_count": 0,
        "evidence_kinds": [],
        "predictive_ml_count": 0,
        "platform_snapshot_count": 0,
        "approved_memory_count": 0,
        "attachment_memory_count": 0,
        "repo_count": 0,
        "top_date": None,
        "sources": [],
        "conflict_note": None,
        "freshness_note": None,
    }


def test_chat_engine_tracks_local_evidence_and_instructs_ml_separation(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_UNIFIED_RETRIEVAL_ENABLED", True)

    engine = ChatEngine()
    captured: dict[str, str] = {}

    class FakeUnifiedRetriever:
        def build_context_bundle(self, query: str, *, top_k: int = 4):
            return {
                "context": (
                    "Unified evidence below blends local platform intelligence.\n"
                    "- [1] predictive ML signal | source=platform intelligence | domain=STOCK | date=2026-08-04\n"
                    "  meaning: Higher model scores indicate a stronger local bullish continuation signal.\n"
                    "  reliability: Treat this as predictive scored evidence, not guaranteed fact."
                ),
                "summary": {
                    "used": True,
                    "source_count": 1,
                    "evidence_kinds": ["predictive_ml_signal"],
                    "predictive_ml_count": 1,
                    "platform_snapshot_count": 0,
                    "approved_memory_count": 0,
                    "attachment_memory_count": 0,
                    "repo_count": 0,
                    "top_date": "2026-08-04",
                    "sources": [
                        {
                            "source_id": "stock_ethosltd",
                            "source_type": "platform_intelligence",
                            "source_label": "platform intelligence",
                            "evidence_kind": "predictive_ml_signal",
                            "evidence_label": "predictive ML signal",
                            "domain": "STOCK",
                            "title": "ETHOSLTD",
                            "entity": "ETHOSLTD",
                            "date": "2026-08-04",
                            "freshness_class": "dated_snapshot",
                            "confidence": None,
                            "summary": "ETHOSLTD remains a high-scoring bullish continuation candidate.",
                            "attachment_name": None,
                            "repo_label": None,
                            "license_name": None,
                            "model_name": "bull_run_score_pipeline",
                            "model_version": "2026-08-04",
                            "score_meaning": "Higher model scores indicate a stronger local bullish continuation signal.",
                            "reliability_note": "Treat this as predictive scored evidence, not guaranteed fact.",
                            "rank": 1,
                        }
                    ],
                    "conflict_note": None,
                    "freshness_note": None,
                },
                "results": [],
            }

    engine._retriever = FakeUnifiedRetriever()
    monkeypatch.setattr(engine, "_get_external_research_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(
        engine,
        "_active_providers",
        lambda: [
            {
                "name": "OpenAI",
                "env_var": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "extra_headers": {},
            }
        ],
    )
    monkeypatch.setattr(engine, "_get_client", lambda provider: object())

    def fake_run_turn(client, model, system_prompt, user_message, use_tools=True, voice_mode=False):
        captured["system_prompt"] = system_prompt
        return {"status": "ok", "reply": "Local answer."}

    monkeypatch.setattr(engine, "_run_turn", fake_run_turn)

    reply = engine.chat("What is the local stock setup?")

    assert reply == "Local answer."
    assert engine.last_local_evidence["predictive_ml_count"] == 1
    assert engine.last_local_evidence["sources"][0]["title"] == "ETHOSLTD"
    assert "If a point comes from predictive ML evidence" in captured["system_prompt"]
    assert "Never imply that uploaded books, approved memory, or outside research changed the ML model itself" in captured["system_prompt"]


def test_chat_engine_marks_research_as_temporary_and_flags_memory_conflict(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    engine = ChatEngine()
    engine.last_local_evidence = {
        "used": True,
        "source_count": 1,
        "evidence_kinds": ["approved_memory"],
        "predictive_ml_count": 0,
        "platform_snapshot_count": 0,
        "approved_memory_count": 1,
        "attachment_memory_count": 0,
        "repo_count": 0,
        "top_date": "2026-08-04",
        "sources": [
            {
                "source_id": "saved_note_1",
                "source_type": "user_reviewed",
                "source_label": "approved memory",
                "evidence_kind": "approved_memory",
                "evidence_label": "approved memory",
                "domain": "RESEARCH",
                "title": "Saved banking note",
                "entity": "Banking setup",
                "date": "2026-08-03",
                "freshness_class": "durable_memory",
                "confidence": None,
                "summary": "Earlier saved note says the banking setup still looks strong and supportive.",
                "rank": 1,
            }
        ],
        "conflict_note": None,
        "freshness_note": None,
    }

    class FakeResearchService:
        def search(self, query: str, *, reason: str):
            return ResearchResult(
                provider="ddgs",
                query=query,
                reason=reason,
                used=True,
                sources=[
                    ResearchSource(
                        title="Fresh banking caution",
                        url="https://example.com/banking-caution",
                        snippet="Fresh outside report warns the banking setup looks weak and risky in the short term.",
                        source="Example News",
                        published_at="2026-08-04",
                    )
                ],
            )

    engine._research_service = FakeResearchService()

    context = engine._get_external_research_context(
        "What does outside research say about banking now?",
        intent=None,
        research_mode=True,
    )

    assert "External research stays temporary unless the user explicitly saves it through review." in context
    assert "Conflict note:" in context
    assert engine.last_research["temporary"] is True
    assert engine.last_research["save_requires_review"] is True
    assert "more cautious than the saved memory" in (engine.last_research["conflict_note"] or "")
