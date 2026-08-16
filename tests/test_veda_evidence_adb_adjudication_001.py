"""Blind ADB birth-source adjudication tests; no astrology or outcome selection."""

import json

import pytest

from scripts.veda_evidence_adb_adjudication_001 import DEFAULT_XML, build, write_artifacts


pytestmark = pytest.mark.skipif(not DEFAULT_XML.exists(), reason="official ADB sample is local-only and not committed")


def test_candidate_freeze_is_exact_and_deterministic():
    first = build()["candidate_set"]
    second = build()["candidate_set"]
    assert first == second
    assert first["subject_count"] == 120
    assert len(first["subject_hash"]) == 64
    assert len(first["selection_policy_hash"]) == 64


def test_blind_adjudication_states_and_yield():
    result = build()
    assert result["results"] == {
        "verified_tier_a": 32,
        "verified_tier_b": 77,
        "total_verified_a_b": 109,
        "retained_tier_c": 0,
        "rejected_precision": 0,
        "rejected_rectified": 0,
        "rejected_conflict": 0,
        "rejected_source_lineage": 0,
        "rejected_untimed": 0,
        "unresolved": 11,
        "verification_yield": 109 / 120,
        "uncertainty_95": result["results"]["uncertainty_95"],
    }
    assert all(record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B", "UNRESOLVED_REVIEW_REQUIRED"} for record in result["records"])
    assert all(record["source_note_hash"] and len(record["source_note_hash"]) == 64 for record in result["records"])


def test_second_pass_and_event_boundary():
    result = build()
    assert result["consistency"] == {"exceptions": [], "second_pass": "PASS"}
    assert result["day_event_overlap"]["verified_subjects_with_any_day_event"] == 65
    assert result["day_event_overlap"]["total_day_events"] == 129
    assert result["day_event_overlap"]["event_status"] == "ADB_EVENT_DISCOVERY_ONLY"
    assert result["governance"]["astrology_executed"] is False
    assert result["governance"]["feature_scoring"] is False
    assert result["governance"]["ml_locked"] is True


def test_adjudication_artifacts_are_deterministic():
    first = json.dumps(build(), sort_keys=True)
    second = json.dumps(build(), sort_keys=True)
    assert first == second
    write_artifacts()
