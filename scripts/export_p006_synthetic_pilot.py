from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.research.platform.contracts import AdminAction
from engines.ai.research.platform.service import ResearchPlatformService
from engines.ai.research.platform import service as service_module
from engines.ai.research.platform import synthetic as synthetic_module


FIXTURE_PATH = ROOT / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"
EXPORT_DIR = ROOT / "data" / "research" / "synthetic_pilot"


class DeterministicClock:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def __call__(self) -> str:
        value = self.current.isoformat().replace("+00:00", "Z")
        self.current += timedelta(seconds=1)
        return value


def _build_service(db_path: Path) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=db_path,
        fixture_path=FIXTURE_PATH,
    )


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in EXPORT_DIR.glob("*.json"):
        path.unlink()

    original_service_clock = service_module.utc_now
    original_synthetic_clock = synthetic_module.utc_now
    clock = DeterministicClock(datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc))

    service_module.utc_now = clock
    synthetic_module.utc_now = clock
    try:
        with tempfile.TemporaryDirectory(prefix="veda_p006_") as tmp:
            service = _build_service(Path(tmp) / "research_platform.sqlite3")
            mission = service.create_mission(
                {
                    "domain_id": "VEDA-DOMAIN-SYNTHETIC",
                    "title": "Synthetic pilot mission",
                    "objective": "Exercise the P006 platform pipeline end to end.",
                    "research_type": "CLAIM_VALIDATION",
                    "priority": "P1",
                    "status": "QUEUED",
                    "created_by": "admin",
                    "query_strategy": {
                        "provider_id": "synthetic-fixture",
                        "batch_sequence": ["initial", "continuation"],
                    },
                    "required_source_classes": ["WEB_REFERENCE", "OFFICIAL_DOCUMENT"],
                    "minimum_independent_sources": 2,
                    "known_claim_ids": [],
                    "known_conflict_ids": [],
                    "known_gap_ids": [],
                    "safety_class": "MODERATE",
                    "completion_policy": {"auto_complete": False},
                    "research_budget": {
                        "max_queries": 2,
                        "max_sources": 6,
                        "max_provider_calls": 2,
                        "max_runtime_seconds": 60,
                        "max_model_calls": 0,
                        "max_cost": 0,
                        "max_follow_up_depth": 2,
                        "max_retries": 1,
                        "cooldown_seconds": 0,
                    },
                }
            )
            service.create_schedule(
                {
                    "domain_id": mission.domain_id,
                    "mission_id": mission.mission_id,
                    "cadence_type": "DAILY",
                    "timezone": "Asia/Calcutta",
                    "priority": "P1",
                }
            )

            service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
            service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")

            candidates = {item.title: item for item in service.list_candidates()}
            alpha = candidates["Synthetic alpha improves evidence durability"]
            beta = candidates["Synthetic beta decreases evidence durability"]
            delta = candidates["Synthetic delta remains uncertain"]

            service.decide_candidate(
                alpha.candidate_id,
                action=AdminAction.APPROVE,
                actor_id="admin@example.com",
                reason="Supported by two independent sources.",
            )
            service.decide_candidate(
                beta.candidate_id,
                action=AdminAction.REJECT,
                actor_id="admin@example.com",
                reason="Conflicts with approved core and lacks override evidence.",
            )
            service.decide_candidate(
                delta.candidate_id,
                action=AdminAction.REQUEST_MORE_RESEARCH,
                actor_id="admin@example.com",
                reason="Needs more evidence before approval.",
            )

            follow_up = next(
                item for item in service.list_missions() if item.parent_candidate_id == delta.candidate_id
            )
            service.trigger_manual_run(follow_up.mission_id, actor_id="admin@example.com")
            service.export_snapshot(EXPORT_DIR)
    finally:
        service_module.utc_now = original_service_clock
        synthetic_module.utc_now = original_synthetic_clock

    print(EXPORT_DIR.relative_to(ROOT))


if __name__ == "__main__":
    main()
