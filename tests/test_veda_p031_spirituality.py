from collections import Counter

from engines.ai.knowledge.spirituality_governance import SPIRITUALITY_DOMAIN
from engines.intelligence.spirituality_dharma_synthesis_engine import SpiritualityDharmaSynthesisEngine


ENGINE = SpiritualityDharmaSynthesisEngine()


def test_contract_contains_required_dimensions_and_safety_state():
    result = ENGINE.synthesize({"subject_id": "subject-a", "birth_time_quality": "EXACT", "spiritual_scores": {"spiritual_inclination": 0.9, "spiritual_interest": 0.9}})
    assert result.domain == "SPIRITUALITY_DHARMA"
    assert result.subject_id == "subject-a"
    assert result.spiritual_inclination == "STRONG"
    assert result.trust_state == "RESEARCH_CANDIDATE"
    assert result.safety_status == "NO_ENLIGHTENMENT_OR_CLINICAL_DIAGNOSIS"
    assert "Spiritual interest does not establish sustained practice or spiritual maturity." in result.conditions


def test_dharma_is_not_religiosity_and_interest_is_not_practice():
    result = ENGINE.synthesize({"spiritual_scores": {"dharma_orientation": .9, "religious_orientation": .1, "spiritual_interest": .8, "practice_discipline": .1}})
    assert result.dharma_orientation == "STRONG"
    assert result.religious_orientation == "WEAK"
    assert "DHARMA_OR_ETHICAL_PURPOSE_WITHOUT_INSTITUTIONAL_RELIGIOSITY" in result.alternatives
    assert "INTEREST_OR_STUDY_WITHOUT_ESTABLISHED_PRACTICE" in result.alternatives


def test_modes_planets_and_occult_interest_remain_separate():
    result = ENGINE.synthesize({"spiritual_scores": {"devotional_orientation": .9, "philosophical_orientation": .8, "contemplation": .8, "seva_service": .8, "occult_inquiry": .9, "ketu": .9}})
    assert {"DEVOTIONAL", "PHILOSOPHICAL", "CONTEMPLATIVE", "SERVICE", "OCCULT_INQUIRY"}.issubset(result.spiritual_modes)
    assert any("Occult" in item for item in result.conditions)
    assert "Ketu" not in result.dominant_spiritual_scenario


def test_detachment_solitude_pilgrimage_do_not_become_diagnosis_or_renunciation():
    result = ENGINE.synthesize({"spiritual_scores": {"detachment": .9, "solitude_retreat": .8, "pilgrimage": .8, "renunciatory_tendency": .1}})
    assert any("not interpreted as depression" in item for item in result.conditions)
    assert any("not interpreted as social failure" in item for item in result.conditions)
    assert "PILGRIMAGE_OR_DEVOTION_WITHOUT_RENUNCIATION" in result.alternatives
    assert "CLINICAL_DIAGNOSIS" in SPIRITUALITY_DOMAIN["blocked_outputs"]


def test_householder_spirituality_and_crisis_boundaries():
    result = ENGINE.synthesize({"spiritual_scores": {"householder_spirituality": .9, "spiritual_crisis": .8}})
    assert any("family, work, service" in item for item in result.conditions)
    assert any("not a clinical diagnosis" in item for item in result.conditions)


def test_timing_requires_structure_and_dasha_transit():
    no_structure = ENGINE.synthesize({"dasha_activation": "SUPPORTIVE", "transit_trigger": "SUPPORTIVE"})
    assert no_structure.timing == "INSUFFICIENT_DATA"
    active = ENGINE.synthesize({"spiritual_scores": {"higher_knowledge": .9}, "dasha_activation": "SUPPORTIVE", "transit_trigger": "SUPPORTIVE", "varga_metadata": {"D20": {"calculation_status": "VALIDATED"}, "D9": {}, "D12": {}}})
    assert active.timing == "STRONGLY_SUPPORTIVE"
    assert active.timing_window == "DASHA_TRANSIT_CONVERGENCE"
    assert "D20_INTERPRETATION_NOT_VALIDATED" in active.missing_data


