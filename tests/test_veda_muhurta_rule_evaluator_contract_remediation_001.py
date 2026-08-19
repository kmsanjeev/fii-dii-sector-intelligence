"""Focused remediation tests for VEDA-MUHURTA-RULE-EVALUATOR-CONTRACT-REMEDIATION-001."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.veda_muhurta_predicate_evaluator import PredicateResult, evaluate_predicate, validate_predicate
from scripts.veda_muhurta_rule_evaluator_contract_remediation_001 import (
    DECISION,
    build_artifacts,
    adapt_p032_facts,
    factor_registry,
    predicate_schema,
    remediate_contract,
)
from engines.ai.knowledge.muhurta_foundation import compute_panchanga_facts


def test_v1_contracts_remain_and_v2_is_hashable():
    result = build_artifacts()
    assert result["audit"]["decision"] == DECISION
    assert len(result["business"]["contract_hash_full"]) == 64
    assert len(result["education"]["contract_hash_full"]) == 64
    assert result["business"]["supersedes"]["contract_hash"] == "941E9ECB9960652C"
    assert result["education"]["supersedes"]["contract_hash"] == "FFE718B6AAA8D6C9"


def test_only_platform_and_scope_rules_are_machine_ready():
    business = remediate_contract("BUSINESS_OPENING_INAUGURATION")
    education = remediate_contract("EDUCATION_COMMENCEMENT")
    assert business["machine_rule_ids"] == ["MUH-BIZ-PANCHANGA-INPUT-001"]
    assert education["machine_rule_ids"] == ["MUH-EDU-PANCHANGA-INPUT-001", "MUH-EDU-ROUTINE-SCOPE-001"]
    assert "MUH-BIZ-NAK-001" in business["source_partial_rule_ids"]
    assert "MUH-EDU-NAK-001" in education["source_partial_rule_ids"]
    assert business["recommendation_engine_state"] == "PARTIAL_MACHINE_CONTRACT"


def test_predicate_operators_and_missing_values_are_categorical():
    cases = [
        ({"factor_id": "x", "operator": "EQ", "expected_value": 2}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "NEQ", "expected_value": 2}, {"x": 3}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "IN", "expected_set": [1, 2]}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "NOT_IN", "expected_set": [1, 2]}, {"x": 3}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "LT", "expected_value": 3}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "LTE", "expected_value": 2}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "GT", "expected_value": 1}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "GTE", "expected_value": 2}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "BETWEEN", "range": [1, 3]}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "EXISTS"}, {"x": 2}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "NOT_EXISTS"}, {}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "BOOLEAN_TRUE"}, {"x": True}, PredicateResult.TRUE),
        ({"factor_id": "x", "operator": "BOOLEAN_FALSE"}, {"x": False}, PredicateResult.TRUE),
        ({"operator": "ALL_OF", "children": [{"factor_id": "a", "operator": "EQ", "expected_value": 1}, {"factor_id": "b", "operator": "EQ", "expected_value": 2}]}, {"a": 1, "b": 2}, PredicateResult.TRUE),
        ({"operator": "ANY_OF", "children": [{"factor_id": "a", "operator": "EQ", "expected_value": 1}, {"factor_id": "b", "operator": "EQ", "expected_value": 2}]}, {"a": 0, "b": 2}, PredicateResult.TRUE),
        ({"operator": "NOT", "child": {"factor_id": "a", "operator": "EQ", "expected_value": 1}}, {"a": 2}, PredicateResult.TRUE),
    ]
    for predicate, factors, expected in cases:
        assert evaluate_predicate(predicate, factors) == expected
    assert evaluate_predicate({"factor_id": "missing", "operator": "EQ", "expected_value": 1}, {}) == PredicateResult.NOT_EVALUABLE


def test_no_dynamic_code_and_schema_are_explicit():
    assert validate_predicate({"factor_id": "x", "operator": "EQ", "expression": "x == 1"}) == ["arbitrary_expression_forbidden"]
    schema = predicate_schema()
    assert schema["arbitrary_expression_allowed"] is False
    assert schema["python_code_allowed"] is False
    assert factor_registry()["calculation_logic_changed"] is False


def test_p032_adapter_is_semantics_preserving_and_missing_honest():
    local = datetime(2026, 8, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    facts = compute_panchanga_facts(0, 30, local)
    adapted = adapt_p032_facts(facts, [], "FORMAL_COURSE_COMMENCEMENT")
    assert adapted["PANCHANGA_FACTS_AVAILABLE"] is True
    assert adapted["NAKSHATRA"] == facts["nakshatra"]["index"]
    assert adapted["KARANA"] == facts["karana"]["number"]
    assert adapted["ACTIVITY_SUBSCOPE"] == "FORMAL_COURSE_COMMENCEMENT"
    incomplete = dict(facts)
    incomplete.pop("yoga")
    assert adapt_p032_facts(incomplete, ["transition"]) ["PANCHANGA_FACTS_AVAILABLE"] is False


def test_generated_artifacts_are_json_serializable_and_deterministic():
    first = build_artifacts()
    first_json = json.dumps(first, sort_keys=True, default=str)
    second = build_artifacts()
    second_json = json.dumps(second, sort_keys=True, default=str)
    assert first_json == second_json
