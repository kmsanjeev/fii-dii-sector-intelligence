"""P024 marriage governance and synthesis regression tests."""

from __future__ import annotations

from pathlib import Path

from engines.ai.knowledge.marriage_governance import build_phase_bundle, export_phase_bundle, validate_bundle
from engines.intelligence.marriage_evidence_aggregation import (
    ConfidenceBand,
    EvidenceDirection,
    MarriageEvidenceAggregator,
)
from engines.intelligence.marriage_synthesis_engine import MarriageSynthesisEngine
from engines.marriage.m001_existing_marriage_logic_inventory import inventory_repository


def test_phase_bundle_is_valid() -> None:
    bundle = build_phase_bundle()
    validation = validate_bundle(bundle)

    assert bundle["meta"]["phase"] == "VEDA-P024"
    assert validation["is_valid"] is True
    assert validation["errors"] == []
    assert bundle["summary"]["approved_core_promotions"] == 0
    assert bundle["summary"]["production_activation"] == 0
    assert bundle["summary"]["sources_discovered"] >= 8
    assert bundle["summary"]["claims_extracted"] >= 6


def test_export_phase_bundle_writes_canonical_artifacts(tmp_path: Path) -> None:
    from engines.ai.knowledge import marriage_governance as governance

    root = tmp_path
    validation_dir = tmp_path / "validation" / "marriage"

    fake_bundle = {
        "meta": {"phase": "VEDA-P024"},
        "existing_logic_inventory": {"files_scanned": 1, "files_with_matches": 1},
        "source_inventory": [{"source_id": "VEDA-SRC-000001"}],
        "source_quality": {"classical_primary_sources": 1, "commentaries": 0, "reference_editions": 0, "traditional_secondary_sources": 0, "modern_practitioner_sources": 0, "independent_works": 1, "independent_source_families": 1},
        "claim_provenance": [{"claim_id": "VEDA-P024-CLM-000001", "passage_id": "VEDA-PSG-000001", "method_variant": "X"}],
        "evidence_records": [{"evidence_id": "VEDA-P024-EVID-000001", "source_layer": "D1", "evidence_type": "SUPPORTING", "direction": "SUPPORTING", "confidence": "HIGH", "validation_status": "APPROVED"}],
        "evidence_ontology": {"support_categories": ["MARRIAGE_BHAVA"]},
        "research_programme": [{"mission_id": "VEDA-P024-MIS-000001"}],
        "validation_corpus": [{"case_id": "P024-CASE-001", "scenario": "support", "expected_state": "SUPPORTED"}],
        "prediction_backtesting_contract": {"contract_id": "VEDA-P024-PREDICTION-CONTRACT"},
        "capability_readiness": [{"capability": "Marriage Backtesting", "state": "READY"}],
        "regression_plan": ["test"],
        "rag_integration": {"trust_tiers": ["APPROVED_CORE"]},
        "approved_core_promotion_candidates": [{"candidate": "7th Bhava methodology"}],
        "regression_scope": {"focused_tests": "tests/test_veda_p024_marriage.py"},
        "summary": {
            "files_scanned": 1,
            "files_with_matches": 1,
            "sources_discovered": 1,
            "claims_extracted": 1,
            "contradictions_found": 0,
            "approved_core_promotions": 0,
            "production_activation": 0,
        },
    }

    def fake_build_phase_bundle(root: Path | None = None) -> dict[str, object]:
        return fake_bundle

    def fake_write_inventory(root: Path | None = None, output_path: Path | None = None) -> Path:
        path = (output_path or root / "m001_inventory.json") if root is not None else validation_dir / "m001_inventory.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        return path

    governance.build_phase_bundle = fake_build_phase_bundle  # type: ignore[assignment]
    governance.write_inventory = fake_write_inventory  # type: ignore[assignment]
    written = export_phase_bundle(root=root, validation_dir=validation_dir)

    assert written
    assert (validation_dir / "p024_marriage_bundle.json").exists()
    assert (validation_dir / "p024_marriage_summary.json").exists()
    assert (root / "docs" / "current-state" / "p024" / "VEDA-P024-00_EXECUTIVE_SUMMARY.md").exists()
    assert (root / "docs" / "current-state" / "p024" / "m001_inventory.json").exists()


