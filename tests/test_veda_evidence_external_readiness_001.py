"""Focused synthetic-only external-readiness checks."""

import json

from scripts.veda_evidence_external_readiness_001 import build, synthetic_withdrawal_test


def test_external_readiness_is_synthetic_only_and_locked():
    result = build()
    assert result["recruitment_state"] == "NOT_READY_EXTERNAL_REVIEW_REQUIRED"
    assert all(value is False for value in result["locks"].values())
    assert result["provider_calls_added"] == 0


def test_current_requirements_are_dated_and_authoritative():
    result = build()
    assert result["retrieved"] == "2026-08-17"
    assert {row["id"] for row in result["source_registry"]} >= {"IND-DPDP-ACT", "ICMR-ETHICS-2017", "CERT-IN-70B", "ADB-RESEARCH"}


def test_lifecycle_contains_required_stages():
    stages = {row[0] for row in build()["lifecycle"]}
    assert {"REGISTRATION", "CONSENT", "IDENTITY", "BIRTH DOCUMENT", "EVENT FOLLOW-UP", "WITHDRAWAL/DELETION/ANONYMIZATION"} <= stages


def test_threat_model_contains_recruitment_blockers():
    threats = build()["threats"]
    assert len(threats) >= 12
    assert all(row[-1] is True for row in threats)


def test_gate_matrix_does_not_authorize_recruitment():
    gates = build()["gates"]
    assert gates["LEGAL"] == "EXTERNAL_REVIEW_REQUIRED"
    assert gates["ETHICS"] == "EXTERNAL_REVIEW_REQUIRED"
    assert gates["SECURITY"] == "EXTERNAL_REVIEW_REQUIRED"


def test_synthetic_withdrawal_stops_contact_and_severs_linkage():
    result = synthetic_withdrawal_test()
    assert result["synthetic"] is True
    assert result["passed"] is True
    assert result["future_contact"] == "STOPPED"
    assert result["identity_linkage"] == "SEVERED"


def test_no_real_pii_or_astrology_path_in_manifest():
    result = build()
    assert result["locks"]["real_pii"] is False
    assert result["locks"]["astrology"] is False
    assert result["locks"]["predictions"] is False
    assert result["locks"]["external_submission"] is False


def test_build_is_deterministic():
    assert json.dumps(build(), sort_keys=True) == json.dumps(build(), sort_keys=True)
