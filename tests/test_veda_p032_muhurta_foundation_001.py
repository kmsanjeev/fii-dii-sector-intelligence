from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from engines.ai.knowledge.muhurta_foundation import (
    EVENT_TYPES,
    atomic_rule_registry,
    build_candidate_windows,
    build_muhurta_foundation,
    compute_panchanga_facts,
    event_taxonomy,
    evaluate_atomic_rules,
    MuhurtaRequest,
)


def _local(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=ZoneInfo("Asia/Kolkata"))


def test_panchanga_facts_match_existing_five_limb_contract():
    facts = compute_panchanga_facts(0.0, 0.0, _local("2026-08-17T12:00:00"))
    assert facts["vara"] == {"index": 1, "name": "Monday", "lord": "Moon"}
    assert facts["tithi"]["number"] == 1
    assert facts["tithi"]["name"] == "Pratipada"
    assert facts["nakshatra"]["name"] == "Ashwini"
    assert facts["nakshatra"]["pada"] == 1
    assert facts["yoga"]["number"] == 1
    assert facts["karana"]["number"] == 1
    assert facts["karana"]["name"] == "Kimstughna"


@pytest.mark.parametrize(
    ("sun", "moon", "expected"),
    [
        (0.0, 11.9999999999, (1, 2)),
        (0.0, 12.0, (2, 3)),
        (0.0, 359.9999999999, (30, 60)),
        (0.0, 360.0, (1, 1)),
    ],
)
def test_tithi_and_karana_half_open_boundaries(sun, moon, expected):
    facts = compute_panchanga_facts(sun, moon, _local("2026-08-17T12:00:00"))
    assert (facts["tithi"]["number"], facts["karana"]["number"]) == expected


def test_nakshatra_and_yoga_boundaries_are_deterministic():
    segment = 360.0 / 27.0
    before = compute_panchanga_facts(0, segment - 1e-10, _local("2026-08-17T12:00:00"))
    after = compute_panchanga_facts(0, segment, _local("2026-08-17T12:00:00"))
    assert before["nakshatra"]["number"] == 1
    assert after["nakshatra"]["number"] == 2
    assert after["yoga"]["number"] == 2


def test_event_taxonomy_does_not_expand_existing_request_contract():
    assert set(EVENT_TYPES).issubset(event_taxonomy())
    assert event_taxonomy()["MARRIAGE"]["production"] == "DISABLED"
    assert event_taxonomy()["PROPERTY_PURCHASE"]["status"] == "TAXONOMY_ONLY"
    with pytest.raises(ValueError):
        MuhurtaRequest(date(2026, 8, 17), 19.0, 72.0, "Asia/Kolkata", "PROPERTY_PURCHASE").validate()


def test_atomic_registry_is_traceable_and_never_scores():
    rules = atomic_rule_registry()
    assert rules
    assert all(item["rule_id"].startswith("P032-") for item in rules)
    assert any(item["status"] == "RESEARCH_CANDIDATE" for item in rules)
    facts = compute_panchanga_facts(0, 15, _local("2026-08-17T12:00:00"))
    results = evaluate_atomic_rules(facts, "MARRIAGE")
    assert results
    assert all(item["score"] is None for item in results)
    assert all(item["recommendation"] == "NOT_AUTHORIZED" for item in results)


def test_candidate_windows_split_only_at_explicit_transitions():
    start = _local("2026-08-17T09:00:00")
    end = _local("2026-08-17T15:00:00")
    transition = start + timedelta(hours=2)
    windows = build_candidate_windows(
        start,
        end,
        [{"at": transition, "kind": "TITHI_BOUNDARY"}],
        [{"tithi": 1}, {"tithi": 2}],
    )
    assert len(windows) == 2
    assert windows[0]["end"] == transition.isoformat()
    assert windows[1]["start"] == transition.isoformat()
    assert all(item["selection_status"] == "INACTIVE" for item in windows)
    assert all(item["recommendation_status"] == "NOT_AUTHORIZED" for item in windows)
    assert all(item["score"] is None for item in windows)


def test_solar_foundation_contract_remains_inactive():
    result = build_muhurta_foundation(
        MuhurtaRequest(date(2026, 8, 17), 19.076, 72.8777, "Asia/Kolkata", "MARRIAGE")
    )
    assert result["activation_status"] == "INACTIVE"
    assert result["recommendation_status"] == "NOT_IMPLEMENTED"
    assert result["dependencies"]["tarabala"] == "NOT_IMPLEMENTED"
    assert result["dependencies"]["chandrabala"] == "NOT_IMPLEMENTED"
