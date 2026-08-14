"""P025 progeny governance, synthesis, and medical-boundary tests."""

from __future__ import annotations

from pathlib import Path

from engines.ai.knowledge.progeny_governance import build_phase_bundle, export_phase_bundle, validate_bundle
from engines.intelligence.progeny_evidence_aggregation import ConfidenceBand, EvidenceDirection, ProgenyEvidenceAggregator
from engines.intelligence.progeny_synthesis_engine import ProgenySynthesisEngine
from engines.progeny.m001_existing_progeny_logic_inventory import inventory_repository


def test_phase_bundle_is_valid_and_high_stakes_safe() -> None:
    bundle = build_phase_bundle()
    report = validate_bundle(bundle)
    assert bundle["meta"]["phase"] == "VEDA-P025"
    assert report["is_valid"] is True
    assert report["errors"] == []
    assert report["d7_calculation_interpretation_separated"] is True
    assert bundle["summary"]["production_activation"] == 0
    assert bundle["summary"]["medical_diagnosis"] == "OUT_OF_SCOPE_MEDICAL"
    assert bundle["source_quality"]["independent_source_families"] >= 1


def test_export_phase_bundle_writes_canonical_artifacts(tmp_path: Path) -> None:
    written = export_phase_bundle(root=tmp_path, validation_dir=tmp_path / "validation")
    assert written
    assert (tmp_path / "validation" / "p025_progeny_bundle.json").exists()
    assert (tmp_path / "docs" / "current-state" / "p025" / "VEDA-P025-00_EXECUTIVE_SUMMARY.md").exists()
    assert (tmp_path / "docs" / "current-state" / "p025" / "m001_inventory.json").exists()


def test_inventory_classifies_legacy_research_and_shadow_surfaces(tmp_path: Path) -> None:
    governed = tmp_path / "engines" / "progeny" / "sample.py"
    governed.parent.mkdir(parents=True)
    governed.write_text("D7 = True\nprogeny = 'research'\n", encoding="utf-8")
    legacy = tmp_path / "engines" / "ai" / "chatbot" / "tools" / "kundli_interpreter.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("children may be delayed\n", encoding="utf-8")
    research = tmp_path / "data" / "veda" / "research" / "astrology" / "x.md"
    research.parent.mkdir(parents=True)
    research.write_text("fertility research\n", encoding="utf-8")
    result = inventory_repository(tmp_path)
    assert result["files_with_matches"] == 3
    assert {row["classification"] for row in result["records"]} >= {"RESEARCH_ONLY", "LEGACY"}


def test_aggregation_preserves_conflict_and_cancellation() -> None:
    aggregator = ProgenyEvidenceAggregator()
    aggregator.add_evidence(source_layer="D1", evidence_type="BHAVA", direction=EvidenceDirection.SUPPORTING, claim="D1 support", confidence=ConfidenceBand.HIGH)
    aggregator.add_evidence(source_layer="D7", evidence_type="VARGA", direction=EvidenceDirection.OPPOSING, claim="D7 challenge")
    aggregator.add_evidence(source_layer="YOGA_DOSHA", evidence_type="CANCELLATION", direction=EvidenceDirection.CANCELLING, claim="mitigation")
    result = aggregator.synthesize_narrative()
    assert result["overall_state"] == "CONFLICTED"
    assert result["supporting_count"] == 1
    assert result["opposing_count"] == 1
    assert result["cancelling_count"] == 1
    assert result["conflict_count"] >= 1


def test_synthesis_separates_d1_d7_and_medical_boundary() -> None:
    output = ProgenySynthesisEngine().synthesize(
        subject_id="SUBJECT-001",
        natal_factors={"fifth_house": True, "fifth_lord": "Jupiter"},
        d7_facts={"d1_d7_alignment": False, "interpretation_status": "RESEARCHING"},
        dasha_context={"progeny_window": True},
        transit_context={"challenge": True},
        yoga_facts={"cancellation_present": True},
        strength_facts={"validated": False},
        prediction_mode="SHADOW",
    )
    assert output.domain == "PROGENY"
    assert output.prediction_mode == "SHADOW"
    assert output.d1_context["fifth_house"] is True
    assert output.d7_context["d1_d7_alignment"] is False
    assert output.medical_boundary_notice == "ASTROLOGICAL_INDICATOR_NOT_MEDICAL_FERTILITY_STATUS"
    assert output.explainability_trace[0] == "PROGENY SYNTHESIS"
    assert output.backtesting_ready is True


def test_prediction_record_supports_backtesting_without_medical_certainty() -> None:
    engine = ProgenySynthesisEngine()
    record = engine.create_prediction_record(prediction_type="EXPERIMENTAL_PREDICTION", prediction_state="EXPERIMENTAL", window_start="2026-08-14T00:00:00Z", window_end="2026-09-14T00:00:00Z", confidence_state="RESEARCH_REQUIRED", rule_versions=["P025_SHADOW_1"], notes="Not a medical prediction")
    record.record_outcome("EXPERIMENTAL")
    assert record.domain == "PROGENY"
    assert record.comparison_result == "MATCH"
    assert "medical" in record.notes.lower()
