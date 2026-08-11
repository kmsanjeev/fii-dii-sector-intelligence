from __future__ import annotations

import json
from pathlib import Path

from engines.ai.knowledge import approved_core_rag
from engines.ai.knowledge.astrology_capability_framework import JyotishaCapabilityLifecycleService
from engines.ai.knowledge.astrology_foundation_migration import (
    build_phase_bundle,
    classify_bhava,
    evaluate_dignity,
    shadow_compare_chart,
    validate_exported_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SAMPLE = ROOT / "data" / "veda" / "validation" / "runtime" / "p012_chart_fact_contract_sample.json"


def _planet(entity_id: str, rashi_entity_id: str, degree: float, *, bhava_number: int = 1) -> dict[str, object]:
    return {
        "entity_id": entity_id,
        "display_name": entity_id,
        "degree": degree,
        "rashi_entity_id": rashi_entity_id,
        "bhava_number": bhava_number,
    }


def test_p014_export_bundle_is_current():
    report = validate_exported_bundle(ROOT)

    assert report["is_valid"] is True
    assert report["missing_files"] == []
    assert report["mismatched_files"] == []


def test_p014_dignity_evaluator_uses_governed_tables_and_preserves_node_variance():
    chart = {
        "planets": [
            _planet("VEDA-GRAHA-SATURN", "VEDA-RASHI-LIBRA", 20.0),
            _planet("VEDA-GRAHA-SUN", "VEDA-RASHI-LIBRA", 10.0),
            _planet("VEDA-GRAHA-MARS", "VEDA-RASHI-ARIES", 5.0),
            _planet("VEDA-GRAHA-RAHU", "VEDA-RASHI-TAURUS", 20.0),
        ]
    }

    results = {row["planet_entity_id"]: row for row in evaluate_dignity(chart)}

    assert results["VEDA-GRAHA-SATURN"]["classification"] == "exalted"
    assert results["VEDA-GRAHA-SATURN"]["dignity_entity_id"] == "VEDA-DIGNITY-EXALTED_EXACT"
    assert results["VEDA-GRAHA-SUN"]["classification"] == "debilitated"
    assert results["VEDA-GRAHA-MARS"]["classification"] == "moolatrikona"
    assert results["VEDA-GRAHA-MARS"]["confidence_status"] == "APPROVED_WITH_CONDITIONS"
    assert results["VEDA-GRAHA-MARS"]["conflict_ids"] == ["VEDA-CNF-000002"]
    assert results["VEDA-GRAHA-RAHU"]["classification"] == "unresolved_foundation"
    assert results["VEDA-GRAHA-RAHU"]["confidence_status"] == "UNRESOLVED_SOURCE_VARIANCE"


def test_p014_bhava_classifier_uses_governed_house_classes():
    sixth = classify_bhava(6)
    first = classify_bhava(1)

    assert {row["class_entity_id"] for row in sixth} == {"VEDA-HCLASS-DUSTHANA", "VEDA-HCLASS-UPACHAYA"}
    assert {row["class_entity_id"] for row in first} == {"VEDA-HCLASS-KENDRA", "VEDA-HCLASS-TRIKONA"}


def test_p014_shadow_compare_surfaces_legacy_unsourced_differences():
    chart = {
        "planets": [
            _planet("VEDA-GRAHA-VENUS", "VEDA-RASHI-LIBRA", 10.0),
            _planet("VEDA-GRAHA-RAHU", "VEDA-RASHI-TAURUS", 20.0),
        ]
    }

    results = {row["planet_entity_id"]: row for row in shadow_compare_chart(chart)}

    assert results["VEDA-GRAHA-VENUS"]["legacy_result"] == "moolatrikona"
    assert results["VEDA-GRAHA-VENUS"]["governed_result"] == "own_sign"
    assert results["VEDA-GRAHA-VENUS"]["classification"] == "UNRESOLVED"
    assert results["VEDA-GRAHA-RAHU"]["classification"] == "SOURCE_VARIANCE"


def test_p014_rag_retrieves_foundation_knowledge_with_citations():
    kendra = approved_core_rag.diagnose_approved_core_query("What are kendra houses?", top_k=4)
    exaltation = approved_core_rag.diagnose_approved_core_query("What is Jupiter exaltation sign?", top_k=4)

    assert kendra["results"][0]["domain"] == "BHAVA"
    assert "VEDA-CLM-000011" in kendra["results"][0]["claim_ids"]
    assert exaltation["results"][0]["domain"] == "DIGNITY"
    assert "VEDA-CLM-000008" in exaltation["results"][0]["claim_ids"]
    assert exaltation["results"][0]["knowledge_class"] == "APPROVED_CORE"
    assert {citation["source_id"] for citation in exaltation["results"][0]["citations"]} == {
        "VEDA-SRC-000008",
        "VEDA-SRC-000009",
    }


def test_p014_capability_framework_marks_dignity_activation_ready_without_activation():
    service = JyotishaCapabilityLifecycleService()
    pilot = service.pilot_capability()

    assert pilot["capability_id"] == "VEDA-CAP-DIGNITY-000001"
    assert pilot["approved_core_available"] is True
    assert pilot["final_status"] == "ACTIVATION_READY"
    assert pilot["activation_gate"]["decision"] == "WAITING_FOR_ADMIN"
    assert pilot["governance_outcome"] == "ACTIVATION_READY"


def test_p014_phase_bundle_reports_green_foundation_state():
    bundle = build_phase_bundle(ROOT)
    sample = json.loads(RUNTIME_SAMPLE.read_text(encoding="utf-8"))

    assert bundle["summary"]["approved_core_changed"] == "YES"
    assert bundle["summary"]["production_rules_activated"] == 0
    assert bundle["summary"]["production_calculation_semantics_changed"] == "NO"
    assert bundle["summary"]["production_interpretation_semantics_changed"] == "NO"
    assert len(bundle["shadow_results"]) == len(sample["planets"])
