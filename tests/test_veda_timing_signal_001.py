import pytest

from scripts.veda_timing_signal_001 import build_audit, source_candidates


def _events():
    return [
        {"event_class": "POSITION_START"},
        {"event_class": "POSITION_END"},
        {"event_class": "PUBLIC_APPOINTMENT"},
        {"event_class": "ELECTION_WIN"},
    ]


def test_signal_audit_is_deterministic_and_not_fit_to_corpus():
    first = build_audit(_events())
    second = build_audit(list(reversed(_events())))
    assert first["signal_hash"] == second["signal_hash"]
    assert first["signal_governance"] == "FAIL"
    assert first["decision"] == "NO_SOURCE_GOVERNABLE_PUBLIC_ROLE_SIGNAL"
    assert first["primary_pilot_rerun"] == "NOT_READY"
    assert first["holdout_accessed"] is False


def test_unsupported_rules_are_rejected_and_event_classes_are_gated():
    rules = {item["rule_id"]: item for item in source_candidates()}
    assert rules["TS-005"]["authority_status"] == "REJECTED"
    result = build_audit(_events())
    assert set(result["event_support"].values()) == {"NOT_GOVERNABLE"}
    with pytest.raises(ValueError, match="PRIMARY_EVENT_CLASS_OUTSIDE_FROZEN_CONTRACT"):
        build_audit([{ "event_class": "DEATH" }])


def test_method_and_precision_contract_are_frozen():
    result = build_audit(_events())
    assert result["date_precision"] == {"EXACT": 2, "MONTH": 0, "YEAR": 13}
    assert result["outputs"] == ["SIGNAL_PRESENT", "SIGNAL_ABSENT", "SIGNAL_INDETERMINATE"]
