from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth.middleware import AuthMiddleware
from backend.routers import research as research_router
from engines.ai.research.platform.contracts import SafetyClass
from engines.ai.research.platform.service import ResearchPlatformService


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_admin_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )


def _client(service: ResearchPlatformService, monkeypatch) -> TestClient:
    monkeypatch.setattr(research_router, "get_research_platform_service", lambda: service)
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(research_router.router)
    return TestClient(app)


def _seed_synthetic_mission(service: ResearchPlatformService) -> tuple[str, str]:
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "P008 synthetic mission",
            "objective": "Generate deterministic research artifacts for admin console tests.",
            "research_type": "CLAIM_VALIDATION",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": ["initial"],
            },
        }
    )
    run = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    return mission.mission_id, run.run_id


def test_research_admin_dashboard_and_detail_surfaces_return_governance_views(tmp_dir, monkeypatch):
    service = _service(tmp_dir)
    mission_id, run_id = _seed_synthetic_mission(service)
    candidate_id = service.list_candidates()[0].candidate_id
    service.create_schedule(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "mission_id": mission_id,
            "cadence_type": "DAILY",
            "enabled": True,
            "next_run_at": "2026-08-12T05:00:00Z",
        }
    )

    client = _client(service, monkeypatch)

    dashboard = client.get("/api/research/dashboard", params={"domain_id": "VEDA-DOMAIN-SYNTHETIC"})
    mission_detail = client.get(f"/api/research/missions/{mission_id}")
    run_detail = client.get(f"/api/research/runs/{run_id}")
    candidate_detail = client.get(f"/api/research/candidates/{candidate_id}")
    schedules = client.get("/api/research/schedules", params={"domain_id": "VEDA-DOMAIN-SYNTHETIC"})

    assert dashboard.status_code == 200
    assert mission_detail.status_code == 200
    assert run_detail.status_code == 200
    assert candidate_detail.status_code == 200
    assert schedules.status_code == 200

    dashboard_payload = dashboard.json()
    assert dashboard_payload["engine_status"] in {"RUNNING", "IDLE", "DEGRADED", "PAUSED"}
    assert len(dashboard_payload["domains"]) >= 1
    assert "provider_health" in dashboard_payload
    assert "notifications" in dashboard_payload
    assert "analytics" in dashboard_payload
    assert "coverage" in dashboard_payload

    mission_payload = mission_detail.json()
    assert mission_payload["mission"]["mission_id"] == mission_id
    assert mission_payload["run_history"]
    assert "ledger" in mission_payload

    run_payload = run_detail.json()
    assert run_payload["run"]["run_id"] == run_id
    assert run_payload["timeline"]
    assert run_payload["observations"]

    candidate_payload = candidate_detail.json()
    assert candidate_payload["candidate"]["candidate_id"] == candidate_id
    assert candidate_payload["evidence_summary"]
    assert "source_observations" in candidate_payload
    assert "approval_history" in candidate_payload
    assert "current_knowledge_comparison" in candidate_payload

    schedules_payload = schedules.json()
    assert schedules_payload["returned"] == 1
    assert schedules_payload["schedules"][0]["mission_id"] == mission_id


def test_high_stakes_candidate_approval_requires_explicit_acknowledgement(tmp_dir, monkeypatch):
    service = _service(tmp_dir)
    _seed_synthetic_mission(service)
    candidate = service.list_candidates()[0]
    service.store.upsert_candidate(candidate.model_copy(update={"safety_class": SafetyClass.HIGH_STAKES}))

    client = _client(service, monkeypatch)

    blocked = client.post(
        f"/api/research/candidates/{candidate.candidate_id}/decision",
        json={"action": "APPROVE", "reason": "Approve without explicit high-stakes acknowledgement."},
    )
    allowed = client.post(
        f"/api/research/candidates/{candidate.candidate_id}/decision",
        json={
            "action": "APPROVE",
            "reason": "Approve after explicit high-stakes review.",
            "acknowledged_high_stakes": True,
        },
    )

    assert blocked.status_code == 409
    assert "high-stakes" in blocked.json()["detail"].lower()
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "APPROVED"
    assert allowed.json()["promotion_state"] == "PROMOTION_READY"


def test_needs_more_research_decision_creates_follow_up_and_preserves_history(tmp_dir, monkeypatch):
    service = _service(tmp_dir)
    mission_id, _run_id = _seed_synthetic_mission(service)
    candidate = service.list_candidates()[0]
    candidate = candidate.model_copy(
        update={
            "metadata": {
                **candidate.metadata,
                "follow_up_batch_sequence": ["follow_up"],
            }
        }
    )
    service.store.upsert_candidate(candidate)
    candidate_id = candidate.candidate_id

    client = _client(service, monkeypatch)

    response = client.post(
        f"/api/research/candidates/{candidate_id}/decision",
        json={
            "action": "REQUEST_MORE_RESEARCH",
            "reason": "Need another source class before approval.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "NEEDS_MORE_RESEARCH"

    candidate_detail = client.get(f"/api/research/candidates/{candidate_id}")
    ledger = client.get("/api/research/ledger", params={"candidate_id": candidate_id, "limit": 50})

    assert candidate_detail.status_code == 200
    assert ledger.status_code == 200

    candidate_payload = candidate_detail.json()
    ledger_payload = ledger.json()

    assert candidate_payload["approval_history"][-1]["status"] == "NEEDS_MORE_RESEARCH"
    assert candidate_payload["follow_up_missions"]
    assert any(item["event_type"] == "MORE_RESEARCH_REQUESTED" for item in ledger_payload["events"])
    assert any(item["event_type"] == "FOLLOW_UP_CREATED" for item in ledger_payload["events"])
