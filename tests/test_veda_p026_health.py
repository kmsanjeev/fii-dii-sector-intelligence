"""P026 health governance, Varga, synthesis, and medical-boundary tests."""

from __future__ import annotations

from pathlib import Path

from engines.ai.knowledge.health_governance import build_phase_bundle, export_phase_bundle, validate_bundle
from engines.health.m001_existing_health_logic_inventory import inventory_repository
from engines.intelligence.health_evidence_aggregation import ConfidenceBand, EvidenceDirection, HealthEvidenceAggregator
from engines.intelligence.health_synthesis_engine import HealthSynthesisEngine


def test_phase_bundle_is_valid_and_medically_bounded() -> None:
    bundle = build_phase_bundle()
    report = validate_bundle(bundle)
    assert bundle["meta"]["phase"] == "VEDA-P026"
    assert report["is_valid"] is True
    assert report["errors"] == []
    assert report["production_activation"] == 0
    assert bundle["summary"]["clinical_diagnosis"] == "OUT_OF_SCOPE_MEDICAL"
    assert bundle["summary"]["medical_treatment_recommendation"] == "OUT_OF_SCOPE_MEDICAL"
    assert report["varga_calculation_interpretation_separated"] is True


def test_export_phase_bundle_writes_canonical_artifacts(tmp_path: Path) -> None:
    written = export_phase_bundle(root=tmp_path, validation_dir=tmp_path / "validation")
    assert written
    assert (tmp_path / "validation" / "p026_health_bundle.json").exists()
    assert (tmp_path / "validation" / "p026_health_varga_audit.json").exists()
    assert (tmp_path / "docs" / "current-state" / "p026" / "VEDA-P026-00_EXECUTIVE_SUMMARY.md").exists()


def test_inventory_classifies_health_surfaces(tmp_path: Path) -> None:
    governed = tmp_path / "engines" / "health" / "sample.py"
    governed.parent.mkdir(parents=True)
    governed.write_text("health = True\nD30 = True\n", encoding="utf-8")
    legacy = tmp_path / "engines" / "ai" / "chatbot" / "tools" / "kundli_interpreter.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("health and disease narrative\n", encoding="utf-8")
    research = tmp_path / "data" / "veda" / "research" / "astrology" / "x.md"
    research.parent.mkdir(parents=True)
    research.write_text("medical astrology research\n", encoding="utf-8")
    result = inventory_repository(tmp_path)
    assert result["files_with_matches"] == 3
    assert {row["classification"] for row in result["records"]} >= {"LEGACY", "RESEARCH_ONLY"}


def test_aggregation_preserves_conflict_and_mitigation() -> None:
    aggregator = HealthEvidenceAggregator()
    aggregator.add_evidence(source_layer="D1", evidence_type="VITALITY", direction=EvidenceDirection.SUPPORTING, claim="Lagna support", confidence=ConfidenceBand.HIGH)
    aggregator.add_evidence(source_layer="BHAVA_6", evidence_type="CHALLENGE", direction=EvidenceDirection.OPPOSING, claim="6th challenge")
    aggregator.add_evidence(source_layer="YOGA_DOSHA", evidence_type="MITIGATION", direction=EvidenceDirection.CANCELLING, claim="mitigation")
    result = aggregator.synthesize_narrative()
    assert result["overall_state"] == "CONFLICTED"
    assert result["supporting_count"] == 1
    assert result["opposing_count"] == 1
    assert result["cancelling_count"] == 1
    assert result["conflict_count"] >= 1


def test_health_synthesis_separates_layers_and_medical_boundary() -> None:
    output = HealthSynthesisEngine().synthesize(
        subject_id="SUBJECT-001",
        natal_factors={"lagna": "Libra", "lagnesha": "Venus", "sixth_house": True},
        varga_facts={"D30": {"status": "IMPLEMENTED_WITH_CONDITIONS"}},
        dasha_context={"challenge": True},
        transit_context={"support": True},
        yoga_facts={"mitigation_present": True},
        strength_facts={"validated": False},
        prediction_mode="SHADOW",
    )
    assert output.domain == "HEALTH"
    assert output.prediction_mode == "SHADOW"
    assert output.d1_context["lagna"] == "Libra"
    assert output.varga_context["D30"]["status"] == "IMPLEMENTED_WITH_CONDITIONS"
    assert output.medical_boundary_notice == "ASTROLOGICAL_HEALTH_INDICATOR_NOT_CLINICAL_DIAGNOSIS"
    assert output.explainability_trace[0] == "HEALTH SYNTHESIS"
    assert output.backtesting_ready is True


def test_health_prediction_record_is_backtestable_not_clinical() -> None:
    record = HealthSynthesisEngine().create_prediction_record(prediction_type="EXPERIMENTAL_PREDICTION", prediction_state="EXPERIMENTAL", window_start="2026-08-14T00:00:00Z", window_end="2026-09-14T00:00:00Z", confidence_state="RESEARCH_REQUIRED", notes="Not a diagnosis or treatment recommendation")
    record.record_outcome("EXPERIMENTAL")
    assert record.domain == "HEALTH"
    assert record.comparison_result == "MATCH"
    assert "diagnosis" in record.notes.lower()
