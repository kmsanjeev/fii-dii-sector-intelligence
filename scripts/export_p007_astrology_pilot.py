from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.research.domains.vedic_astrology import plugin as astrology_plugin_module
from engines.ai.research.platform.contracts import AdminAction
from engines.ai.research.platform.service import ResearchPlatformService
from engines.ai.research.platform import service as service_module


EXPORT_DIR = ROOT / "data" / "research" / "vedic_astrology_pilot"


class DeterministicClock:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def __call__(self) -> str:
        value = self.current.isoformat().replace("+00:00", "Z")
        self.current += timedelta(seconds=1)
        return value


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _filtered_candidates(service: ResearchPlatformService):
    return [item for item in service.list_candidates() if item.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY"]


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in EXPORT_DIR.glob("*.json"):
        path.unlink()

    original_service_clock = service_module.utc_now
    original_astrology_clock = astrology_plugin_module.utc_now
    clock = DeterministicClock(datetime(2026, 8, 11, 0, 0, 0, tzinfo=timezone.utc))

    service_module.utc_now = clock
    astrology_plugin_module.utc_now = clock
    try:
        with tempfile.TemporaryDirectory(prefix="veda_p007_") as tmp:
            service = ResearchPlatformService(
                db_path=Path(tmp) / "research_platform.sqlite3",
            )
            plugin = service.domain_plugins["VEDA-DOMAIN-VEDIC-ASTROLOGY"]
            missions = [service.create_mission(payload) for payload in plugin.build_pilot_missions()]

            run_a = service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")
            run_b = service.trigger_manual_run(missions[1].mission_id, actor_id="admin@example.com")
            run_c = service.trigger_manual_run(missions[2].mission_id, actor_id="admin@example.com")

            initial_candidates = _filtered_candidates(service)
            approved = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000002"])
            rejected = next(item for item in initial_candidates if item.candidate_type.value == "PROVENANCE_CANDIDATE")
            more_research = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000005"])

            approval_a = service.decide_candidate(
                approved.candidate_id,
                action=AdminAction.APPROVE,
                actor_id="admin@example.com",
                reason="Known governed foundation with deterministic source alignment.",
            )
            approval_b = service.decide_candidate(
                rejected.candidate_id,
                action=AdminAction.REJECT,
                actor_id="admin@example.com",
                reason="Discovery-only upload evidence remains insufficient for governed provenance promotion.",
            )
            approval_c = service.decide_candidate(
                more_research.candidate_id,
                action=AdminAction.REQUEST_MORE_RESEARCH,
                actor_id="admin@example.com",
                reason="Contradiction context requires additional source review.",
            )

            follow_up = next(item for item in service.list_missions() if item.parent_candidate_id == more_research.candidate_id)
            follow_up_run = service.trigger_manual_run(follow_up.mission_id, actor_id="admin@example.com")
            rerun_a = service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")
            rerun_b = service.trigger_manual_run(missions[1].mission_id, actor_id="admin@example.com")

            service.export_snapshot(EXPORT_DIR)

            final_candidates = _filtered_candidates(service)
            pending = next(item for item in final_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000001"])
            rejected_after = next(item for item in final_candidates if item.candidate_id == rejected.candidate_id)
            more_after = next(item for item in final_candidates if item.candidate_id == more_research.candidate_id)

            _write_json(EXPORT_DIR / "p007_coverage_matrix.json", plugin.build_coverage_matrix())
            _write_json(EXPORT_DIR / "p007_mission_templates.json", plugin.mission_templates())
            _write_json(EXPORT_DIR / "p007_gap_missions.json", plugin.generate_gap_missions(limit=12))
            _write_json(
                EXPORT_DIR / "p007_pilot_summary.json",
                {
                    "phase": "VEDA-P007",
                    "date": "2026-08-11",
                    "domain_id": plugin.domain_id,
                    "missions": [item.model_dump(mode="json") for item in service.list_missions() if item.domain_id == plugin.domain_id],
                    "initial_runs": [run_a.model_dump(mode="json"), run_b.model_dump(mode="json"), run_c.model_dump(mode="json")],
                    "follow_up_run": follow_up_run.model_dump(mode="json"),
                    "reruns": [rerun_a.model_dump(mode="json"), rerun_b.model_dump(mode="json")],
                    "admin_decisions": [
                        approval_a.model_dump(mode="json"),
                        approval_b.model_dump(mode="json"),
                        approval_c.model_dump(mode="json"),
                    ],
                    "candidates": [item.model_dump(mode="json") for item in final_candidates],
                    "pilot_results": {
                        "pilot_a": {
                            "mission_id": missions[0].mission_id,
                            "run_id": run_a.run_id,
                            "candidate_ids": [
                                item.candidate_id
                                for item in final_candidates
                                if item.metadata.get("claim_ids") in (["VEDA-CLM-000001"], ["VEDA-CLM-000002"], ["VEDA-CLM-000003"])
                            ],
                        },
                        "pilot_b": {
                            "mission_id": missions[1].mission_id,
                            "run_id": run_b.run_id,
                            "candidate_id": rejected_after.candidate_id,
                            "legacy_rule_id": rejected_after.metadata.get("legacy_rule_id"),
                        },
                        "pilot_c": {
                            "mission_id": missions[2].mission_id,
                            "run_id": run_c.run_id,
                            "candidate_ids": [
                                item.candidate_id
                                for item in final_candidates
                                if item.metadata.get("claim_ids") in (["VEDA-CLM-000005"], ["VEDA-CLM-000006"])
                            ],
                        },
                    },
                    "continuity": {
                        "research_continues_while_pending": pending.support_count == 2 and pending.approval_status.value == "PENDING",
                        "needs_more_research_follow_up_created": follow_up.parent_candidate_id == more_research.candidate_id,
                        "needs_more_research_candidate_evidence_ids": len(more_after.evidence_ids),
                        "rejected_candidate_rediscovery_same_candidate": rejected_after.candidate_id == rejected.candidate_id,
                        "rejected_candidate_support_count": rejected_after.support_count,
                        "rejected_candidate_evidence_ids": len(rejected_after.evidence_ids),
                    },
                    "metrics": service.dashboard().model_dump(mode="json"),
                    "snapshot_counts": {
                        "domains": len(service.list_domains()),
                        "core_knowledge": len(service.store.list_core_knowledge(plugin.domain_id)),
                        "missions": len(service.list_missions()),
                        "runs": len(service.list_runs()),
                        "observations": len(service.store.list_observations()),
                        "evidence": len(service.store.list_evidence()),
                        "candidates": len(service.list_candidates()),
                        "validations": len(service.store.list_validations()),
                        "conflicts": len(service.store.list_conflicts()),
                        "approvals": len(service.store.list_approvals()),
                        "ledger_events": len(service.list_ledger_events()),
                    },
                },
            )
    finally:
        service_module.utc_now = original_service_clock
        astrology_plugin_module.utc_now = original_astrology_clock

    print(EXPORT_DIR.relative_to(ROOT))


if __name__ == "__main__":
    main()
