from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth.middleware import AuthMiddleware
from backend.routers import research as research_router
from engines.ai.research.platform.contracts import EvidenceType, ProviderStatus, ProviderType, ResearchMissionRecord, ResearchProviderDescriptor
from engines.ai.research.platform.providers import BasePlatformResearchProvider, ProviderDocument, ProviderEvidenceHint, ProviderSearchBatch
from engines.ai.research.platform.runtime import ResearchPlatformRuntime
from engines.ai.research.platform.service import ResearchPlatformService


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"


class SearchProvider(BasePlatformResearchProvider):
    def descriptor(self) -> ResearchProviderDescriptor:
        return ResearchProviderDescriptor(
            provider_id="external-search",
            provider_type=ProviderType.WEB_SEARCH,
            capabilities=["search"],
            supports_search=True,
            supports_fetch=False,
            supports_documents=True,
            status=ProviderStatus.HEALTHY,
            allowed_uri_schemes=["https", "http"],
        )

    def is_available(self) -> bool:
        return True

    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        doc = ProviderDocument(
            source_uri="https://example.com/runtime-api",
            source_title="Runtime API alpha",
            source_type=EvidenceType.WEB_REFERENCE,
            content="Runtime API alpha content",
            metadata={"authority_score": 0.7},
            evidence_hints=[
                ProviderEvidenceHint(
                    passage="Runtime API alpha evidence.",
                    claim_hint="Runtime API alpha evidence.",
                    normalized_text="runtime api alpha evidence",
                    confidence=0.7,
                    location="paragraph:1",
                    metadata={
                        "title": "Runtime API alpha",
                        "topic_key": "runtime.api.alpha",
                        "stance": "POSITIVE",
                        "candidate_type": "NEW_CLAIM",
                        "priority": "P1",
                    },
                )
            ],
        )
        return ProviderSearchBatch(documents=[doc], query="runtime api alpha", search_metadata={"result_count": 1})

    def retrieve(self, document: ProviderDocument) -> str:
        return document.content

    def fetch_metadata(self, document: ProviderDocument) -> dict:
        return dict(document.metadata)

    def extract(self, document: ProviderDocument, *, content: str):
        return list(document.evidence_hints)

    def health_check(self) -> dict:
        return {"provider_id": "external-search", "status": "HEALTHY"}


class FetchProvider(SearchProvider):
    def descriptor(self) -> ResearchProviderDescriptor:
        return ResearchProviderDescriptor(
            provider_id="external-fetch",
            provider_type=ProviderType.DIRECT_WEB,
            capabilities=["retrieve", "extract"],
            supports_search=False,
            supports_fetch=True,
            supports_documents=True,
            status=ProviderStatus.HEALTHY,
            allowed_uri_schemes=["https", "http"],
        )

    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        raise RuntimeError("not used")


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
        providers={
            "external-search": SearchProvider(),
            "external-fetch": FetchProvider(),
        },
    )


def _client(service: ResearchPlatformService, runtime: ResearchPlatformRuntime, monkeypatch) -> TestClient:
    monkeypatch.setattr(research_router, "get_research_platform_service", lambda: service)
    monkeypatch.setattr(research_router, "get_research_platform_runtime", lambda: runtime)
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(research_router.router)
    return TestClient(app)


def test_p009_runtime_admin_routes_control_scheduler_state_and_run_due(tmp_dir, monkeypatch):
    service = _service(tmp_dir)
    runtime = ResearchPlatformRuntime(service=service, instance_id="api-runtime")
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "API runtime mission",
            "objective": "Exercise runtime admin endpoints.",
            "research_type": "DISCOVERY",
            "priority": "P1",
            "status": "ACTIVE",
            "query_strategy": {
                "provider_id": "external-search",
                "retrieval_provider_id": "external-fetch",
            },
        }
    )
    service.create_schedule(
        {
            "domain_id": mission.domain_id,
            "mission_id": mission.mission_id,
            "cadence_type": "HOURLY",
            "timezone": "UTC",
            "next_run_at": "2026-08-11T00:00:00Z",
        }
    )
    client = _client(service, runtime, monkeypatch)

    pause = client.post("/api/research/platform/pause", json={"reason": "maintenance"})
    resume = client.post("/api/research/platform/resume", json={"reason": "resume"})
    kill_on = client.post("/api/research/platform/kill-switch", json={"enabled": True, "reason": "stop"})
    blocked = client.post("/api/research/platform/run-due", json={"as_of": "2026-08-11T01:00:00Z"})
    kill_off = client.post("/api/research/platform/kill-switch", json={"enabled": False, "reason": "resume"})
    ran = client.post("/api/research/platform/run-due", json={"as_of": "2026-08-11T01:00:00Z"})
    status = client.get("/api/research/platform/runtime")
    disable_provider = client.post("/api/research/providers/external-search/disable")
    enable_provider = client.post("/api/research/providers/external-search/enable")

    assert pause.status_code == 200
    assert pause.json()["paused"] is True
    assert resume.status_code == 200
    assert resume.json()["paused"] is False
    assert kill_on.status_code == 200 and kill_on.json()["kill_switch"] is True
    assert blocked.status_code == 200 and blocked.json()["status"] == "KILL_SWITCH"
    assert kill_off.status_code == 200 and kill_off.json()["kill_switch"] is False
    assert ran.status_code == 200 and ran.json()["runs_started"] == 1
    assert status.status_code == 200
    assert status.json()["runtime"]["backlog_state"] in {"NORMAL", "ELEVATED", "HIGH", "SATURATED"}
    assert disable_provider.status_code == 200 and disable_provider.json()["enabled"] is False
    assert enable_provider.status_code == 200 and enable_provider.json()["enabled"] is True
