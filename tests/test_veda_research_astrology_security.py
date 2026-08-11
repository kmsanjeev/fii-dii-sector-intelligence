from __future__ import annotations

from engines.ai.research.platform.service import ResearchPlatformService


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
    )


def test_astrology_research_flags_prompt_injection_but_keeps_source_as_data(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-VEDIC-ASTROLOGY",
            "title": "Malicious astrology source mission",
            "objective": "Verify prompt-injection isolation for astrology research.",
            "research_type": "LEGACY_RULE_PROVENANCE",
            "query_strategy": {
                "provider_id": "vedic-astrology-local",
                "queries": ["astrology finance signal"],
                "search_rounds": [
                    {
                        "queries": ["astrology finance signal"],
                        "inject_malicious_source": True,
                    }
                ],
            },
        }
    )

    run = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    observations = service.store.list_observations_for_run(run.run_id)
    evidence_rows = service.store.list_evidence()
    candidates = [item for item in service.list_candidates() if item.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY"]

    assert run.status.value == "SUCCESS"
    assert run.sources_discovered == 1
    assert observations[0].trust_metadata["prompt_injection_detected"] is True
    assert evidence_rows[0].domain_metadata["prompt_injection_detected"] is True
    assert "ignore previous instructions" not in evidence_rows[0].normalized_text.lower()
    assert len(candidates) == 1
    assert candidates[0].approval_status.value == "PENDING"
    assert candidates[0].safety_class.value == "HIGH_STAKES"


def test_astrology_research_rejects_unsupported_or_fabricated_source_before_candidate_creation(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-VEDIC-ASTROLOGY",
            "title": "Unsupported astrology source mission",
            "objective": "Reject unsupported or fabricated astrology sources.",
            "research_type": "LEGACY_RULE_PROVENANCE",
            "query_strategy": {
                "provider_id": "vedic-astrology-local",
                "queries": ["unsupported fabricated sentinel qzxj"],
                "search_rounds": [
                    {
                        "queries": ["unsupported fabricated sentinel qzxj"],
                        "inject_unsupported_source": True,
                    }
                ],
            },
        }
    )

    run = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    observations = service.store.list_observations_for_run(run.run_id)
    candidates = [item for item in service.list_candidates() if item.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY"]

    assert run.status.value == "SUCCESS"
    assert run.sources_rejected == 1
    assert candidates == []
    assert observations[0].access_status.value == "REJECTED"
    assert observations[0].trust_metadata["reject_reason"] == "POSSIBLE_FABRICATION"
