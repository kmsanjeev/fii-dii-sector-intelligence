"""Focused tests for governance-only Muhurta recommendation design."""

import json

from scripts.veda_muhurta_recommendation_governance_001 import OUT, acceptance, build_result, emit


def test_p032_is_reused_and_recommendations_remain_inactive():
    result = build_result()
    assert result["p032"]["foundation_status"] == "IMPLEMENTED / FROZEN"
    assert result["p032"]["recommendation_status_after"] == "INACTIVE / NOT_IMPLEMENTED"
    assert result["production"]["recommendation_engine_activated"] is False


def test_taxonomy_and_risk_are_deterministic_and_restrict_high_risk():
    result = build_result()
    activities = {row["activity"]: row for row in result["activities"]}
    assert len(activities) == 15
    assert activities["MEDICAL_PROCEDURE"]["support"] == "RESTRICTED"
    assert activities["LEGAL_ACTION_OR_FILING"]["support"] == "RESTRICTED"
    assert activities["FINANCIAL_OR_INVESTMENT_DECISION"]["support"] == "RESTRICTED"
    assert activities["EDUCATION_COMMENCEMENT"]["support"] == "SUPPORTED_WITH_CAUTION"
    assert activities["MARRIAGE_OR_ENGAGEMENT"]["mvp"] is False


def test_no_score_and_personal_bala_is_gated():
    result = build_result()
    assert result["state_models"]["arbitrary_weighted_score"] is False
    assert result["personal_readiness"]["tara_bala"]["recommendation_use"] == "NO"
    assert result["personal_readiness"]["chandra_bala"]["recommendation_use"] == "NO"
    assert result["personal_readiness"]["personalized_recommendation_ready"] is False


def test_safety_abstention_and_output_contract():
    result = build_result()
    assert result["caution_consultation"]["mandatory_caution"] is True
    assert result["caution_consultation"]["non_bypassable"] is True
    assert "PERSONAL_DATA_INSUFFICIENT" in result["state_models"]["abstention_states"]
    assert "SOURCE_CONFLICT_UNRESOLVED" in result["state_models"]["recommendation_states"]
    assert "SOURCE_CITATIONS" in result["output_contract"]["fields"]
    assert result["output_contract"]["guarantee_prohibited"] is True


def test_parallel_state_and_two_run_determinism():
    result = build_result()
    emit(result)
    first = {path.name: path.read_bytes() for path in OUT.iterdir() if path.is_file()}
    emit(result)
    second = {path.name: path.read_bytes() for path in OUT.iterdir() if path.is_file()}
    assert first == second
    assert result["production"]["approved_core_before"] == result["production"]["approved_core_after"] == 17
    assert result["next_programme"]["automatically_started"] is False
    assert json.loads((OUT / "12_MVP_ACTIVITY_READINESS.json").read_text(encoding="utf-8"))["initial_activities"] == ["BUSINESS_START_OR_INAUGURATION", "EDUCATION_COMMENCEMENT", "RELIGIOUS_OR_SPIRITUAL_CEREMONY"]
    assert len(acceptance()) == 26
    assert "26/26" in (OUT / "15_FINAL_ACCEPTANCE.md").read_text(encoding="utf-8")
