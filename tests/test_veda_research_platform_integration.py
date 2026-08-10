from __future__ import annotations

from pathlib import Path

from engines.ai.research.platform.contracts import ApprovalStatus, ContradictionStatus
from engines.ai.research.platform.service import ResearchPlatformService


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )


def _mission_payload() -> dict:
    return {
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


def test_research_platform_synthetic_pilot_survives_pending_review_and_restart(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(_mission_payload())

    run_one = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    candidates_after_run_one = {item.title: item for item in service.list_candidates()}

    assert run_one.status == run_one.status.SUCCESS
    assert run_one.sources_discovered == 4
    assert run_one.sources_rejected == 1
    assert run_one.candidates_created == 3
    assert run_one.conflicts_created == 1

    alpha = candidates_after_run_one["Synthetic alpha improves evidence durability"]
    beta = candidates_after_run_one["Synthetic beta decreases evidence durability"]
    gamma = candidates_after_run_one["Synthetic gamma requires multi-source confirmation"]

    assert alpha.approval_status == ApprovalStatus.PENDING
    assert alpha.support_count == 1
    assert beta.contradiction_status == ContradictionStatus.DIRECT
    assert gamma.novelty_status.value == "KNOWN"

    run_two = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    candidates_after_run_two = {item.title: item for item in service.list_candidates()}
    alpha_after = candidates_after_run_two["Synthetic alpha improves evidence durability"]
    delta = candidates_after_run_two["Synthetic delta remains uncertain"]

    assert run_two.status == run_two.status.SUCCESS
    assert run_two.duplicates_detected == 1
    assert alpha_after.candidate_id == alpha.candidate_id
    assert alpha_after.support_count == 2
    assert alpha_after.validation_status.value == "PASS"
    assert delta.approval_status == ApprovalStatus.PENDING
    assert delta.validation_status.value == "PASS_WITH_CONDITIONS"

    approval_alpha = service.decide_candidate(alpha_after.candidate_id, action="APPROVE", actor_id="admin@example.com", reason="Supported by two independent sources.")
    approval_beta = service.decide_candidate(beta.candidate_id, action="REJECT", actor_id="admin@example.com", reason="Conflicts with approved core and lacks override evidence.")
    approval_delta = service.decide_candidate(delta.candidate_id, action="REQUEST_MORE_RESEARCH", actor_id="admin@example.com", reason="Needs more evidence before approval.")

    assert approval_alpha.status == ApprovalStatus.APPROVED
    assert approval_beta.status == ApprovalStatus.REJECTED
    assert approval_delta.status == ApprovalStatus.NEEDS_MORE_RESEARCH

    follow_up_missions = [item for item in service.list_missions() if item.parent_candidate_id == delta.candidate_id]
    assert len(follow_up_missions) == 1

    follow_up_run = service.trigger_manual_run(follow_up_missions[0].mission_id, actor_id="admin@example.com")
    delta_after_follow_up = service.get_candidate(delta.candidate_id)
    assert follow_up_run.status == follow_up_run.status.SUCCESS
    assert delta_after_follow_up is not None
    assert delta_after_follow_up.support_count == 2

    restarted = _service(tmp_dir)
    restored_alpha = restarted.get_candidate(alpha_after.candidate_id)
    restored_delta = restarted.get_candidate(delta.candidate_id)
    restored_follow_up = restarted.list_missions()
    alpha_ledger = restarted.store.list_ledger_for_candidate(alpha_after.candidate_id)

    assert restored_alpha is not None and restored_alpha.approval_status == ApprovalStatus.APPROVED
    assert restored_delta is not None and restored_delta.support_count == 2
    assert any(item.parent_candidate_id == delta.candidate_id for item in restored_follow_up)
    assert any(event.event_type.value == "CANDIDATE_CREATED" for event in alpha_ledger)
    assert any(event.event_type.value == "VALIDATION_COMPLETED" for event in alpha_ledger)
    assert any(event.event_type.value == "ADMIN_APPROVED" for event in alpha_ledger)


def test_research_platform_exports_machine_readable_snapshot(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(_mission_payload())
    service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    export_dir = tmp_dir / "export"
    written = service.export_snapshot(export_dir)

    assert (export_dir / "research_domain.json").exists()
    assert (export_dir / "research_candidate.json").exists()
    assert (export_dir / "research_ledger_event.json").exists()
    assert "research_dashboard" in written
