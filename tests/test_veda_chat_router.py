from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import chat as chat_router
import engines.ai.chat_history as history_pkg
import engines.ai.knowledge.review_service as knowledge_pkg
import engines.ai.research as research_pkg
from engines.ai.chat_history.service import ChatHistoryService
from engines.common import config as cfg


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(chat_router.router)
    return TestClient(app)


def test_chat_capabilities_reports_runtime_research_capabilities(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_AUTO_FOR_RESEARCH_INTENT", True)
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_INTAKE_ENABLED", True)

    class FakeResearchService:
        def capabilities(self) -> dict:
            return {
                "research_enabled": True,
                "provider_available": True,
                "research_runtime_ready": True,
                "default_provider": "ddgs",
                "attachments_enabled": True,
                "save_to_knowledge_enabled": True,
                "mcp_enabled": True,
                "mcp_server_names": ["github", "ddgs"],
            }

    monkeypatch.setattr(research_pkg, "get_research_service", lambda: FakeResearchService())

    response = _make_client().get("/api/chat/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["research_enabled"] is True
    assert payload["research_provider_available"] is True
    assert payload["research_runtime_ready"] is True
    assert payload["attachments_enabled"] is True
    assert payload["save_to_knowledge_enabled"] is True
    assert payload["mcp_enabled"] is True
    assert payload["mcp_server_names"] == ["github", "ddgs"]
    assert payload["supported_attachment_mime_prefixes"] == [
        "application/pdf",
        "image/",
        "text/",
        "application/json",
    ]


def test_chat_capabilities_fall_back_to_cfg_when_research_service_errors(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_ENABLED", False)
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_PROVIDER", "ddgs")
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_AUTO_FOR_RESEARCH_INTENT", False)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENTS_ENABLED", False)
    monkeypatch.setattr(cfg, "VEDA_SAVE_TO_KNOWLEDGE_ENABLED", False)
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_INTAKE_ENABLED", False)
    monkeypatch.setattr(cfg, "VEDA_MCP_ENABLED", False)
    monkeypatch.setattr(
        research_pkg,
        "get_research_service",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = _make_client().get("/api/chat/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["research_enabled"] is False
    assert payload["research_provider_available"] is False
    assert payload["research_runtime_ready"] is False
    assert payload["default_research_provider"] == "ddgs"
    assert payload["attachments_enabled"] is False
    assert payload["mcp_enabled"] is False
    assert payload["mcp_server_names"] == []


def test_chat_rejects_inline_attachments_when_feature_is_disabled(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENTS_ENABLED", False)

    response = _make_client().post(
        "/api/chat",
        json={
            "message": "Please study this file.",
            "attachments": [
                {
                    "name": "note.pdf",
                    "mime_type": "application/pdf",
                    "storage_key": "note.pdf",
                }
            ],
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Veda attachments are disabled."


def test_chat_attachment_upload_rejects_when_feature_is_disabled(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENTS_ENABLED", False)

    response = _make_client().post(
        "/api/chat/attachments",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Veda attachments are disabled."


def test_chat_endpoint_returns_local_evidence_summary(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeEngine:
        last_symbols = ["ETHOSLTD"]
        last_flag = {"flagged": False, "reason": None}
        last_research = {
            "requested": False,
            "used": False,
            "provider": None,
            "reason": "local_first",
            "source_count": 0,
            "cached": False,
            "error": None,
            "sources": [],
        }
        last_local_evidence = {
            "used": True,
            "source_count": 2,
            "evidence_kinds": ["predictive_ml_signal", "platform_signal_snapshot"],
            "predictive_ml_count": 1,
            "platform_snapshot_count": 1,
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
                    "summary": "ETHOSLTD still scores well on local signals.",
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
        }

        def chat(self, *args, **kwargs):
            return "Local answer."

    monkeypatch.setattr(chat_router, "_get_or_create_session", lambda session_id: ("session-1", FakeEngine()))

    response = _make_client().post("/api/chat", json={"message": "What is the stock setup?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_evidence"]["used"] is True
    assert payload["local_evidence"]["predictive_ml_count"] == 1
    assert payload["local_evidence"]["top_date"] == "2026-08-04"
    assert payload["local_evidence"]["sources"][0]["title"] == "ETHOSLTD"


def test_chat_endpoint_returns_research_governance_meta(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeEngine:
        last_symbols = []
        last_flag = {"flagged": False, "reason": None}
        last_research = {
            "requested": True,
            "used": True,
            "provider": "ddgs",
            "reason": "explicit_research_mode",
            "source_count": 1,
            "cached": False,
            "error": None,
            "sources": [
                {
                    "title": "Fresh caution note",
                    "url": "https://example.com/caution",
                    "snippet": "Outside report looks more cautious than older saved memory.",
                    "source": "Example News",
                    "published_at": "2026-08-04",
                    "kind": "text",
                }
            ],
            "temporary": True,
            "save_requires_review": True,
            "conflict_note": "Outside research looks more cautious than the saved memory already stored in Veda.",
            "governance_note": "Outside research stays temporary unless you explicitly save it through review.",
        }
        last_local_evidence = {
            "used": False,
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

        def chat(self, *args, **kwargs):
            return "Research-backed answer."

    monkeypatch.setattr(chat_router, "_get_or_create_session", lambda session_id: ("session-2", FakeEngine()))

    response = _make_client().post(
        "/api/chat",
        json={"message": "Research this topic for me.", "research_mode": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["research"]["temporary"] is True
    assert payload["research"]["save_requires_review"] is True
    assert "more cautious than the saved memory" in payload["research"]["conflict_note"]


def test_chat_endpoint_returns_retrieval_audit_meta(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeEngine:
        last_symbols = []
        last_flag = {"flagged": False, "reason": None}
        last_research = {
            "requested": False,
            "used": False,
            "provider": None,
            "reason": "local_first",
            "source_count": 0,
            "cached": False,
            "error": None,
            "sources": [],
        }
        last_local_evidence = {
            "used": True,
            "source_count": 1,
            "evidence_kinds": ["platform_signal_snapshot"],
            "predictive_ml_count": 0,
            "platform_snapshot_count": 1,
            "approved_memory_count": 0,
            "attachment_memory_count": 0,
            "repo_count": 0,
            "top_date": "2026-08-04",
            "sources": [],
            "conflict_note": None,
            "freshness_note": None,
        }
        last_retrieval_audit = {
            "shadow_enabled": True,
            "configured_primary_mode": "legacy",
            "resolved_primary_mode": "legacy",
            "primary_used": True,
            "primary_source_count": 1,
            "primary_attribution_quality": 0.833,
            "primary_duplicate_noise": 0.0,
            "shadow_mode": "unified",
            "shadow_used": True,
            "shadow_source_count": 2,
            "shadow_attribution_quality": 1.0,
            "shadow_duplicate_noise": 0.0,
            "overlap_count": 1,
            "overlap_rate": 0.5,
            "only_in_primary": [],
            "only_in_shadow": ["ETHOSLTD"],
            "notes": ["Shadow retrieval kept richer source attribution than the primary path."],
            "primary_error": None,
            "shadow_error": None,
        }

        def chat(self, *args, **kwargs):
            return "Shadow-audited answer."

    monkeypatch.setattr(chat_router, "_get_or_create_session", lambda session_id: ("session-3", FakeEngine()))

    response = _make_client().post("/api/chat", json={"message": "What is the latest local view?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_audit"]["shadow_enabled"] is True
    assert payload["retrieval_audit"]["configured_primary_mode"] == "legacy"
    assert payload["retrieval_audit"]["shadow_mode"] == "unified"
    assert payload["retrieval_audit"]["only_in_shadow"] == ["ETHOSLTD"]


def test_chat_saved_sessions_round_trip_and_isolate_by_client_header(monkeypatch, tmp_dir):
    monkeypatch.setattr(history_pkg, "get_chat_history_service", lambda: ChatHistoryService(storage_dir=tmp_dir))

    client = _make_client()
    session_payload = {
        "id": "chat-1",
        "title": "Imported chat",
        "messages": [
            {
                "role": "user",
                "content": "Please keep this history.",
                "ts": 123,
            }
        ],
        "backendSessionId": "srv-1",
        "createdAt": 120,
        "updatedAt": 123,
    }

    upsert = client.put(
        "/api/chat/sessions/chat-1",
        headers={"X-Veda-Client-Id": "browser-a"},
        json=session_payload,
    )

    assert upsert.status_code == 200
    assert upsert.json()["id"] == "chat-1"

    list_a = client.get("/api/chat/sessions", headers={"X-Veda-Client-Id": "browser-a"})
    list_b = client.get("/api/chat/sessions", headers={"X-Veda-Client-Id": "browser-b"})

    assert list_a.status_code == 200
    assert list_a.json()["sessions"][0]["title"] == "Imported chat"
    assert list_b.status_code == 200
    assert list_b.json()["sessions"] == []


def test_chat_saved_sessions_delete_endpoints(monkeypatch, tmp_dir):
    monkeypatch.setattr(history_pkg, "get_chat_history_service", lambda: ChatHistoryService(storage_dir=tmp_dir))

    client = _make_client()
    headers = {"X-Veda-Client-Id": "browser-a"}

    payload_one = {
        "id": "chat-1",
        "title": "One",
        "messages": [{"role": "user", "content": "A", "ts": 1}],
        "backendSessionId": "srv-1",
        "createdAt": 1,
        "updatedAt": 1,
    }
    payload_two = {
        "id": "chat-2",
        "title": "Two",
        "messages": [{"role": "user", "content": "B", "ts": 2}],
        "backendSessionId": "srv-2",
        "createdAt": 2,
        "updatedAt": 2,
    }

    assert client.put("/api/chat/sessions/chat-1", headers=headers, json=payload_one).status_code == 200
    assert client.put("/api/chat/sessions/chat-2", headers=headers, json=payload_two).status_code == 200

    deleted_one = client.delete("/api/chat/sessions/chat-1", headers=headers)
    deleted_all = client.delete("/api/chat/sessions", headers=headers)
    remaining = client.get("/api/chat/sessions", headers=headers)

    assert deleted_one.status_code == 200
    assert deleted_one.json()["status"] == "deleted"
    assert deleted_all.status_code == 200
    assert deleted_all.json()["count"] == 1
    assert remaining.json()["sessions"] == []


def test_chat_knowledge_draft_returns_existing_match_recommendation(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_SAVE_TO_KNOWLEDGE_ENABLED", True)

    class FakeKnowledgeService:
        def create_draft(self, **kwargs):
            class Draft:
                def to_dict(self):
                    return {
                        "draft_id": "draft-1",
                        "title": "Research: Banking memory check",
                        "summary": "A similar banking memory already exists.",
                        "facts": ["Banking rotation remains strong."],
                        "tags": ["research", "banking"],
                        "raw_question": kwargs["question"],
                        "raw_answer": kwargs["answer"],
                        "intent": kwargs["intent"],
                        "session_id": kwargs["session_id"],
                        "created_at": "2026-08-04T10:00:00Z",
                        "sources": [],
                        "existing_matches": [
                            {
                                "doc_id": "veda_review_existing",
                                "title": "Banking rotation and FII support",
                                "summary": "Existing saved banking note.",
                                "saved_at": "2026-08-04T09:00:00Z",
                                "memory_type": "reviewed_note",
                                "overlap_score": 14,
                                "semantic_score": 88,
                                "reason": "This saved memory already overlaps strongly with the new material.",
                                "exact_duplicate": False,
                            }
                        ],
                        "suggested_action": "discard",
                        "suggestion_reason": "A strong saved memory already exists on this same topic.",
                        "status": "draft",
                    }

            return Draft()

    monkeypatch.setattr(knowledge_pkg, "get_knowledge_review_service", lambda: FakeKnowledgeService())

    response = _make_client().post(
        "/api/chat/knowledge/draft",
        json={
            "question": "Review the same banking topic again.",
            "answer": "Banking rotation and FII support still look strong.",
            "intent": "SECTOR",
            "session_id": "session-1",
            "research": {"used": False, "sources": []},
            "attachments": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["suggested_action"] == "discard"
    assert payload["existing_matches"][0]["overlap_score"] == 14
    assert payload["existing_matches"][0]["title"] == "Banking rotation and FII support"


def test_chat_knowledge_approve_passes_explicit_decision(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_SAVE_TO_KNOWLEDGE_ENABLED", True)
    captured: dict[str, str | None] = {}

    class FakeKnowledgeService:
        def approve(self, draft_id: str, **kwargs):
            captured["draft_id"] = draft_id
            captured["decision"] = kwargs.get("decision")
            return {
                "draft_id": draft_id,
                "doc_id": "veda_review_existing",
                "saved_at": "2026-08-04T10:15:00Z",
                "title": kwargs["title"],
                "status": "approved",
                "duplicate": False,
                "attachment_doc_count": 1,
                "attachment_chunk_count": 2,
                "decision": kwargs.get("decision"),
                "merged_into_doc_id": "veda_review_existing",
            }

    monkeypatch.setattr(knowledge_pkg, "get_knowledge_review_service", lambda: FakeKnowledgeService())

    response = _make_client().post(
        "/api/chat/knowledge/draft/draft-1/approve",
        json={
            "title": "Merged memory",
            "summary": "Merge this into the saved note.",
            "facts": ["New Mercury timing note."],
            "tags": ["astrology", "timing"],
            "decision": "merge",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "draft_id": "draft-1",
        "decision": "merge",
    }
    assert response.json()["decision"] == "merge"


def test_chat_knowledge_draft_delete_endpoint_discards_review(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_SAVE_TO_KNOWLEDGE_ENABLED", True)

    class FakeKnowledgeService:
        def discard(self, draft_id: str):
            assert draft_id == "draft-1"
            return {
                "draft_id": draft_id,
                "status": "discarded",
            }

    monkeypatch.setattr(knowledge_pkg, "get_knowledge_review_service", lambda: FakeKnowledgeService())

    response = _make_client().delete("/api/chat/knowledge/draft/draft-1")

    assert response.status_code == 200
    assert response.json() == {
        "draft_id": "draft-1",
        "status": "discarded",
    }
