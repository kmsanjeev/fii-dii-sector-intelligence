from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from engines.ai.knowledge.muhurta_foundation import compute_panchanga_facts
from engines.ai.knowledge.muhurta_window_search import (
    MAX_SEARCH_RANGE,
    MuhurtaWindowSearchError,
    search,
)
from engines.ai.knowledge.muhurta_transition_source import discover_transitions, position_facts


LOCATION = {"latitude": 28.6139, "longitude": 77.2090, "timezone_name": "Asia/Kolkata"}
START = "2026-08-20T09:00:00+05:30"
END = "2026-08-20T12:00:00+05:30"


def _facts(sun: float, moon: float, value: str = START) -> dict:
    return compute_panchanga_facts(sun, moon, datetime.fromisoformat(value))


def _request(activity: str = "BUSINESS_OPENING_INAUGURATION", **extra):
    value = {
        "activity_id": activity,
        "location": LOCATION,
        "start_datetime": START,
        "end_datetime": END,
    }
    value.update(extra)
    return value


def _segments(*facts: dict) -> list[dict]:
    boundaries = ["2026-08-20T09:00:00+05:30", "2026-08-20T10:00:00+05:30", "2026-08-20T11:00:00+05:30", END]
    return [
        {"start": boundaries[index], "end": boundaries[index + 1], "p032_facts": fact}
        for index, fact in enumerate(facts)
    ]


def test_single_candidate_engine_is_composed_and_business_search_is_deterministic():
    facts = _facts(60, 100)
    request = _request(p032_fact_segments=_segments(facts, facts, facts))
    first = search(request)
    second = search(request)
    first.pop("performance")
    second.pop("performance")
    assert first["result_state"] == "WINDOWS_FOUND"
    assert first["windows_examined"] == 1
    assert first["primary_window"]["recommendation_state"] == "MIXED_FACTORS"
    assert first["contract_id"] == "VEDA-MUH-CONTRACT-BUSINESS-OPENING-V4"
    assert first["engine_id"] == "VEDA_MUHURTA_GENERAL_RECOMMENDATION_ENGINE"


def test_education_search_preserves_formal_scope_and_tithi_contract():
    facts = _facts(70, 100)
    result = search(_request(
        "EDUCATION_COMMENCEMENT",
        activity_subscope="FORMAL_COURSE_COMMENCEMENT",
        p032_fact_segments=_segments(facts, facts, facts),
    ))
    assert result["primary_window"]["recommendation_state"] == "SUPPORTED_WITH_CAUTION"
    assert "MUH-EDU-TITHI-VIDYARAMBHA-001" in [item["rule_id"] for item in result["primary_window"]["rules_evaluated"]]
    assert result["personal_factors"]["tara_bala"] == "NOT_EVALUATED"


def test_daily_time_bounds_are_applied_without_sampling():
    facts = _facts(60, 100)
    result = search(_request(
        daily_earliest_time="10:00",
        daily_latest_time="11:00",
        p032_fact_segments=_segments(facts, facts, facts),
    ))
    assert result["primary_window"]["start"].startswith("2026-08-20T10:00:00")
    assert result["primary_window"]["end"].startswith("2026-08-20T11:00:00")


def test_equivalent_top_windows_are_returned_without_hidden_ranking():
    facts = _facts(60, 100)
    result = search(_request(p032_fact_segments=_segments(facts, facts, facts)))
    assert result["equivalent_primary_windows"] == []
    assert result["comparison_basis"].startswith("CATEGORICAL_STATE_ORDER_V1")
    assert "score" not in result
    assert all("score" not in item for item in result["windows"])


def test_different_rule_result_is_not_merged():
    supported = _facts(60, 100)
    mixed = _facts(0, 1)
    insufficient = _facts(0, 50)
    result = search(_request(p032_fact_segments=_segments(supported, mixed, insufficient)))
    assert result["windows_before_merge"] == 3
    assert result["windows_examined"] == 3
    assert [item["recommendation_state"] for item in result["windows"]] == ["MIXED_FACTORS", "MIXED_FACTORS", "INSUFFICIENT_RULE_COVERAGE"]


