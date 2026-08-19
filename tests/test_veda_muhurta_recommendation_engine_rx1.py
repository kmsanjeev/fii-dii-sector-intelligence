from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from engines.ai.knowledge import muhurta_recommendation_engine_rx1 as engine


LOCAL = datetime(2026, 8, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
LOCATION = {"latitude": 28.6139, "longitude": 77.2090, "timezone_name": "Asia/Kolkata"}


def _facts(*, tithi: int = 6, nakshatra: int = 0, karana_name: str = "Vanija"):
    return {
        "vara": {"index": 0},
        "tithi": {"index": tithi},
        "nakshatra": {"index": nakshatra},
        "yoga": {"index": 0},
        "karana": {"number": 7, "name": karana_name},
    }


def _request(activity: str, **extra):
    return {
        "activity_id": activity,
        "candidate_start": LOCAL,
        "location": LOCATION,
        "p032_facts": _facts(),
        "transition_boundaries": [],
        **extra,
    }


def test_v4_contracts_are_loaded_and_hash_checked():
    business = engine.load_validated_contract("BUSINESS_OPENING_INAUGURATION")
    education = engine.load_validated_contract("EDUCATION_COMMENCEMENT")
    assert business["contract_hash_full"] == engine.CONTRACTS["BUSINESS_OPENING_INAUGURATION"]["hash"]
    assert education["contract_hash_full"] == engine.CONTRACTS["EDUCATION_COMMENCEMENT"]["hash"]


def test_hash_mismatch_fails_closed(monkeypatch):
    original = engine.CONTRACTS["BUSINESS_OPENING_INAUGURATION"]["hash"]
    monkeypatch.setitem(engine.CONTRACTS["BUSINESS_OPENING_INAUGURATION"], "hash", "BAD")
    with pytest.raises(engine.ContractValidationError, match="hash mismatch"):
        engine.load_validated_contract("BUSINESS_OPENING_INAUGURATION")
    monkeypatch.setitem(engine.CONTRACTS["BUSINESS_OPENING_INAUGURATION"], "hash", original)


def test_business_evaluates_ready_rules_and_discloses_gaps_without_score():
    result = engine.recommend(_request("BUSINESS_OPENING_INAUGURATION"))
    assert result["recommendation_state"] == "MIXED_FACTORS"
    assert result["supporting_factors"]
    assert {gap["rule_id"] for gap in result["unevaluated_source_gaps"]} == {
        "MUH-BIZ-VARA-YOGA-GAP-001",
        "MUH-BIZ-TITHI-SCOPE-GAP-001",
    }
    assert "score" not in str(result).lower()
    assert result["source_trace"]["contract_hash_full"] == engine.CONTRACTS["BUSINESS_OPENING_INAUGURATION"]["hash"]


def test_education_formal_commencement_uses_tithi_and_caution():
    result = engine.recommend(_request("EDUCATION_COMMENCEMENT", activity_subscope="FORMAL_COURSE_COMMENCEMENT"))
    assert result["recommendation_state"] == "SUPPORTED_WITH_CAUTION"
    assert "education" in result["caution"]["activity"].lower()
    assert "institutional" in result["consultation_guidance"].lower()


def test_education_routine_study_abstains_on_scope():
    result = engine.recommend(_request("EDUCATION_COMMENCEMENT", activity_subscope="ROUTINE_DAILY_STUDY"))
    assert result["recommendation_state"] == "ABSTAIN"
    assert result["abstention_reason"] == "ACTIVITY_SCOPE_MISMATCH"


def test_business_excluded_activity_abstains_on_scope():
    result = engine.recommend(_request("BUSINESS_OPENING_INAUGURATION", activity_subscope="investment selection"))
    assert result["recommendation_state"] == "ABSTAIN"
    assert result["abstention_reason"] == "ACTIVITY_SCOPE_MISMATCH"


def test_missing_p032_dependency_is_governed_abstention():
    result = engine.recommend({"activity_id": "BUSINESS_OPENING_INAUGURATION", "candidate_start": LOCAL, "location": LOCATION})
    assert result["recommendation_state"] == "ABSTAIN"
    assert result["abstention_reason"] == "CALCULATION_DEPENDENCY_UNAVAILABLE"


def test_unsupported_activity_is_not_silently_activated():
    result = engine.recommend(_request("RELIGIOUS_CEREMONY"))
    assert result["recommendation_state"] == "ABSTAIN"
    assert result["abstention_reason"] == "NOT_YET_ENGINE_READY"


def test_computed_p032_path_is_deterministic():
    request = {
        "activity_id": "EDUCATION_COMMENCEMENT",
        "candidate_start": LOCAL,
        "location": LOCATION,
        "sun_sidereal_longitude": 0,
        "moon_sidereal_longitude": 30,
        "transition_boundaries": [],
    }
    first = engine.recommend(request)
    second = engine.recommend(request)
    assert first == second
    assert first["engine_metadata"]["calculation"]["source"] == "P032_COMPUTE_PANCHANGA_FACTS"
