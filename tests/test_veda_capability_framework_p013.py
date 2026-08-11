from __future__ import annotations

import json
from pathlib import Path

from engines.ai.knowledge.astrology_capability_framework import (
    CapabilityStatus,
    JyotishaCapabilityLifecycleService,
    export_phase_bundle,
    validate_exported_bundle,
    write_json_schemas,
)
from engines.ai.research.platform.service import ResearchPlatformService


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "research" / "fixtures" / "synthetic_research_fixture.json"
DATA_ROOT = ROOT / "data" / "veda" / "validation" / "capabilities"


def _load_json(name: str):
    return json.loads((DATA_ROOT / name).read_text(encoding="utf-8"))


def test_p013_writes_json_schemas(tmp_dir):
    target = tmp_dir / "schemas"
    target.mkdir(parents=True, exist_ok=True)
    written = write_json_schemas(tmp_dir)

    assert {path.name for path in written} == {
        "capability_registry.schema.json",
        "capability_dependency.schema.json",
        "capability_lifecycle.schema.json",
        "capability_validation.schema.json",
        "capability_activation.schema.json",
        "capability_rollback.schema.json",
        "capability_coverage.schema.json",
        "capability_package.schema.json",
    }


def test_p013_export_bundle_is_current():
    report = validate_exported_bundle(ROOT)

    assert report["is_valid"] is True
    assert report["missing_files"] == []
    assert report["mismatched_files"] == []
    assert report["schema_errors"] == []


def test_p013_summary_records_fail_closed_framework_and_zero_new_activation():
    payload = _load_json("p013_summary.json")
    summary = payload["summary"]

    assert summary["capabilities_registered"] >= 20
    assert summary["pilot_capability_id"] == "VEDA-CAP-DIGNITY-000001"
    assert summary["pilot_status"] == "ACTIVATION_READY"
    assert summary["next_recommended_phase"].startswith("P014")
    assert summary["production_capabilities_activated"] == 0
    assert summary["production_calculation_semantics_changed"] == "NO"
    assert summary["production_interpretation_semantics_changed"] == "NO"
    assert summary["approved_core_automatically_modified"] == "NO"
    assert summary["lifecycle_fail_closed"] is True


def test_p013_dignity_pilot_reaches_activation_ready_without_auto_activation():
    service = JyotishaCapabilityLifecycleService()
    pilot = service.pilot_capability()

    assert pilot["capability_id"] == "VEDA-CAP-DIGNITY-000001"
    assert pilot["approved_core_available"] is True
    assert pilot["approved_rule_ids"] == ["VEDA-RUL-DIGNITY-000002"]
    assert pilot["final_status"] == "ACTIVATION_READY"
    assert pilot["governance_outcome"] == "ACTIVATION_READY"
    assert pilot["research_gate"]["decision"] == "PASS"
    assert pilot["validation_gate"]["decision"] == "PASS"
    assert pilot["shadow_gate"]["decision"] == "PASS"
    assert pilot["activation_gate"]["decision"] == "WAITING_FOR_ADMIN"
    assert pilot["recommended_research_mission"] is None
    assert pilot["blocked_reason"] is None


def test_p013_prevents_direct_transition_from_researching_to_active():
    service = JyotishaCapabilityLifecycleService()

    transition = service.preview_transition(
        "VEDA-CAP-RULE-000001",
        CapabilityStatus.ACTIVE,
        actor_is_admin=True,
    )

    assert transition.allowed is False
    assert transition.from_status == CapabilityStatus.RESEARCHING
    assert transition.to_status == CapabilityStatus.ACTIVE
    assert "not allowed" in transition.reason.lower()


def test_p013_capability_gap_mission_is_created_once_and_then_deduplicated(tmp_dir):
    capability_service = JyotishaCapabilityLifecycleService()
    research_service = ResearchPlatformService(
        db_path=tmp_dir / "research_platform.sqlite3",
        fixture_path=FIXTURE_PATH,
    )

    first = capability_service.create_research_mission(
        research_service,
        "VEDA-CAP-VARGA-000001",
        actor_id="admin@example.com",
    )
    second = capability_service.create_research_mission(
        research_service,
        "VEDA-CAP-VARGA-000001",
        actor_id="admin@example.com",
    )

    assert first["duplicate"] is False
    assert first["mission"]["domain_id"] == "VEDA-DOMAIN-VEDIC-ASTROLOGY"
    assert first["mission"]["research_type"] == "KNOWLEDGE_GAP"
    assert first["mission"]["known_gap_ids"] == ["VEDA-CAP-VARGA-000001"]
    assert second["duplicate"] is True
    assert second["mission"]["mission_id"] == first["mission"]["mission_id"]
