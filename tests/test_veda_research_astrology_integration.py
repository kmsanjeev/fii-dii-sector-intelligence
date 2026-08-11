from __future__ import annotations

from engines.ai.research.platform.contracts import AdminAction, ApprovalStatus
from engines.ai.research.platform.service import ResearchPlatformService


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
    )


def _astrology_candidates(service: ResearchPlatformService):
    return [item for item in service.list_candidates() if item.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY"]


def test_astrology_pilot_runs_create_governed_claim_and_legacy_provenance_candidates(tmp_dir):
    service = _service(tmp_dir)
    plugin = service.domain_plugins["VEDA-DOMAIN-VEDIC-ASTROLOGY"]
    missions = [service.create_mission(payload) for payload in plugin.build_pilot_missions()]

    run_a = service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")
    run_b = service.trigger_manual_run(missions[1].mission_id, actor_id="admin@example.com")
    run_c = service.trigger_manual_run(missions[2].mission_id, actor_id="admin@example.com")
    candidates = _astrology_candidates(service)

    assert run_a.status.value == "SUCCESS"
    assert run_a.sources_discovered == 2
    assert run_a.candidates_created == 2
    assert run_a.conflicts_created == 2

    assert run_b.status.value == "SUCCESS"
    assert run_b.sources_discovered == 4
    assert run_b.candidates_created == 1
    assert run_b.duplicates_detected == 3

    assert run_c.status.value == "SUCCESS"
    assert run_c.sources_discovered == 2
    assert run_c.candidates_created == 3
    assert run_c.duplicates_detected == 1
    assert run_c.conflicts_created == 3

    provenance = next(item for item in candidates if item.candidate_type.value == "PROVENANCE_CANDIDATE")
    contextual = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000005"])
    cross_supported = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000006"])

    assert len(candidates) == 6
    assert provenance.title == "VEDA-P005-LGC-0001"
    assert provenance.support_count == 4
    assert provenance.validation_status.value == "PASS_WITH_CONDITIONS"
    assert provenance.metadata["legacy_rule_id"] == "VEDA-P005-LGC-0001"
    assert contextual.contradiction_status.value == "CONTEXTUAL"
    assert contextual.metadata["conflict_ids"] == ["VEDA-CNF-000001"]
    assert cross_supported.support_count == 2
    assert service.store.list_conflicts()


def test_astrology_research_continues_while_review_is_pending_and_rejections_are_rediscovered_not_duplicated(tmp_dir):
    service = _service(tmp_dir)
    plugin = service.domain_plugins["VEDA-DOMAIN-VEDIC-ASTROLOGY"]
    missions = [service.create_mission(payload) for payload in plugin.build_pilot_missions()]

    for mission in missions:
        service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")

    initial_candidates = _astrology_candidates(service)
    approved = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000002"])
    pending = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000001"])
    more_research = next(item for item in initial_candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000005"])
    rejected = next(item for item in initial_candidates if item.candidate_type.value == "PROVENANCE_CANDIDATE")

    service.decide_candidate(approved.candidate_id, action=AdminAction.APPROVE, actor_id="admin@example.com", reason="Known governed foundation.")
    service.decide_candidate(rejected.candidate_id, action=AdminAction.REJECT, actor_id="admin@example.com", reason="Discovery-only provenance is not sufficient.")
    service.decide_candidate(more_research.candidate_id, action=AdminAction.REQUEST_MORE_RESEARCH, actor_id="admin@example.com", reason="Need more contradiction context.")

    follow_up = next(item for item in service.list_missions() if item.parent_candidate_id == more_research.candidate_id)
    follow_up_run = service.trigger_manual_run(follow_up.mission_id, actor_id="admin@example.com")
    rerun_a = service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")
    rerun_b = service.trigger_manual_run(missions[1].mission_id, actor_id="admin@example.com")
    final_candidates = _astrology_candidates(service)

    approved_after = next(item for item in final_candidates if item.candidate_id == approved.candidate_id)
    pending_after = next(item for item in final_candidates if item.candidate_id == pending.candidate_id)
    more_after = next(item for item in final_candidates if item.candidate_id == more_research.candidate_id)
    rejected_after = next(item for item in final_candidates if item.candidate_id == rejected.candidate_id)
    provenance_candidates = [item for item in final_candidates if item.candidate_type.value == "PROVENANCE_CANDIDATE"]

    assert follow_up_run.status.value == "SUCCESS"
    assert follow_up_run.candidates_created == 0
    assert follow_up_run.duplicates_detected == 2

    assert rerun_a.status.value == "SUCCESS"
    assert rerun_a.candidates_created == 0
    assert rerun_a.duplicates_detected == 3

    assert rerun_b.status.value == "SUCCESS"
    assert rerun_b.candidates_created == 0
    assert rerun_b.duplicates_detected == 4

    assert len(final_candidates) == 6
    assert approved_after.approval_status == ApprovalStatus.APPROVED
    assert pending_after.candidate_id == pending.candidate_id
    assert pending_after.support_count == 2
    assert len(pending_after.evidence_ids) == 2
    assert more_after.approval_status == ApprovalStatus.NEEDS_MORE_RESEARCH
    assert len(more_after.evidence_ids) == 2
    assert rejected_after.approval_status == ApprovalStatus.REJECTED
    assert rejected_after.knowledge_zone.value == "RESEARCH_ARCHIVE"
    assert rejected_after.support_count == 4
    assert len(rejected_after.evidence_ids) == 8
    assert len(provenance_candidates) == 1


def test_astrology_candidate_ledger_reconstructs_creation_merge_and_admin_decision(tmp_dir):
    service = _service(tmp_dir)
    plugin = service.domain_plugins["VEDA-DOMAIN-VEDIC-ASTROLOGY"]
    missions = [service.create_mission(payload) for payload in plugin.build_pilot_missions()]

    for mission in missions:
        service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")

    candidates = _astrology_candidates(service)
    approved = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000002"])
    pending = next(item for item in candidates if item.metadata.get("claim_ids") == ["VEDA-CLM-000001"])

    service.decide_candidate(approved.candidate_id, action=AdminAction.APPROVE, actor_id="admin@example.com", reason="Known governed foundation.")
    service.trigger_manual_run(missions[0].mission_id, actor_id="admin@example.com")

    approved_events = {item.event_type.value for item in service.store.list_ledger_for_candidate(approved.candidate_id)}
    pending_events = {item.event_type.value for item in service.store.list_ledger_for_candidate(pending.candidate_id)}

    assert "CANDIDATE_CREATED" in approved_events
    assert "VALIDATION_COMPLETED" in approved_events
    assert "ADMIN_APPROVED" in approved_events
    assert "CANDIDATE_CREATED" in pending_events
    assert "CANDIDATE_MERGED" in pending_events
    assert "VALIDATION_COMPLETED" in pending_events
