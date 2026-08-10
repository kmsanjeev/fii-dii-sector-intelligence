from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth.middleware import AuthMiddleware
from backend.routers import research as research_router
from engines.ai.research.platform.service import ResearchPlatformService


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )


def _client(service: ResearchPlatformService, monkeypatch) -> TestClient:
    monkeypatch.setattr(research_router, "get_research_platform_service", lambda: service)
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(research_router.router)
    return TestClient(app)


def test_research_platform_admin_routes_operate_under_dev_loopback(tmp_dir, monkeypatch):
    service = _service(tmp_dir)
    client = _client(service, monkeypatch)

    mission_response = client.post(
        "/api/research/missions",
        json={
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "API mission",
            "objective": "Create a mission through the API.",
            "research_type": "CLAIM_VALIDATION",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": ["initial"],
            },
        },
    )
    assert mission_response.status_code == 200
    mission_id = mission_response.json()["mission_id"]

    domains = client.get("/api/research/domains")
    dashboard = client.get("/api/research/dashboard")
    run = client.post(f"/api/research/missions/{mission_id}/trigger")
    candidates = client.get("/api/research/candidates")
    ledger = client.get("/api/research/ledger?limit=20")

    assert domains.status_code == 200
    assert dashboard.status_code == 200
    assert run.status_code == 200
    assert candidates.status_code == 200
    assert ledger.status_code == 200
    assert dashboard.json()["research_status"] in {"HEALTHY", "DEGRADED"}
    assert candidates.json()["candidates"]


def test_research_platform_admin_decision_endpoint_requires_admin_role(tmp_dir, monkeypatch):
    service = _service(tmp_dir)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "Security mission",
            "objective": "Generate a candidate for auth enforcement.",
            "research_type": "CLAIM_VALIDATION",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": ["initial"],
            },
        }
    )
    service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    candidate_id = service.list_candidates()[0].candidate_id

    monkeypatch.setattr(research_router, "get_research_platform_service", lambda: service)
    from backend.auth import middleware as auth_middleware

    monkeypatch.setattr(auth_middleware, "is_auth_enabled", lambda: True)
    monkeypatch.setattr(
        auth_middleware,
        "_resolve_user",
        lambda request: auth_middleware.User(id="analyst", email="analyst@example.com", role="analyst", active=True, created_at=""),
    )

    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(research_router.router)
    client = TestClient(app)

    response = client.post(
        f"/api/research/candidates/{candidate_id}/decision",
        json={"action": "APPROVE", "reason": "Should fail for analyst."},
    )

    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    assert "read-only" in detail or "admin" in detail
