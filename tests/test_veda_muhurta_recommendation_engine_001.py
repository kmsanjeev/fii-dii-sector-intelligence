"""Fail-closed tests for VEDA-MUHURTA-RECOMMENDATION-ENGINE-001."""

from scripts.veda_muhurta_recommendation_engine_001 import (
    DECISION,
    SUPPORTED_ACTIVITIES,
    activity_guard,
    audit_contract,
    build_report,
    load_contract,
)


def test_accepted_contract_hashes_are_verified():
    for activity_id in ("BUSINESS_OPENING_INAUGURATION", "EDUCATION_COMMENCEMENT"):
        contract = load_contract(activity_id)
        assert contract["contract_hash"]


def test_source_rules_are_blocked_without_machine_predicates():
    for activity_id in SUPPORTED_ACTIVITIES:
        audit = audit_contract(activity_id)
        assert audit["contract_hash_verified"] is True
        assert audit["machine_executable"] is False
        assert audit["rules_without_machine_binding"]
        assert all(item["condition_field_is_prose_only"] for item in audit["rules_without_machine_binding"])


def test_supported_activity_guard_fails_closed_without_recommendation():
    result = activity_guard("BUSINESS_OPENING_INAUGURATION")
    assert result == {
        "activity_id": "BUSINESS_OPENING_INAUGURATION",
        "recommendation_state": "ABSTAIN",
        "abstention_reason": DECISION,
    }


def test_unsupported_activity_is_distinct_from_contract_block():
    result = activity_guard("MARRIAGE")
    assert result["recommendation_state"] == "ABSTAIN"
    assert result["abstention_reason"] == "UNSUPPORTED_ACTIVITY"


def test_report_is_deterministic_and_does_not_activate_runtime():
    first = build_report()
    second = build_report()
    assert first == second
    assert first["decision"] == DECISION
    assert first["recommendation_runtime"] == "NOT_ACTIVATED"
    assert first["production_activation"] is False
    assert first["numeric_scoring"] is False
