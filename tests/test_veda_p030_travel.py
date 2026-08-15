from engines.ai.knowledge.travel_relocation_governance import TRAVEL_RELOCATION_DOMAIN
from engines.intelligence.travel_relocation_synthesis_engine import (
    TravelRelocationSynthesisEngine,
    build_travel_benchmark,
    build_travel_holdout,
)


def test_contract_separates_travel_relocation_residence_and_settlement():
    result = TravelRelocationSynthesisEngine().synthesize({"movement_scores": {"travel_potential": .9, "foreign_travel": .9, "foreign_residence": .7, "foreign_settlement": .2}})
    assert result.domain == "TRAVEL_RELOCATION"
    assert result.travel_potential == "STRONG"
    assert result.foreign_travel == "STRONG"
    assert result.foreign_residence == "MODERATE"
    assert result.foreign_settlement == "WEAK"
    assert any("settlement" in item.lower() for item in result.contradictions)


def test_travel_does_not_become_relocation_or_property():
    result = TravelRelocationSynthesisEngine().synthesize({"movement_scores": {"short_travel": .9, "foreign_travel": .8}}, property_context={"residence_change": "WEAK"})
    assert result.relocation_potential == "INSUFFICIENT_DATA"
    assert result.foreign_residence == "INSUFFICIENT_DATA"
    assert "P029_RESIDENCE_CHANGE_SIGNAL" in result.alternatives


def test_d4_calculation_does_not_enable_travel_interpretation():
    result = TravelRelocationSynthesisEngine().synthesize({"varga_metadata": {"D4": {"calculation_status": "VALIDATED", "interpretation_status": "NOT_VALIDATED"}}, "movement_scores": {"foreign_residence": .8}})
    assert "D4_INTERPRETATION_NOT_VALIDATED" in result.missing_data
    assert "D4" in " ".join(result.reasoning_trace)


def test_timing_requires_structural_signal_and_preserves_conflict():
    engine = TravelRelocationSynthesisEngine()
    strong = engine.synthesize({"movement_scores": {"foreign_residence": .9}, "dasha_activation": "SUPPORTIVE", "transit_trigger": "SUPPORTIVE"})
    weak = engine.synthesize({"movement_scores": {"foreign_residence": .2}, "dasha_activation": "UNKNOWN", "transit_trigger": "SUPPORTIVE"})
    assert strong.movement_timing == "STRONGLY_SUPPORTIVE"
    assert weak.movement_timing == "NOT_ACTIVE"


def test_cross_domain_context_is_association_only():
    result = TravelRelocationSynthesisEngine().synthesize({"movement_scores": {"relocation_potential": .8}}, career_context={"relocation_signal": "STRONG"}, education_context={"study_signal": "MODERATE"}, relationship_context={"relationship_signal": "MIXED"})
    assert len(result.conditions) >= 3
    assert "causal" in " ".join(result.reasoning_trace)


def test_benchmark_and_holdout_sizes():
    assert len(build_travel_benchmark()) >= 140
    assert len(build_travel_holdout()) >= 50


def test_governance_blocks_unsafe_outputs():
    assert "IMMIGRATION_ADVICE" in TRAVEL_RELOCATION_DOMAIN["blocked_outputs"]
    assert TRAVEL_RELOCATION_DOMAIN["varga_policy"]["D4"] == "CALCULATION_VALIDATED_INTERPRETATION_NOT_VALIDATED"
