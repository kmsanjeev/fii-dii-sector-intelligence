from engines.intelligence.p027_synthesis import (
    ConfidenceBand,
    ContradictionSeverity,
    EvidenceRole,
    P027SynthesisEngine,
    SynthesisEvidence,
)


def _evidence(**overrides):
    base = {
        "evidence_id": "d1-1",
        "claim": "Career promise is present",
        "source_engine": "D1",
        "source_phase": "P014",
        "chart_id": "chart-a",
        "subject_id": "person-a",
        "evidence_type": "STRUCTURAL",
        "authority_class": "APPROVED_CORE",
        "knowledge_zone": "APPROVED_CORE",
        "strength": "HIGH",
        "lineage_id": "career-promise",
        "supports": "CAREER",
        "validation_state": "VALIDATED",
    }
    base.update(overrides)
    return SynthesisEvidence(**base)


def test_evidence_roles_separate_promise_timing_and_condition():
    result = P027SynthesisEngine().synthesize(
        "career",
        [
            _evidence(),
            _evidence(evidence_id="d10-1", source_engine="D10", source_phase="P015", evidence_type="VARGA", lineage_id="career-varga", claim="D10 confirms career specialization"),
            _evidence(evidence_id="dasha-1", source_engine="Dasha", source_phase="DASHA", evidence_type="DASHA", lineage_id="career-timing", role=None, time_scope="2027", claim="Dasha activates the career promise"),
        ],
        domain="CAREER",
    )
    assert result.timing.structural_promise == "SUPPORTED"
    assert result.timing.primary_window == "2027"
    assert result.convergence_state == "MODERATE_CONVERGENCE"
    assert result.confidence in {ConfidenceBand.HIGH, ConfidenceBand.VERY_HIGH}


def test_lineage_prevents_rule_count_confidence_inflation():
    rows = [_evidence(evidence_id=f"same-{i}", rule_family="same-rule", factor="same-fact") for i in range(8)]
    result = P027SynthesisEngine().synthesize("career", rows)
    assert len(result.redundant_evidence) == 7
    assert result.confidence in {ConfidenceBand.LOW, ConfidenceBand.MODERATE}


def test_contradiction_is_explicit_and_reduces_confidence():
    result = P027SynthesisEngine().synthesize(
        "marriage",
        [_evidence(), _evidence(evidence_id="d9-negative", source_engine="D9", source_phase="P015", evidence_type="VARGA", lineage_id="marriage-varga", claim="D9 weakens the marriage promise", direction="OPPOSES", opposes="CAREER", authority_class="APPROVED_CORE")],
    )
    assert result.contradiction_state in {ContradictionSeverity.MODERATE, ContradictionSeverity.MINOR}
    assert result.contradictions
    assert result.confidence in {ConfidenceBand.LOW, ConfidenceBand.MODERATE}


def test_missing_data_and_experimental_evidence_are_not_promoted_in_safe_mode():
    result = P027SynthesisEngine().synthesize("health", [_evidence(evidence_id="experimental", knowledge_zone="EXPERIMENTAL", authority_class="EXPERIMENTAL")], mode="PRODUCTION_SAFE", missing_data=["D9_NOT_IMPLEMENTED"], birth_time_precision="RANGE")
    assert result.confidence == ConfidenceBand.VERY_LOW
    assert "D9_NOT_IMPLEMENTED" in " ".join(result.reasoning_trace)


def test_two_chart_contract_preserves_identity_and_declines_compatibility_claim():
    value = P027SynthesisEngine().compare_charts({"chart_id": "a"}, {"chart_id": "b"}, subject_a="alice", subject_b="bob", relationship_type="PARTNER", comparison_domain="MARRIAGE")
    assert value["chart_a"] == "a"
    assert value["chart_b"] == "b"
    assert value["state"] == "FOUNDATIONAL_COMPARISON_ONLY"


def test_deterministic_property_benchmark_has_100_scenarios():
    engine = P027SynthesisEngine()
    scenarios = []
    for index in range(100):
        rows = [_evidence(evidence_id=f"case-{index}-d1", lineage_id=f"case-{index}-d1")]
        if index % 2 == 0:
            rows.append(_evidence(evidence_id=f"case-{index}-dasha", source_engine="Dasha", source_phase="DASHA", evidence_type="DASHA", lineage_id=f"case-{index}-timing", claim="Activation window", time_scope="2027"))
        scenarios.append(engine.synthesize(f"scenario-{index}", rows))
    assert len(scenarios) == 100
    assert all(item.chart_attribution["chart-a"] == "person-a" for item in scenarios)
