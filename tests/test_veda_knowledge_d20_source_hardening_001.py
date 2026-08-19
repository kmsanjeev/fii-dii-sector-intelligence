"""Focused tests for the bounded D20 source-hardening programme."""

import hashlib

from engines.ai.knowledge.source_witness_governance import validate_bundle
from engines.ai.knowledge.varga_governance import varga_sign
from scripts.veda_knowledge_d20_source_hardening_001 import (
    OUT,
    STARTS,
    build,
    build_hardening_bundle,
    emit,
    mapping_matrix,
)


METHOD = "d20_vimshamsha_bphs_category_start_v1"


def test_source_witness_standard_is_used_and_bundle_validates():
    bundle = build_hardening_bundle()
    report = validate_bundle(bundle)
    assert bundle.standard_id == "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
    assert report.is_valid
    assert not report.errors
    assert bundle.works and bundle.witnesses and bundle.editions and bundle.passages
    assert bundle.assertions and bundle.variants and bundle.contracts
    assert {passage.source_layer.value for passage in bundle.passages} >= {"ORIGINAL_TEXT", "TRANSLATION"}


def test_bphs_atomic_dimensions_separate_resolved_and_unstated_rules():
    result = build()
    assertion_model = result["bundle"].assertions
    statements = {item.assertion_group: item.statement for item in assertion_model}
    assert "twenty Vimshamsha parts" in statements["D20_DIVISION_COUNT"]
    assert "1°30′" in statements["D20_DIVISION_SIZE"]
    assert "category starts" not in statements["D20_SIGN_CLASS_START"] or "Aries" in statements["D20_SIGN_CLASS_START"]
    assert "does not explicitly state" in statements["D20_DESTINATION_SEQUENCE"]
    assert "does not explicitly state" in statements["D20_COUNT_DIRECTION"]
    assert result["decision"] == "D20_SOURCE_CONTRACT_PARTIALLY_RESOLVED_FREEZE"


def test_mapping_matrix_is_complete_mathematically_but_not_textually():
    result = build()
    rows = mapping_matrix()
    assert len(rows) == 240
    assert {row["input_sign_class"] for row in rows} == set(STARTS)
    assert all(row["source_destination"] is None for row in rows)
    assert result["comparison"]["current_matches_independent_sequential_inference"] is True
    assert result["comparison"]["source_destination_comparison"] == "NOT_ASSESSABLE_DESTINATION_NOT_STATED"
    assert result["comparison"]["legacy_differences_vs_selected_route"] == 220


def test_category_starts_and_boundary_behavior_are_explicit():
    assert [varga_sign(sign * 30 + 0.1, 20, METHOD) for sign in (0, 3, 6, 9)] == ["Aries"] * 4
    assert [varga_sign(sign * 30 + 0.1, 20, METHOD) for sign in (1, 4, 7, 10)] == ["Sagittarius"] * 4
    assert [varga_sign(sign * 30 + 0.1, 20, METHOD) for sign in (2, 5, 8, 11)] == ["Leo"] * 4
    assert varga_sign(1.5, 20, METHOD) == "Taurus"
    assert varga_sign(1.499999, 20, METHOD) == "Aries"
    assert varga_sign(359.999999, 20, METHOD) == "Pisces"
    assert varga_sign(30.0, 20, METHOD) == "Sagittarius"


def test_contract_candidate_is_deterministic_and_non_production():
    first = build()["contract"]
    second = build()["contract"]
    assert first == second
    assert first["contract_hash"] == "20CF6C0BDAF29BF109243673E51EE377908402569EDF76096391D78B1EFE32A1"
    assert first["status"] == "PARTIAL_SOURCE_CONTRACT"
    assert first["production_bound"] is False
    assert first["destination_policy"] == "NOT_STATED; no complete source mapping"


def test_variants_and_source_gap_are_not_flattened():
    result = build()
    groups = {variant.assertion_group for variant in result["bundle"].variants}
    assert "D20_DESTINATION_SEQUENCE" in groups
    assert "D20_RUNTIME_DESTINATION_INFERENCE" in groups
    assert "D20_SOURCE_CONTRACT" in groups
    assert any(conflict.conflict_type.value == "UNRESOLVED" for conflict in result["bundle"].conflicts)
    assert result["bundle"].contracts[-1].status.value == "SOURCE_LIMITED"


def test_governance_boundaries_remain_unchanged():
    governance = build()["governance"]
    assert governance["d20_runtime_changed"] is False
    assert governance["d20_default_changed"] is False
    assert governance["d20_interpretation_changed"] is False
    assert governance["interpretation_status"] == "NOT_VALIDATED"
    assert governance["ashtakavarga_changed"] is False
    assert governance["p032_changed"] is False
    assert governance["rag_changed"] is False
    assert governance["approved_core_before"] == governance["approved_core_after"] == 17
    assert governance["provider_calls"] == 0


def test_exports_are_deterministic():
    emit(build())
    names = sorted(path.name for path in OUT.iterdir() if path.is_file())
    first = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
    emit(build())
    second = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in names}
    assert first == second
    assert len(names) == 19
    assert "11_D20_CONTRACT_CANDIDATE.json" in names
    assert "05_DESTINATION_MAPPING_MATRIX.json" in names