def test_scope_mismatch_produces_no_result_and_does_not_generalize_business():
    facts = _facts(60, 100)
    result = search(_request(activity_subscope="investment selection", p032_fact_segments=_segments(facts, facts, facts)))
    assert result["result_state"] == "NO_RESULT"
    assert all(item["recommendation_state"] == "ABSTAIN" for item in result["windows"])
    assert result["no_result_reason"] == "NO_GOVERNED_RECOMMENDABLE_WINDOW_FOUND"


def test_unsupported_activity_returns_maturity_gate_without_search():
    result = search(_request("RELIGIOUS_CEREMONY"))
    assert result["capability_state"] == "NOT_YET_ENGINE_READY"
    assert result["windows_examined"] == 0
    assert result["abstention_reason"] == "NOT_YET_ENGINE_READY"


def test_missing_p032_fact_segment_is_not_silently_used_as_personalization():
    result = search(_request("EDUCATION_COMMENCEMENT", activity_subscope="ROUTINE_DAILY_STUDY"))
    assert result["result_state"] == "NO_RESULT"
    assert result["windows_examined"] >= 1
    assert result["abstained_intervals"][0]["abstention_reason"] == "ACTIVITY_SCOPE_MISMATCH"


def test_transition_dependency_failure_is_a_governed_no_result(monkeypatch):
    import engines.ai.knowledge.muhurta_window_search as search_module

    def unavailable(*args, **kwargs):
        from engines.ai.knowledge.muhurta_transition_source import TransitionSourceError

        raise TransitionSourceError("test dependency unavailable")

    monkeypatch.setattr(search_module, "discover_transitions", unavailable)
    result = search(_request())
    assert result["result_state"] == "NO_RESULT"
    assert result["no_result_reason"] == "CALCULATION_DEPENDENCY_UNAVAILABLE"
    assert result["capability_state"] == "IMPLEMENTED_VALIDATED_WITH_DEPENDENCY_CONDITION"


def test_range_and_result_limits_are_bounded():
    with pytest.raises(MuhurtaWindowSearchError):
        search(_request(end_datetime="2026-09-21T09:00:00+05:30"))
    with pytest.raises(MuhurtaWindowSearchError):
        search(_request(max_results=21))
    assert MAX_SEARCH_RANGE.days == 31


def test_calculated_transition_source_emits_relevant_factor_boundaries():
    start = datetime.fromisoformat("2026-08-20T00:00:00+05:30")
    end = start + timedelta(days=2)
    transitions = discover_transitions(start, end)
    assert transitions
    assert {item["classification"] for item in transitions} == {"CALCULATED_TRANSITION"}
    assert {item["factor"] for item in transitions} <= {"TITHI", "KARANA", "NAKSHATRA"}
    assert all(start.isoformat() < item["at"] < end.isoformat() for item in transitions)


def test_transition_boundary_changes_the_existing_p032_factor():
    start = datetime.fromisoformat("2026-08-20T00:00:00+05:30")
    end = start + timedelta(days=1)
    transition = next(item for item in discover_transitions(start, end) if item["factor"] == "NAKSHATRA")
    at = datetime.fromisoformat(transition["at"])
    before = position_facts(at - timedelta(seconds=2))["p032_facts"]["nakshatra"]["index"]
    after = position_facts(at + timedelta(seconds=2))["p032_facts"]["nakshatra"]["index"]
    assert before != after


def test_explicit_transition_and_fact_segments_are_used_as_exact_source():
    facts = _facts(60, 100)
    result = search(_request(
        transition_boundaries=[{"at": "2026-08-20T10:00:00+05:30", "kind": "TEST_TITHI_BOUNDARY"}],
        p032_fact_segments=_segments(facts, facts, facts),
    ))
    assert result["search_method"] == "EXPLICIT_AND_CALCULATED_TRANSITIONS"
    assert result["windows_examined"] == 1


def test_api_contract_exposes_search_route():
    from backend.main import app

    paths = set(app.openapi()["paths"])
    assert "/api/muhurta/search" in paths
