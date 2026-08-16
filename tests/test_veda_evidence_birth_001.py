"""Focused documentary birth-source yield tests."""

import json

from scripts.veda_evidence_birth_001 import build, time_precision


def test_bounded_exact_day_frame_is_feature_blind():
    result = build()
    assert result["subjects_screened"] == 13
    assert result["exact_day_event_subjects"] == 14
    assert result["governance"]["astrology_inspected"] is False
    assert result["governance"]["feature_scoring"] is False


def test_ogdb_times_remain_tier_c_until_documentary_time_chain_is_verified():
    result = build()
    assert result["birth_yield"]["tier_a_b"] == 0
    assert result["birth_yield"]["tier_c"] == 13
    assert result["precision_qualifier_status"] == "UNRESOLVED_FOR_ALL_CURRENT_RECORDS"


def test_precision_and_queue_are_preserved():
    assert time_precision("MINUTE") == "EXACT_MINUTE"
    result = build()
    assert all(row["verification_queue"] == "PENDING_REVIEW" for row in result["rows"])
    assert all(row["birth"]["source_urls"] for row in result["rows"])


def test_no_finite_scale_estimate_from_zero_yield():
    result = build()
    assert all(item["candidates_required"] is None for item in result["scale_estimates"].values())


def test_manifest_is_deterministic():
    assert json.dumps(build(), sort_keys=True) == json.dumps(build(), sort_keys=True)