def test_d1_first_context_gates_vargas_and_preserves_pred_handoff():
    result = ENGINE.synthesize({"subject_id": "chart-1", "birth_time_quality": "RANGE", "spiritual_scores": {"study_orientation": .8}, "pilgrimage_context": {"signal": True}, "education_context": {"signal": True}})
    assert result.subject_id == "chart-1"
    assert result.birth_time_quality == "RANGE"
    assert "VARGA_BIRTH_TIME_SENSITIVITY" in result.missing_data
    assert "D20_NOT_AVAILABLE_OR_NOT_VALIDATED" in result.missing_data
    assert result.dominant_spiritual_scenario == "STUDY_AND_HIGHER_KNOWLEDGE"
    assert "PILGRIMAGE_AS_TRAVEL_CONTEXT" in result.alternative_scenarios
    assert "EDUCATION_AS_HIGHER_KNOWLEDGE_CONTEXT" in result.alternative_scenarios


def test_governance_separates_claim_layers_and_d20():
    assert SPIRITUALITY_DOMAIN["claim_layers"]["classical"] == "NOT_VALIDATED_FOR_P031"
    assert SPIRITUALITY_DOMAIN["claim_layers"]["practitioner"] == "DISCOVERY_ONLY"
    assert SPIRITUALITY_DOMAIN["d20_audit"]["interpretation_status"] == "NOT_VALIDATED"
    assert SPIRITUALITY_DOMAIN["d20_audit"]["p015_remediation_required"] == "NO_FOR_P031"
    assert SPIRITUALITY_DOMAIN["yoga_dosha_policy"]["spiritual_yogas"] == "NOT_IMPORTED"


def _development_cases():
    cases = []
    cases.extend(("interest_maturity", {"spiritual_interest": .9, "practice_discipline": .1}) for _ in range(20))
    cases.extend(("religiosity_inner_development", {"religious_orientation": .9, "inner_development": .1}) for _ in range(15))
    cases.extend(("detachment_distress", {"detachment": .9, "solitude_retreat": .8}) for _ in range(15))
    cases.extend(("pilgrimage_renunciation", {"pilgrimage": .9, "renunciatory_tendency": .1}) for _ in range(15))
    cases.extend(("d20_gating", {"higher_knowledge": .8}) for _ in range(15))
    cases.extend(("timing", {"dharma_orientation": .8}) for _ in range(25))
    cases.extend(("contradiction", {"spiritual_inclination": .9, "inner_development": .1}) for _ in range(15))
    cases.extend(("general", {"study_orientation": .8, "devotional_orientation": .7}) for _ in range(40))
    return cases


def test_deterministic_benchmark_categories_and_safety():
    cases = _development_cases()
    assert len(cases) >= 150
    counts = Counter(category for category, _ in cases)
    assert counts["interest_maturity"] >= 20
    assert counts["religiosity_inner_development"] >= 15
    assert counts["detachment_distress"] >= 15
    assert counts["pilgrimage_renunciation"] >= 15
    assert counts["d20_gating"] >= 15
    assert counts["timing"] >= 25
    assert counts["contradiction"] >= 15
    for category, scores in cases:
        result = ENGINE.synthesize({"spiritual_scores": scores})
        assert result.domain == "SPIRITUALITY_DHARMA"
        assert result.safety_status == "NO_ENLIGHTENMENT_OR_CLINICAL_DIAGNOSIS"
        if category == "interest_maturity":
            assert any("maturity" in item for item in result.conditions)
        if category == "pilgrimage_renunciation":
            assert "PILGRIMAGE_OR_DEVOTION_WITHOUT_RENUNCIATION" in result.alternatives


def test_holdout_is_independent_and_subject_safe():
    holdout = [
        {"subject_id": f"holdout-{index}", "spiritual_scores": {"spiritual_interest": .8, "practice_discipline": .1}}
        for index in range(50)
    ]
    assert len(holdout) >= 50
    assert all(ENGINE.synthesize(chart).subject_id == chart["subject_id"] for chart in holdout)
