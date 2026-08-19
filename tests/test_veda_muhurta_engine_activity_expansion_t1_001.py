from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from engines.ai.knowledge.muhurta_foundation import compute_panchanga_facts
from engines.ai.knowledge import muhurta_recommendation_engine_rx1 as engine
from engines.ai.knowledge.muhurta_window_search import search


LOCATION = {"latitude": 28.6139, "longitude": 77.2090, "timezone_name": "Asia/Kolkata"}
LOCAL = datetime(2026, 8, 19, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
START = "2026-08-20T09:00:00+05:30"
END = "2026-08-20T12:00:00+05:30"


def _facts(nakshatra: int) -> dict:
    facts = compute_panchanga_facts(0, nakshatra * (360 / 27) + 0.1, LOCAL)
    return facts


def _request(activity_id: str, *, facts: dict | None = None, **extra) -> dict:
    return {
        "activity_id": activity_id,
        "candidate_start": LOCAL,
        "location": LOCATION,
        "p032_facts": _facts(0) if facts is None else facts,
        "transition_boundaries": [],
        **extra,
    }


def _segments(*facts: dict) -> list[dict]:
    boundaries = [START, "2026-08-20T10:00:00+05:30", "2026-08-20T11:00:00+05:30", END]
    return [
        {"start": boundaries[index], "end": boundaries[index + 1], "p032_facts": fact}
        for index, fact in enumerate(facts)
    ]


def _search_request(activity_id: str, **extra) -> dict:
    value = {
        "activity_id": activity_id,
        "location": LOCATION,
        "start_datetime": START,
        "end_datetime": END,
    }
    value.update(extra)
    return value


@pytest.mark.parametrize("activity_id", ["VEHICLE_CONVEYANCE_COMMENCEMENT", "CONSECRATION_INSTALLATION_COMMENCEMENT"])
def test_t1_contracts_are_hash_guarded_and_machine_bound(activity_id: str):
    contract = engine.load_validated_contract(activity_id)
    assert contract["contract_hash_full"] == engine.CONTRACTS[activity_id]["hash"]
    assert contract["rules"][0]["factor_id"] == "NAKSHATRA_NAME"
    assert contract["rules"][0]["evaluator_state"] == "EXECUTABLE"
    assert contract["source_lineage"]["passages"]


def test_vehicle_matches_all_three_light_nakshatras():
    for index in (0, 7, 12):
        result = engine.recommend(_request("VEHICLE_CONVEYANCE_COMMENCEMENT", facts=_facts(index)))
        assert result["recommendation_state"] == "SUPPORTED_WITH_CAUTION"
        assert result["source_trace"]["source_passage_ids"] == ["VEDA-SWW-PASSAGE-BRIHAT-SAMHITA-97-09-001"]


def test_vehicle_nonmatch_missing_factor_and_scope_abstain_without_exclusion():
    nonmatch = engine.recommend(_request("VEHICLE_CONVEYANCE_COMMENCEMENT", facts=_facts(1)))
    assert nonmatch["recommendation_state"] == "ABSTAIN"
    assert nonmatch["abstention_reason"] == "NO_SOURCE_BOUND_CLASS_MATCH"
    missing = dict(_facts(0))
    missing.pop("nakshatra")
    missing_result = engine.recommend(_request("VEHICLE_CONVEYANCE_COMMENCEMENT", facts=missing))
    assert missing_result["recommendation_state"] == "ABSTAIN"
    assert missing_result["abstention_reason"] == "MISSING_NAKSHATRA"
    scope = engine.recommend(_request("VEHICLE_CONVEYANCE_COMMENCEMENT", activity_subscope="VEHICLE_PURCHASE"))
    assert scope["recommendation_state"] == "ABSTAIN"
    assert scope["abstention_reason"] == "ACTIVITY_SCOPE_MISMATCH"
    assert not scope.get("hard_exclusion")


def test_vehicle_contract_hash_mismatch_fails_closed(monkeypatch):
    original = engine.CONTRACTS["VEHICLE_CONVEYANCE_COMMENCEMENT"]["hash"]
    monkeypatch.setitem(engine.CONTRACTS["VEHICLE_CONVEYANCE_COMMENCEMENT"], "hash", "BAD")
    with pytest.raises(engine.ContractValidationError, match="hash mismatch"):
        engine.load_validated_contract("VEHICLE_CONVEYANCE_COMMENCEMENT")
    monkeypatch.setitem(engine.CONTRACTS["VEHICLE_CONVEYANCE_COMMENCEMENT"], "hash", original)


@pytest.mark.parametrize("index", [3, 11, 20, 25])
def test_consecration_matches_all_four_fixed_nakshatras(index: int):
    result = engine.recommend(_request(
        "CONSECRATION_INSTALLATION_COMMENCEMENT",
        facts=_facts(index),
        ceremony_subtype="DEITY_INSTALLATION",
    ))
    assert result["recommendation_state"] == "SUPPORTED_WITH_CAUTION"
    assert "qualified traditional" in result["consultation_guidance"].lower()


def test_consecration_requires_explicit_subtype_and_rejects_broad_scope():
    missing = engine.recommend(_request("CONSECRATION_INSTALLATION_COMMENCEMENT"))
    assert missing["recommendation_state"] == "ABSTAIN"
    assert missing["abstention_reason"] == "CEREMONY_SUBTYPE_MISSING"
    invalid = engine.recommend(_request("CONSECRATION_INSTALLATION_COMMENCEMENT", ceremony_subtype=""))
    assert invalid["recommendation_state"] == "ABSTAIN"
    assert invalid["abstention_reason"] == "CEREMONY_SUBTYPE_MISSING"
    broad = engine.recommend(_request(
        "CONSECRATION_INSTALLATION_COMMENCEMENT",
        ceremony_subtype="DEITY_INSTALLATION",
        activity_subscope="PUJA",
    ))
    assert broad["recommendation_state"] == "ABSTAIN"
    assert broad["abstention_reason"] == "ACTIVITY_SCOPE_MISMATCH"


def test_consecration_nonmatch_and_source_trace():
    result = engine.recommend(_request(
        "CONSECRATION_INSTALLATION_COMMENCEMENT",
        facts=_facts(1),
        ceremony_subtype="DEITY_INSTALLATION",
    ))
    assert result["recommendation_state"] == "ABSTAIN"
    assert result["abstention_reason"] == "NO_SOURCE_BOUND_CLASS_MATCH"
    assert result["source_trace"]["source_assertion_ids"] == ["VEDA-SWW-ASSERTION-BS-NAK-CONSECRATION-001"]
    assert "guarantee" in result["caution"]["general"].lower()


def test_t1_window_search_uses_nakshatra_only_and_preserves_boundary_changes():
    supported = _facts(0)
    nonmatch = _facts(1)
    result = search(_search_request(
        "VEHICLE_CONVEYANCE_COMMENCEMENT",
        transition_boundaries=[{"at": "2026-08-20T10:00:00+05:30", "factor": "NAKSHATRA"}],
        p032_fact_segments=_segments(supported, nonmatch, nonmatch),
    ))
    assert not {"TITHI_BOUNDARY", "KARANA_BOUNDARY"}.intersection(result["transition_types"])
    assert result["windows_before_merge"] == 3
    assert result["windows_examined"] == 2
    assert result["windows"][0]["recommendation_state"] == "SUPPORTED_WITH_CAUTION"
    assert result["windows"][1]["recommendation_state"] == "ABSTAIN"
    assert result["windows"][0]["source_trace"]["source_passage_ids"]


def test_t1_window_search_no_supported_interval_returns_no_result():
    result = search(_search_request(
        "VEHICLE_CONVEYANCE_COMMENCEMENT",
        p032_fact_segments=_segments(_facts(1), _facts(1), _facts(1)),
    ))
    assert result["result_state"] == "NO_RESULT"
    assert result["windows"]
    assert all(item["recommendation_state"] == "ABSTAIN" for item in result["windows"])


def test_consecration_window_requires_subtype_and_accepts_supported_interval():
    missing = search(_search_request(
        "CONSECRATION_INSTALLATION_COMMENCEMENT",
        p032_fact_segments=_segments(_facts(3), _facts(3), _facts(3)),
    ))
    assert missing["result_state"] == "NO_RESULT"
    assert missing["abstained_intervals"][0]["abstention_reason"] == "CEREMONY_SUBTYPE_MISSING"
    valid = search(_search_request(
        "CONSECRATION_INSTALLATION_COMMENCEMENT",
        ceremony_subtype="DEITY_INSTALLATION",
        p032_fact_segments=_segments(_facts(3), _facts(1), _facts(3)),
    ))
    assert valid["result_state"] in {"WINDOWS_FOUND", "EQUIVALENT_TOP_WINDOWS"}
    assert valid["primary_window"]["recommendation_state"] == "SUPPORTED_WITH_CAUTION"


def test_t1_outputs_are_deterministic_and_no_score_or_personal_bala_is_used():
    request = _request("VEHICLE_CONVEYANCE_COMMENCEMENT", facts=_facts(0))
    first = engine.recommend(request)
    second = engine.recommend(request)
    assert first == second
    assert "score" not in first
    assert first["personal_factors_evaluated"] is False
    assert first["personal_factors"]["tara_bala"] == "NOT_EVALUATED"


def test_openapi_exposes_context_field_and_existing_routes_remain_present():
    from backend.main import app

    schema = app.openapi()
    assert "/api/muhurta/recommend" in schema["paths"]
    assert "/api/muhurta/search" in schema["paths"]
    request_schema = schema["components"]["schemas"]["MuhurtaRecommendationRequest"]["properties"]
    search_schema = schema["components"]["schemas"]["MuhurtaWindowSearchRequest"]["properties"]
    assert "ceremony_subtype" in request_schema
    assert "ceremony_subtype" in search_schema
