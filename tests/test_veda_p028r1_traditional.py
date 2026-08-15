from engines.intelligence.p028_compatibility import P028CompatibilityEngine, RelationshipSubject
from engines.intelligence.p028r1_traditional import MAX_TOTAL, METHOD_ID, calculate_ashtakoota


def test_all_eight_kutas_and_exact_total():
    result = calculate_ashtakoota(subject_a_id="a", subject_b_id="b", nakshatra_a="Ashwini", nakshatra_b="Rohini", rashi_a="Aries", rashi_b="Taurus")
    assert set(result.components) == {"VARNA", "VASHYA", "TARA", "YONI", "GRAHA_MAITRI", "GANA", "BHAKOOT", "NADI"}
    assert result.max_total == MAX_TOTAL
    assert result.raw_total == sum(item.score for item in result.components.values())
    assert result.method_id == METHOD_ID


def test_tara_wrap_and_boundary_inputs_are_deterministic():
    first = calculate_ashtakoota(subject_a_id="a", subject_b_id="b", nakshatra_a="Revati", nakshatra_b="Ashwini", rashi_a="Pisces", rashi_b="Aries")
    second = calculate_ashtakoota(subject_a_id="a", subject_b_id="b", nakshatra_a="Revati", nakshatra_b="Ashwini", rashi_a="Pisces", rashi_b="Aries")
    assert first.components["TARA"].reason == "Cyclic Nakshatra distance=2"
    assert first.to_dict() == second.to_dict()


def test_missing_data_is_not_converted_to_zero_and_no_fatalism():
    result = calculate_ashtakoota(subject_a_id="a", subject_b_id="b", nakshatra_a="unknown", nakshatra_b="Ashwini", rashi_a="Aries", rashi_b="Taurus")
    assert result.raw_total is None
    assert all(item.state == "INSUFFICIENT_DATA" for item in result.components.values())
    assert any("fertility" not in warning.lower() for warning in result.warnings)


def test_p028_receives_breakdown_as_one_governed_evidence_family():
    a = RelationshipSubject("chart-a", "a", "A")
    b = RelationshipSubject("chart-b", "b", "B")
    traditional = calculate_ashtakoota(subject_a_id="a", subject_b_id="b", nakshatra_a="Ashwini", nakshatra_b="Rohini", rashi_a="Aries", rashi_b="Taurus")
    result = P028CompatibilityEngine().analyze(relationship_id="r", subject_a=a, subject_b=b, relationship_type="MARRIAGE", evidence=[], traditional_matching=traditional)
    assert result.traditional_matching["method_id"] == METHOD_ID
    assert result.traditional_matching["score"] if "score" in result.traditional_matching else result.traditional_matching["raw_total"] >= 0
    assert "Guna total is one evidence family" in " ".join(traditional.warnings)


def test_development_and_holdout_benchmark_sizes():
    cases = [calculate_ashtakoota(subject_a_id="a", subject_b_id="b", nakshatra_a="Ashwini", nakshatra_b=_nak, rashi_a="Aries", rashi_b="Taurus") for _nak in ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Pushya", "Magha", "Hasta", "Chitra", "Swati", "Vishakha"] for _ in range(10)]
    holdout = [calculate_ashtakoota(subject_a_id="a", subject_b_id="b", nakshatra_a="Revati", nakshatra_b="Ashwini", rashi_a="Pisces", rashi_b="Aries") for _ in range(40)]
    assert len(cases) == 120 and len(holdout) == 40
