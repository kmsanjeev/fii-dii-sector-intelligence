"""Focused tests for VEDA-MUHURTA-MVP-SOURCE-SEMANTICS-HARDENING-001."""

import json
from pathlib import Path

from scripts.veda_muhurta_mvp_source_semantics_hardening_001 import (
    NAKSHATRA_INDEXES,
    build,
    derive_factors,
    emit,
)
from scripts.veda_muhurta_predicate_evaluator import PredicateResult, evaluate_predicate


def test_source_witness_and_partial_decisions_are_explicit():
    result = build()
    assert result["bundle_validation"]["is_valid"] is True
    assert result["decision"] == "MUHURTA_MVP_SOURCE_SEMANTICS_PARTIAL"
    assert result["ready_activities"] == []
    assert result["engine_handoff_created"] is False
    assert result["business"]["supersedes"]["legacy_v1_hash"] == "941E9ECB9960652C"
    assert result["education"]["supersedes"]["legacy_v1_hash"] == "FFE718B6AAA8D6C9"


def test_direct_nakshatra_value_set_is_machine_evaluable():
    result = build()
    rule = next(r for r in result["business"]["rules"] if r["rule_id"] == "MUH-BIZ-NAK-001")
    predicate = {key: rule[key] for key in ("factor_id", "operator", "expected_set")}
    assert rule["expected_set"] == list(NAKSHATRA_INDEXES.values())
    assert evaluate_predicate(predicate, {"NAKSHATRA": 12}) == PredicateResult.TRUE
    assert evaluate_predicate(predicate, {"NAKSHATRA": 1}) == PredicateResult.FALSE
    assert evaluate_predicate(predicate, {}) == PredicateResult.NOT_EVALUABLE


def test_business_karana_values_are_narrow_and_education_stays_partial():
    result = build()
    business = result["business"]
    education = result["education"]
    assert {"MUH-BIZ-KARANA-TRADE-001", "MUH-BIZ-KARANA-ESTABLISHMENT-001"}.issubset(business["machine_rule_ids"])
    assert "MUH-BIZ-TITHI-KARANA-001" in business["source_partial_rule_ids"]
    assert "MUH-EDU-TITHI-KARANA-001" in education["source_partial_rule_ids"]
    assert all(rule["recommendation_effect"] != "HARD_EXCLUSION" for rule in business["rules"] + education["rules"])


def test_derivation_is_existing_sequence_only_and_does_not_change_p032():
    factors = derive_factors(nakshatra=0, tithi=0, karana=7)
    assert factors["NAKSHATRA"] == 0
    assert factors["TITHI_CLASS"] == "NANDA"
    assert factors["KARANA_NAME"] == "VANIJA"
    assert factors["PANCHANGA_FACTS_AVAILABLE"] is True


def test_emitted_artifacts_are_deterministic(tmp_path):
    first = build()
    emit(first)
    first_text = Path("docs/current-state/muhurta-mvp-source-semantics-hardening-001/10_BUSINESS_CONTRACT_V3.json").read_text(encoding="utf-8")
    second = build()
    emit(second)
    second_text = Path("docs/current-state/muhurta-mvp-source-semantics-hardening-001/10_BUSINESS_CONTRACT_V3.json").read_text(encoding="utf-8")
    assert json.loads(first_text) == json.loads(second_text)
