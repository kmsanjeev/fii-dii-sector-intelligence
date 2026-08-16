"""Focused hybrid strategy and consent-design tests."""

import json

from scripts.veda_evidence_hybrid_001 import build, upper_zero_success_yield


def test_new_documentary_screen_is_bounded_and_feature_blind():
    result = build()
    assert result["documentary_pilot"]["new_subjects_screened"] == 40
    assert result["documentary_pilot"]["tier_a_b"] == 0
    assert result["governance"]["astrology_inspected"] is False
    assert result["governance"]["feature_scoring"] is False


def test_zero_yield_workload_reports_uncertainty_not_fake_precision():
    result = build()
    assert all(item["status"] == "NOT_ESTIMABLE_WITH_USEFUL_PRECISION" for item in result["workload"].values())
    assert upper_zero_success_yield(40) > 0


def test_formal_access_and_human_blocker_are_explicit():
    result = build()
    assert result["formal_access"]["astro_databank"]["external_human_action_required"] is True
    assert result["governance"]["external_human_action"] == "HUMAN_EXTERNAL_ACCESS_BLOCKER"


def test_consent_schema_is_minimum_necessary_and_deterministic():
    result = build()
    fields = result["consented_corpus"]["fields"]
    assert "consent_version" in fields and "withdrawal_status" in fields
    assert result["consented_corpus"]["implementation_authorized"] is False
    assert json.dumps(build(), sort_keys=True) == json.dumps(build(), sort_keys=True)


def test_india_lane_does_not_invent_candidates():
    result = build()
    assert result["india"]["candidates_screened"] == 0
    assert result["india"]["decision"] == "INDIA_CONSENTED_ROUTE_REQUIRED"
