"""Focused tests for VEDA-KNOWLEDGE-SHADBALA-SOURCE-HARDENING-001."""

import json
from pathlib import Path

from scripts.veda_knowledge_shadbala_source_hardening_001 import (
    SOURCE_DIG_MAX_HOUSE,
    SOURCE_NAISARGIKA,
    build_witness_bundle,
    build_result,
    independent_dig_from_minimum,
    independent_naisargika,
)


ROOT = Path(__file__).parents[1]
OUT = ROOT / "docs/current-state/knowledge-shadbala-source-hardening-001"


def test_source_witness_bundle_is_valid_and_component_level():
    result = build_result()
    assert result["source_witness_validation"]["is_valid"] is True
    assert len(result["formula_contracts"]) >= 7
    assert result["decision"] == "SHADBALA_IMPLEMENTATION_SOURCE_MISMATCH_REMEDIATION_REQUIRED"


def test_source_contract_and_runtime_are_not_promoted_or_changed():
    result = build_result()
    assert result["governance"]["production_shadbala_changed"] is False
    assert result["governance"]["approved_core_before"] == 17
    assert result["governance"]["approved_core_after"] == 17
    assert result["governance"]["rag_documents_before"] == result["governance"]["rag_documents_after"] == 1205


def test_independent_naisargika_oracle_uses_source_order():
    assert independent_naisargika("Venus") > independent_naisargika("Jupiter")
    assert SOURCE_NAISARGIKA["Sun"] == 60.0
    assert round(sum(SOURCE_NAISARGIKA.values()), 4) == 240.0


def test_independent_dig_oracle_boundaries():
    assert SOURCE_DIG_MAX_HOUSE["Venus"] == 4
    assert independent_dig_from_minimum("Sun", 270.0, 90.0) == 60.0
    assert independent_dig_from_minimum("Sun", 90.0, 90.0) == 0.0


def test_runtime_comparison_exposes_material_mismatches():
    comparison = build_result()["runtime_comparison"]
    assert comparison["summary"]["naisargika_matches"] < comparison["summary"]["naisargika_cases"]
    assert comparison["summary"]["dig_max_mapping_matches"] < comparison["summary"]["dig_cases"]
    assert comparison["summary"]["material_mismatch_found"] is True


def test_unit_and_dependency_gates_are_explicit():
    result = build_result()
    contracts = {item["component_id"]: item for item in result["formula_contracts"]}
    assert contracts["NAISARGIKA_BALA"]["unit"] == "RUPA_LABEL_CURRENTLY; VIRUPA_SOURCE"
    assert result["dependency_graph"]["ASPECTS"]["status"] == "MISSING_FOUNDATION"
    assert result["dependency_graph"]["PLANET_MOTION"]["status"] == "PARTIAL"


def test_no_cross_tradition_hybrid_and_no_prediction_use():
    bundle = build_witness_bundle()
    result = build_result()
    assert any(
        variant.source_family == "SARAVALI_OPEN_DOCUMENTATION"
        and variant.canonical_status.value == "SUPPORTED_VARIANT"
        for variant in bundle.variants
    )
    assert not any(
        variant.canonical_status.value == "SUPERSEDED_INVALID_HYBRID"
        for variant in bundle.variants
    )
    assert result["governance"]["prediction_changed"] is False
    assert result["governance"]["ml"] == "LOCKED"


def test_emitted_acceptance_is_deterministic_after_build():
    from scripts.veda_knowledge_shadbala_source_hardening_001 import emit

    result = build_result()
    emit(result)
    first = {p.name: p.read_bytes() for p in OUT.iterdir() if p.is_file()}
    emit(result)
    second = {p.name: p.read_bytes() for p in OUT.iterdir() if p.is_file()}
    assert first == second
    acceptance = json.loads((OUT / "14_FINAL_ACCEPTANCE.json").read_text(encoding="utf-8"))
    assert acceptance["fail"] == 0
    assert acceptance["blocked"] == 0
