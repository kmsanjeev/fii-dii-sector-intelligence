from __future__ import annotations

from pathlib import Path

from engines.ai.knowledge.career_wealth_governance import (
    build_phase_bundle,
    export_phase_bundle,
    validate_bundle,
)


def test_p020_bundle_keeps_shadow_only_domain_scope():
    bundle = build_phase_bundle()

    assert bundle["summary"]["registry_rows"] == 4
    assert bundle["summary"]["high_stakes_domains"] == 3
    assert bundle["summary"]["validation_fixtures"] == 24
    assert bundle["summary"]["shadow_mismatches"] == 0

    domain_ids = [row["domain_id"] for row in bundle["domain_registry"]]
    assert domain_ids == ["CAREER", "FINANCE", "D10_CALCULATION", "D10_INTERPRETATION"]
    assert next(row for row in bundle["domain_registry"] if row["domain_id"] == "FINANCE")["activation_status"] == "INACTIVE"
    assert next(row for row in bundle["capability_status"] if row["domain_id"] == "D10_INTERPRETATION")["implementation_status"] == "SHADOW_ONLY"


def test_p020_bundle_distinguishes_evidence_fact_and_conflict():
    bundle = build_phase_bundle()
    evidence_types = {row["evidence_type"] for row in bundle["evidence_records"]}
    conflict_statuses = {row["status"] for row in bundle["conflict_framework"]}

    assert evidence_types == {"SUPPORTING", "CONDITIONAL", "OPPOSING", "CONTEXTUAL"}
    assert conflict_statuses == {"CONTEXT_DEPENDENT", "BLOCKED", "RESEARCH_REQUIRED"}
    assert bundle["evidence_contract"]["distinguish_fact_rule_signal"] is True
    assert "NATAL" in bundle["evidence_contract"]["source_layers"]
    assert "TEMPORARY_RESEARCH" in bundle["evidence_contract"]["source_layers"]


def test_p020_shadow_validation_matches_canonical_d10_formula():
    bundle = build_phase_bundle()
    report = validate_bundle(bundle)

    assert report["is_valid"] is True
    assert report["shadow_mismatches"] == []
    assert bundle["shadow_validation"][0]["classification"] == "MATCH"
    assert bundle["shadow_validation"][1]["classification"] == "MATCH"


def test_p020_export_writes_bundle_registry_validation_and_docs(tmp_path):
    validation_dir = tmp_path / "validation"

    written = export_phase_bundle(root=tmp_path, validation_dir=validation_dir)

    expected = {
        validation_dir / "p020_career_bundle.json",
        validation_dir / "p020_career_registry.json",
        validation_dir / "p020_career_validation.json",
        validation_dir / "p020_career_capability_status.json",
        validation_dir / "p020_career_research_missions.json",
        tmp_path / "docs" / "current-state" / "p020" / "VEDA-P020-00_EXECUTIVE_SUMMARY.md",
        tmp_path / "docs" / "current-state" / "p020" / "VEDA-P020-04_FINAL_ACCEPTANCE.md",
    }

    assert expected.issubset(set(written))
    for path in expected:
        assert Path(path).exists()

