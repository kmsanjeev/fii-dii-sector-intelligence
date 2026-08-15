from engines.intelligence.property_synthesis_engine import PropertySynthesisEngine, build_property_benchmark, build_property_holdout


def test_property_contract_separates_ownership_and_residence():
    result = PropertySynthesisEngine().synthesize({"property_scores": {"ownership": .9, "residence_stability": .2}})
    assert result.property_ownership == "STRONG"
    assert result.residential_stability == "CHANGE_PRONE"
    assert result.domain == "PROPERTY"


def test_wealth_does_not_become_property_evidence():
    result = PropertySynthesisEngine().synthesize({"property_scores": {"potential": .2}}, wealth_context={"capacity": "STRONG"})
    assert result.property_potential == "WEAK"
    assert any("wealth context" in item for item in result.conditions)
    assert result.contradictions


def test_d4_is_explicitly_not_validated_and_d1_path_continues():
    result = PropertySynthesisEngine().synthesize({"property_scores": {"potential": .8}})
    assert result.property_potential == "STRONG"
    assert result.d4_status.startswith("D4_NOT_")
    assert result.missing_data


def test_promise_and_timing_are_separate():
    result = PropertySynthesisEngine().synthesize({"property_scores": {"potential": .9}, "dasha_activation": "INACTIVE"})
    assert result.property_potential == "STRONG"
    assert result.timing == "NOT_ACTIVE"


def test_dasha_transit_convergence_is_timing_only():
    result = PropertySynthesisEngine().synthesize({"property_scores": {"potential": .9}, "dasha_activation": "SUPPORTIVE", "transit_trigger": "SUPPORTIVE"})
    assert result.timing == "STRONGLY_SUPPORTIVE"


def test_benchmark_and_holdout_sizes():
    assert len(build_property_benchmark()) >= 120
    assert len(build_property_holdout()) >= 40


def test_safety_boundaries_are_explicit():
    result = PropertySynthesisEngine().synthesize({"property_scores": {"dispute": .8}})
    assert result.safety_status == "NO_FINANCIAL_OR_LEGAL_ADVICE"
    assert any("property-price" in item for item in result.reasoning_trace)