def test_inventory_repository_classifies_marriage_surfaces(tmp_path: Path) -> None:
    governed = tmp_path / "engines" / "marriage" / "sample.py"
    governed.parent.mkdir(parents=True, exist_ok=True)
    governed.write_text("marriage = True\n# 7th house and navamsha\n", encoding="utf-8")

    shadow = tmp_path / "tests" / "test_sample.py"
    shadow.parent.mkdir(parents=True, exist_ok=True)
    shadow.write_text("relationship = 'shadow'\n", encoding="utf-8")

    research = tmp_path / "data" / "veda" / "research" / "astrology" / "sample.md"
    research.parent.mkdir(parents=True, exist_ok=True)
    research.write_text("manglik relationship research\n", encoding="utf-8")

    inventory = inventory_repository(root=tmp_path)

    assert inventory["files_with_matches"] == 3
    classifications = {record["classification"] for record in inventory["records"]}
    assert "GOVERNED" in classifications
    assert "SHADOW" in classifications
    assert "RESEARCH_ONLY" in classifications


def test_evidence_aggregation_preserves_conflicts_and_cancellations() -> None:
    aggregator = MarriageEvidenceAggregator()
    aggregator.add_evidence(
        source_layer="D1",
        evidence_type="FOUNDATION",
        direction=EvidenceDirection.SUPPORTING,
        claim="D1 supports the marriage foundation",
        confidence=ConfidenceBand.HIGH,
    )
    aggregator.add_evidence(
        source_layer="D9",
        evidence_type="VARGA",
        direction=EvidenceDirection.OPPOSING,
        claim="D9 adds tension",
        confidence=ConfidenceBand.MODERATE,
    )
    aggregator.add_evidence(
        source_layer="YOGA_DOSHA",
        evidence_type="DOSHA",
        direction=EvidenceDirection.CANCELLING,
        claim="Cancellation modifies the dosha signal",
    )

    conflicts = aggregator.detect_conflicts()
    synthesis = aggregator.synthesize_narrative()

    assert conflicts
    assert synthesis["supporting_count"] == 1
    assert synthesis["opposing_count"] == 1
    assert synthesis["cancelling_count"] == 1
    assert synthesis["overall_state"] in {"CONFLICTED", "SUPPORTED_WITH_CANCELLATION"}


def test_synthesis_engine_separates_layers_and_stays_shadow_only() -> None:
    engine = MarriageSynthesisEngine()
    output = engine.synthesize(
        subject_id="SUBJECT-001",
        natal_factors={"seventh_house": True, "seventh_lord": "Venus"},
        d9_facts={"d1_d9_alignment": False},
        dasha_context={"relationship_window": True},
        transit_context={"challenge": True},
        yoga_facts={"manglik_present": True, "cancellation_present": True},
        strength_facts={"validated": False},
        prediction_mode="SHADOW",
    )

    assert output.domain == "MARRIAGE"
    assert output.prediction_mode == "SHADOW"
    assert output.prediction_state == "SHADOW"
    assert output.interpretation_status == "SHADOW_ONLY"
    assert output.experimental is True
    assert output.shadow is True
    assert output.backtesting_ready is True
    assert output.supporting_evidence
    assert output.opposing_evidence
    assert output.cancelling_evidence
    assert output.explainability_trace[0] == "MARRIAGE SYNTHESIS"


def test_prediction_record_supports_backtesting() -> None:
    engine = MarriageSynthesisEngine()
    record = engine.create_prediction_record(
        prediction_type="SHADOW_PREDICTION",
        prediction_state="SHADOW",
        window_start="2026-08-14T00:00:00Z",
        window_end="2026-09-14T00:00:00Z",
        confidence_state="RESEARCH_REQUIRED",
        rule_versions=["P024_SHADOW_1"],
        supporting_evidence=[{"claim": "support"}],
        opposing_evidence=[{"claim": "oppose"}],
        cancelling_evidence=[],
    )
    record.record_outcome("SHADOW")

    assert record.domain == "MARRIAGE"
    assert record.actual_outcome == "SHADOW"
    assert record.comparison_result == "MATCH"
    assert record.to_dict()["prediction_type"] == "SHADOW_PREDICTION"
