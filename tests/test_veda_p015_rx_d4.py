from engines.ai.knowledge.varga_governance import varga_sign
from engines.intelligence.kundli_engine import KundliEngine, SIGNS


def _expected(source_sign: int, division: int) -> str:
    return SIGNS[(source_sign + (0, 3, 6, 9)[division - 1]) % 12]


def test_all_12_signs_and_four_divisions_use_14710_mapping():
    for source_sign in range(12):
        for division in range(1, 5):
            longitude = source_sign * 30 + (division - 1) * 7.5 + 1.0
            assert varga_sign(longitude, 4, "chaturthamsa_14710") == _expected(source_sign, division)


def test_exact_boundaries_are_lower_inclusive_and_upper_exclusive():
    cases = ((0.0, 1), (7.5, 2), (15.0, 3), (22.5, 4), (29.999999, 4))
    for degree, division in cases:
        assert varga_sign(degree, 4, "chaturthamsa_14710") == _expected(0, division)


def test_wraparound_for_capricorn_aquarius_pisces():
    assert varga_sign(270.0 + 7.5, 4, "chaturthamsa_14710") == "Aries"
    assert varga_sign(300.0 + 15.0, 4, "chaturthamsa_14710") == "Leo"
    assert varga_sign(330.0 + 22.5, 4, "chaturthamsa_14710") == "Sagittarius"


def test_runtime_routes_only_d4_to_source_selected_method():
    engine = KundliEngine()
    assert engine._varga_sign(7.5, 4, "chaturthamsa_14710") == "Cancer"
    assert engine._varga_sign(7.5, 9, "navamsa") == "Gemini"
    assert engine._varga_sign(7.5, 10, "dasamsa") == "Gemini"


def test_ascendant_and_supported_points_share_numeric_method():
    engine = KundliEngine()
    longitudes = {"Ascendant": 29.999999, "Sun": 0.0, "Moon": 7.5, "Mars": 15.0, "Mercury": 22.5, "Jupiter": 60.0, "Venus": 120.0, "Saturn": 210.0, "Rahu": 300.0, "Ketu": 120.0}
    for longitude in longitudes.values():
        assert engine._varga_sign(longitude, 4, "chaturthamsa_14710") in SIGNS


def test_legacy_generic_method_is_not_selected_for_d4():
    engine = KundliEngine()
    old = engine._varga_sign(7.5, 4, "general")
    new = engine._varga_sign(7.5, 4, "chaturthamsa_14710")
    assert old != new


def test_deterministic_benchmark_and_holdout_sizes():
    development = [(sign, division, degree) for sign in range(12) for division in range(1, 5) for degree in (0.1, 7.499999, 7.5, 14.999999, 15.0, 22.499999, 22.5, 29.999999)]
    holdout = [(index * 37 % 360, (index % 4) + 1) for index in range(40)]
    assert len(development) >= 120
    assert len(holdout) == 40
    for longitude, division in holdout:
        source_sign = int(longitude // 30)
        degree = longitude % 30
        actual = varga_sign(longitude, 4, "chaturthamsa_14710")
        expected = _expected(source_sign, min(int(degree / 7.5) + 1, 4))
        assert actual == expected
