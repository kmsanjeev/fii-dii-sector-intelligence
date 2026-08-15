from engines.ai.knowledge.spirituality_governance import SPIRITUALITY_DOMAIN
from engines.intelligence.spirituality_dharma_synthesis_engine import (
    SpiritualityDharmaSynthesisEngine,
    build_spirituality_benchmark,
    build_spirituality_holdout,
)


def test_contract_contains_required_dimensions_and_safety_state():
    result = SpiritualityDharmaSynthesisEngine().synthesize({"spiritual_scores": {"spiritual_inclination": 0.9, "spiritual_interest": 0.9}})
    assert result.domain == "SPIRITUALITY_DHARMA"
    assert result.spiritual_inclination == "STRONG"
    assert result.trust_state == "RESEARCH_CANDIDATE"
    assert result.safety_status == "NO_ENLIGHTENMENT_OR_CLINICAL_DIAGNOSIS"
    assert "Spiritual interest does not establish sustained practice or spiritual maturity." in result.conditions


def test_dharma_is_not_religiosity_and_interest_is_not_practice():
    result = SpiritualityDharmaSynthesisEngine().synthesize({"spiritual_scores": {"dharma_orientation": .9, "religious_orientation": .1, "spiritual_interest": .8, "practice_discipline": .1}})
    assert result.dharma_orientation == "STRONG"
    assert result.religious_orientation == "WEAK"
    assert "DHARMA_OR_ETHICAL_PURPOSE_WITHOUT_INSTITUTIONAL_RELIGIOSITY" in result.alternatives
    assert "INTEREST_OR_STUDY_WITHOUT_ESTABLISHED_PRACTICE" in result.alternatives


def test_detachment_solitude_pilgrimage_do_not_become_diagnosis_or_renunciation():
    result = SpiritualityDharmaSynthesisEngine().synthesize({"spiritual_scores": {"detachment": .9, "solitude_retreat": .8, "pilgrimage": .8, "renunciatory_tendency": .1}})
    assert any("not interpreted as depression" in item for item in result.conditions)
    assert any("not interpreted as social failure" in item for item in result.conditions)
    assert "PILGRIMAGE_OR_DEVOTION_WITHOUT_RENUNCIATION" in result.alternatives
    assert "CLINICAL_DIAGNOSIS" in SPIRITUALITY_DOMAIN["blocked_outputs"]


def test_householder_spirituality_and_crisis_boundaries():
    result = SpiritualityDharmaSynthesisEngine().synthesize({"spiritual_scores": {"householder_spirituality": .9, "spiritual_crisis": .8}})
    assert any("family, work, service" in item for item in result.conditions)
    assert any("not a clinical diagnosis" in item for item in result.conditions)


def test_timing_requires_structure_and_dasha_transit():
    no_structure = SpiritualityDharmaSynthesisEngine().synthesize({"dasha_activation": "SUPPORTIVE", "transit_trigger": "SUPPORTIVE"})
    assert no_structure.timing == "INSUFFICIENT_DATA"
    active = SpiritualityDharmaSynthesisEngine().synthesize({"spiritual_scores": {"higher_knowledge": .9}, "dasha_activation": "SUPPORTIVE", "transit_trigger": "SUPPORTIVE", "varga_metadata": {"D20": {"calculation_status": "VALIDATED"}, "D9": {}, "D12": {}}})
    assert active.timing == "STRONGLY_SUPPORTIVE"
    assert "D20_INTERPRETATION_NOT_VALIDATED" in active.missing_data


def test_benchmark_and_holdout_sizes_and_no_enlightenment_claim():
    assert len(build_spirituality_benchmark()) == 160
    holdout = build_spirituality_holdout()
    assert len(holdout) == 50
    assert all("ENLIGHTENMENT" in item["expected"] or "RENUNCIATION" in item["expected"] for item in holdout)
