"""Focused tests for VEDA-MUHURTA-ACTIVITY-RULE-CONTRACTS-001."""

import json

from scripts.veda_muhurta_activity_rule_contracts_001 import (
    OUT,
    acceptance,
    build_result,
    emit,
)


def test_three_mvp_contracts_and_scopes_are_preserved():
    result = build_result()
    assert set(result["contracts"]) == {
        "BUSINESS_OPENING_INAUGURATION",
        "EDUCATION_COMMENCEMENT",
        "RELIGIOUS_SPIRITUAL_CEREMONY",
    }
    assert all(contract["activity_scope"]["included"] for contract in result["contracts"].values())
    assert result["contracts"]["BUSINESS_OPENING_INAUGURATION"]["activity_scope"]["excluded"]
    assert "routine daily studying" in result["contracts"]["EDUCATION_COMMENCEMENT"]["activity_scope"]["excluded"]


def test_source_witness_lineage_and_rule_contract_fields_are_complete():
    result = build_result()
    assert result["source_matrix"]
    for record in result["source_matrix"]:
        assert record["rule_to_assertion"].startswith("VEDA-SWW-ASSERTION-")
        assert record["assertion_to_passage"].startswith("VEDA-SWW-PASSAGE-")
        assert record["passage_to_edition"].startswith("VEDA-SWW-EDITION-")
        assert record["edition_to_witness"].startswith("VEDA-SWW-WITNESS-")
        assert record["witness_to_work"].startswith("VEDA-SWW-WORK-")
        assert record["lineage"].startswith("ACTIVITY_RULE_CONTRACT")
        assert record["lineage_status"] == "LEGACY_SOURCE_REGISTRY_RECONCILED"
        assert record["source_witness_standard_id"] == "VEDA-KNOWLEDGE-SOURCE-WITNESS-STANDARD-001"
        assert record["full_source_text_committed"] is False
    for contract in result["contracts"].values():
        for rule in contract["rules"]:
            assert rule["rule_id"] in contract["rule_ids"]
            assert rule["rule_class"] in {
                "HARD_EXCLUSION", "HARD_REQUIREMENT", "STRONG_NEGATIVE",
                "PREFERENCE_NEGATIVE", "NEUTRAL", "PREFERENCE_POSITIVE",
                "STRONG_POSITIVE", "PERSONAL_FACTOR", "CONTEXT_DEPENDENT",
                "SOURCE_VARIANT", "UNRESOLVED",
            }
            assert rule["production_activation"] is False


def test_precedence_abstention_and_no_scoring():
    result = build_result()
    for contract in result["contracts"].values():
        assert contract["precedence_policy"][0] == "HARD_EXCLUSION"
        assert "SOURCE_CONFLICT_UNRESOLVED" in contract["abstention_policy"]
        assert contract["arbitrary_numeric_score"] is False
        assert contract["hidden_weights"] is False
    assert result["evaluator_design"]["numeric_score"] is False
    assert result["evaluator_design"]["llm_rule_execution"] is False


def test_readiness_is_partial_and_personal_bala_remains_gated():
    result = build_result()
    assert result["contracts"]["BUSINESS_OPENING_INAUGURATION"]["recommendation_engine_state"] == "ENGINE_READY_WITH_CONDITION"
    assert result["contracts"]["EDUCATION_COMMENCEMENT"]["recommendation_engine_state"] == "ENGINE_READY_WITH_CONDITION"
    assert result["contracts"]["RELIGIOUS_SPIRITUAL_CEREMONY"]["recommendation_engine_state"] == "SOURCE_HARDENING_REQUIRED"
    assert result["decision"]["programme_decision"] == "MUHURTA_PARTIAL_ACTIVITY_CONTRACTS_READY"
    assert result["personal_factors"]["activated"] is False
    assert result["next_programme"]["automatically_started"] is False


def test_parallel_state_and_two_run_contract_determinism():
    result = build_result()
    emit(result)
    first = {path.name: path.read_bytes() for path in OUT.iterdir() if path.is_file()}
    emit(result)
    second = {path.name: path.read_bytes() for path in OUT.iterdir() if path.is_file()}
    assert first == second
    assert json.loads((OUT / "03_BUSINESS_OPENING_RULE_CONTRACT.json").read_text(encoding="utf-8"))["production_bound"] is False
    assert result["production"]["approved_core_before"] == result["production"]["approved_core_after"] == 17
    assert len(acceptance(result)) == 30
    assert all(row["status"] == "PASS" for row in acceptance(result))
