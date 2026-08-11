from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth.middleware import AuthMiddleware
from backend.routers import research as research_router
from engines.ai.knowledge.astrology_capability_framework import JyotishaCapabilityLifecycleService
from engines.ai.research.platform.service import ResearchPlatformService


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"


def _client(capability_service: JyotishaCapabilityLifecycleService, research_service: ResearchPlatformService, monkeypatch) -> TestClient:
    monkeypatch.setattr(research_router, "get_jyotisha_capability_lifecycle_service", lambda: capability_service)
    monkeypatch.setattr(research_router, "get_research_platform_service", lambda: research_service)
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(research_router.router)
    return TestClient(app)


def test_p013_capability_admin_routes_return_registry_and_detail(tmp_dir, monkeypatch):
    capability_service = JyotishaCapabilityLifecycleService()
    research_service = ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )
    client = _client(capability_service, research_service, monkeypatch)

    listing = client.get("/api/research/capabilities", params={"status": "ACTIVATION_READY", "search": "dignity"})
    detail = client.get("/api/research/capabilities/VEDA-CAP-DIGNITY-000001")

    assert listing.status_code == 200
    assert detail.status_code == 200
    listing_payload = listing.json()
    detail_payload = detail.json()

    assert listing_payload["returned"] >= 1
    assert listing_payload["capabilities"][0]["capability_id"] == "VEDA-CAP-DIGNITY-000001"
    assert detail_payload["capability"]["capability_id"] == "VEDA-CAP-DIGNITY-000001"
    assert detail_payload["lifecycle"]["research_gate"]["decision"] == "PASS"
    assert detail_payload["research_mission_proposal"] is None
    assert detail_payload["transition_preview"]["ACTIVE"]["allowed"] is True


def test_p013_capability_route_can_materialize_gap_research_mission(tmp_dir, monkeypatch):
    capability_service = JyotishaCapabilityLifecycleService()
    research_service = ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )
    client = _client(capability_service, research_service, monkeypatch)

    first = client.post("/api/research/capabilities/VEDA-CAP-VARGA-000001/research-mission")
    second = client.post("/api/research/capabilities/VEDA-CAP-VARGA-000001/research-mission")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    assert first.json()["mission"]["title"] == second.json()["mission"]["title"]
