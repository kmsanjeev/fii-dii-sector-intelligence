from __future__ import annotations

from pathlib import Path

from engines.ai.research.platform.contracts import (
    MissionStatus,
    ResearchRunRecord,
    RunStatus,
    TriggerType,
    write_json_schemas,
)
from engines.ai.research.platform.service import ResearchPlatformService, utc_now


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )


def test_research_platform_writes_json_schemas(tmp_dir):
    target = tmp_dir / "schemas"
    written = write_json_schemas(target)

    assert {path.name for path in written} == {
        "research_domain.schema.json",
        "research_mission.schema.json",
        "research_schedule.schema.json",
        "research_run.schema.json",
        "source_observation.schema.json",
        "research_evidence.schema.json",
        "research_candidate.schema.json",
        "research_validation.schema.json",
        "research_conflict.schema.json",
        "research_approval.schema.json",
        "research_ledger_event.schema.json",
    }
    for path in written:
        assert path.exists()


def test_research_platform_mission_and_schedule_lifecycle(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "Synthetic continuity mission",
            "objective": "Validate candidate continuity across runs.",
            "research_type": "CLAIM_VALIDATION",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": ["initial", "continuation"],
            },
            "minimum_independent_sources": 2,
        }
    )
    schedule = service.create_schedule(
        {
            "domain_id": mission.domain_id,
            "mission_id": mission.mission_id,
            "cadence_type": "DAILY",
            "timezone": "Asia/Calcutta",
        }
    )

    updated_schedule = service.update_schedule(schedule.schedule_id, {"enabled": False, "priority": "P1"})
    paused = service.pause_mission(mission.mission_id)
    resumed = service.resume_mission(mission.mission_id)

    assert mission.status == MissionStatus.QUEUED
    assert updated_schedule.enabled is False
    assert updated_schedule.priority.value == "P1"
    assert paused.status == MissionStatus.PAUSED
    assert resumed.status == MissionStatus.ACTIVE


def test_research_platform_marks_stale_runs_recoverable(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "Synthetic recovery mission",
            "objective": "Validate restart recovery.",
            "research_type": "CLAIM_VALIDATION",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": ["initial"],
            },
        }
    )

    running = ResearchRunRecord(
        run_id=service.store.next_id("run", "VEDA-RUN-"),
        mission_id=mission.mission_id,
        domain_id=mission.domain_id,
        trigger_type=TriggerType.MANUAL,
        started_at=utc_now(),
        status=RunStatus.RUNNING,
    )
    service.store.insert_run(running)

    restarted = _service(tmp_dir)
    recovered = restarted.get_run(running.run_id)

    assert recovered is not None
    assert recovered.status == RunStatus.RECOVERABLE
