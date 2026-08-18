"""Focused no-acquisition governance tests for India access RX-001."""

import json

from scripts.veda_evidence_india_access_rx_001 import build, digest


def test_gemini_claims_are_discovery_only_and_50k_150k_are_separated():
    result = build()
    claims = {row["claim"]: row for row in result["gemini_claim_audit"]}
    assert claims["BVB/K.N. Rao has 50,000+ horoscopes"]["classification"].endswith("PRIMARY_SOURCE_SUPPORTED")
    assert claims["BVB/K.N. Rao has 150,000 horoscopes"]["classification"] == "NOT_VERIFIED"


def test_primary_source_and_provider_boundaries_are_explicit():
    result = build()
    assert result["icas"]["central_dataset_verified"] is False
    assert result["shodhganga"]["controls_automatically_eligible"] == "NO"
    assert result["crs"]["tob_in_standard_birth_form"] == "CRS_TOB_NOT_ESTABLISHED_FROM_FORM"
    assert result["source_registry"]


def test_rti_dpdp_and_rectification_safety():
    result = build()
    assert result["rti"]["excludes"] == ["names", "DOB", "TOB", "POB", "individual records", "bulk PII"]
    assert result["dpdp_rbd_rti"]["disclosure_entitlement"] == "NOT_CREATED_BY_RESEARCH_CONDITION"
    rectified = next(row for row in result["provenance_contract"] if row["class"] == "INDIA_RECTIFIED")
    assert rectified["confirmatory"] is False


def test_hospital_model_is_minimal_and_pseudonymous():
    result = build()
    hospital = result["hospital"]
    assert hospital["ethics_required"] is True
    assert "provider-held identity key" in hospital["pseudonymized_architecture"].lower()
    assert result["governance"]["personal_data_acquired"] is False


def test_no_acquisition_or_prediction_path_and_parallel_lanes_preserved():
    result = build()
    boundary = result["execution_boundary"]
    assert boundary["provider_calls"] == 0
    assert boundary["external_requests_sent"] is False
    assert boundary["scraping"] is False
    assert boundary["astrology"] is False
    assert boundary["feature_scoring"] is False
    assert boundary["ml"] == "LOCKED"
    assert boundary["pred_m4"] == "INSUFFICIENT_SAMPLE"
    assert result["parallel_lanes"]["muller"] == "MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE"
    assert result["parallel_lanes"]["ashtakavarga"] == "ASHTAKAVARGA_REMEDIATION_SPEC_READY"


def test_artifact_contract_is_deterministic():
    left = build()
    right = build()
    assert json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)
    assert digest(left) == digest(right)


def test_acceptance_register_has_no_unresolved_execution_failure():
    result = build()
    assert len(result["acceptance"]) >= 25
    assert {row["status"] for row in result["acceptance"]} <= {"PASS", "PASS_WITH_CONDITION"}
