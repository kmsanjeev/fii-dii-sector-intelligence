from __future__ import annotations

from pathlib import Path

from engines.ai.research.platform.service import ResearchPlatformService


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"


def _service(tmp_dir) -> ResearchPlatformService:
    return ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )


def test_research_platform_rejects_unsafe_source_and_does_not_create_candidate(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "Unsafe-source mission",
            "objective": "Verify unsafe URI rejection.",
            "research_type": "CLAIM_VALIDATION",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": ["initial"],
            },
        }
    )

    run = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    observations = service.store.list_observations_for_run(run.run_id)

    assert run.sources_rejected == 1
    assert any(obs.source_uri.startswith("file://") and obs.access_status.value == "UNSAFE" for obs in observations)


def test_research_platform_flags_prompt_injection_and_treats_content_as_data(tmp_dir):
    service = _service(tmp_dir)
    mission = service.create_mission(
        {
            "domain_id": "VEDA-DOMAIN-SYNTHETIC",
            "title": "Prompt-injection mission",
            "objective": "Verify prompt-injection isolation.",
            "research_type": "CLAIM_VALIDATION",
            "query_strategy": {
                "provider_id": "synthetic-fixture",
                "batch_sequence": ["initial"],
            },
        }
    )

    run = service.trigger_manual_run(mission.mission_id, actor_id="admin@example.com")
    observations = service.store.list_observations_for_run(run.run_id)
    evidence_rows = service.store.list_evidence()

    beta_observation = next(obs for obs in observations if obs.source_title == "Synthetic Beta Adversarial Note")
    beta_evidence = next(row for row in evidence_rows if row.domain_metadata.get("topic_key") == "synthetic.beta.durability")

    assert beta_observation.trust_metadata["prompt_injection_detected"] is True
    assert "ignore previous instructions" not in beta_evidence.normalized_text.lower()
    assert beta_evidence.claim_hint == "Synthetic beta decreases evidence durability."
