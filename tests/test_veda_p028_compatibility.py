from engines.intelligence.p027_synthesis import SynthesisEvidence
from engines.intelligence.p028_compatibility import P028CompatibilityEngine, RelationshipSubject, RelationshipType


def subjects():
    return RelationshipSubject("chart-a", "person-a", "A", "EXACT", "SUPPORTED"), RelationshipSubject("chart-b", "person-b", "B", "APPROXIMATE", "MIXED")


def test_subject_contract_and_asymmetric_evidence_are_preserved():
    a, b = subjects()
    result = P028CompatibilityEngine().analyze(relationship_id="rel-1", subject_a=a, subject_b=b, relationship_type=RelationshipType.MARRIAGE.value, evidence=[SynthesisEvidence("a", "A experiences B as stabilizing", chart_id="chart-a", subject_id="person-a", direction="A_TO_B", domain="EMOTIONAL_ALIGNMENT"), SynthesisEvidence("b", "B experiences A as demanding", chart_id="chart-b", subject_id="person-b", direction="B_TO_A", domain="COMMUNICATION_ALIGNMENT")])
    assert result.chart_a_id == "chart-a" and result.chart_b_id == "chart-b"
    assert {item["direction"] for item in result.asymmetries} == {"A_TO_B", "B_TO_A"}
    assert result.timing["state"] == "INSUFFICIENT_DATA"


def test_missing_traditional_method_is_explicit_not_fabricated():
    a, b = subjects()
    result = P028CompatibilityEngine().analyze(relationship_id="rel-2", subject_a=a, subject_b=b, relationship_type="ROMANTIC_RELATIONSHIP", evidence=[])
    assert result.traditional_matching["state"] == "NOT_IMPLEMENTED"
    assert result.traditional_matching["score"] is None
    assert result.overall_state == "INSUFFICIENT_DATA"


def test_foreign_chart_or_subject_evidence_is_rejected():
    a, b = subjects()
    try:
        P028CompatibilityEngine().analyze(relationship_id="rel-3", subject_a=a, subject_b=b, relationship_type="MARRIAGE", evidence=[SynthesisEvidence("x", "foreign", chart_id="chart-c", subject_id="person-c")])
    except ValueError as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("foreign chart evidence was accepted")


def test_multidimensional_result_does_not_create_single_score():
    a, b = subjects()
    result = P028CompatibilityEngine().analyze(relationship_id="rel-4", subject_a=a, subject_b=b, relationship_type="LONG_TERM_PARTNERSHIP", evidence=[{"evidence_id": "x", "claim": "shared emotional support", "chart_id": "chart-a", "subject_id": "person-a", "direction": "SUPPORTS", "domain": "EMOTIONAL_ALIGNMENT"}])
    assert len(result.dimensions) >= 9
    assert "score" not in result.to_dict()


def test_deterministic_benchmark_and_holdout_sizes():
    a, b = subjects()
    engine = P028CompatibilityEngine()
    development = [engine.analyze(relationship_id=f"dev-{i}", subject_a=a, subject_b=b, relationship_type="MARRIAGE", evidence=[]) for i in range(100)]
    holdout = [engine.analyze(relationship_id=f"holdout-{i}", subject_a=a, subject_b=b, relationship_type="MARRIAGE", evidence=[]) for i in range(30)]
    assert len(development) == 100 and len(holdout) == 30
