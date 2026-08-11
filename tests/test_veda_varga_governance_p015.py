import json
from pathlib import Path

import jsonschema

from engines.ai.knowledge.varga_governance import (
    build_phase_bundle,
    canonical_varga_fact,
    export_phase_bundle,
    validate_bundle,
    varga_sign,
)


def test_p015_registry_covers_current_p004_surface():
    bundle = build_phase_bundle()
    assert [row["varga_id"] for row in bundle["varga_registry"]] == [
        "D1", "D2", "D3", "D4", "D7", "D9", "D10", "D11", "D12", "D16", "D20", "D30", "D60"
    ]
    assert bundle["summary"]["vargas_inventoried"] == 13
    assert bundle["summary"]["vargas_calculation_validated"] == 3
    assert bundle["summary"]["vargas_with_conditions"] == 10


def test_p015_boundary_formulas_are_deterministic():
    assert varga_sign(60.0, 9, "navamsa") == "Libra"
    assert varga_sign(63.333334, 9, "navamsa") == "Scorpio"
    assert varga_sign(60.0, 10, "dasamsa") == "Gemini"
    assert varga_sign(89.999999, 10, "dasamsa") == "Pisces"


def test_p015_emits_canonical_varga_fact_with_runtime_boundary():
    fact = canonical_varga_fact("VEDA-GRAHA-JUPITER", 95.0, "D9")
    assert fact["varga"] == "D9"
    assert fact["planet_id"] == "VEDA-GRAHA-JUPITER"
    assert fact["runtime_version"] == "P012_CANONICAL_RUNTIME"
    assert fact["calculation_rule_id"] == "VEDA-RUL-VARGA-009"
    assert fact["interpretation_status"] == "RESEARCHING"


def test_p015_shadow_matches_current_runtime_formula():
    report = validate_bundle(build_phase_bundle())
    assert report["is_valid"] is True
    assert report["shadow_mismatches"] == []


def test_p015_preserves_interpretation_and_production_boundaries(tmp_path):
    bundle = build_phase_bundle()
    assert all(row["production_activation"] == "NOT_EXECUTED" for row in bundle["varga_capability_status"])
    assert bundle["summary"]["approved_core_changed"] == "NO"
    assert bundle["summary"]["production_planetary_calculation_semantics_changed"] == "NO"
    assert bundle["summary"]["production_interpretation_semantics_changed"] == "NO"
    assert any(row["varga"] == "D60" and row["calculation"] == "CALCULATION_VALIDATED_WITH_CONDITIONS" for row in bundle["varga_capability_status"])


def test_p015_machine_readable_artifacts_and_fact_schema():
    bundle = build_phase_bundle()
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "astrology" / "varga_fact.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(canonical_varga_fact("VEDA-GRAHA-SUN", 0.0, "D9"), schema)
    assert len(bundle["varga_research_missions"]) == 4
    assert len(bundle["varga_claims"]) == 4
    assert len(bundle["varga_rules"]) == 13
    assert len(bundle["varga_conflicts"]) == 2
