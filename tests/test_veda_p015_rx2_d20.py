"""Independent P015-RX2 D20 calculation fixtures and regression checks."""

from decimal import Decimal, ROUND_FLOOR

from engines.ai.knowledge.varga_governance import VARGA_METHODS, canonical_varga_fact, varga_sign
from engines.intelligence.kundli_engine import KundliEngine, SIGNS


METHOD = "d20_vimshamsha_bphs_category_start_v1"
DIVISIONS = 20
SEGMENT = Decimal("1.5")
MOVABLE = {0, 3, 6, 9}
FIXED = {1, 4, 7, 10}


def source_expected(longitude: float) -> str:
    normalized = Decimal(str(longitude % 360.0))
    source_sign = int(normalized // Decimal("30"))
    in_sign = normalized % Decimal("30")
    division = min(int((in_sign / SEGMENT).to_integral_value(rounding=ROUND_FLOOR)), 19)
    start = 0 if source_sign in MOVABLE else 8 if source_sign in FIXED else 4
    return SIGNS[(start + division) % 12]


def test_method_registry_and_metadata_are_explicit():
    record = VARGA_METHODS["D20"]
    assert record["method"] == METHOD
    assert record["method_id"] == "D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1"
    assert record["method_version"] == "1.0"
    assert record["calculation_status"] == "PARTIALLY_VALIDATED"
    assert record["interpretation_status"] == "NOT_VALIDATED"
    assert record["mapping_status"] == "SOURCE_MAPPING_INCOMPLETE"


def test_full_source_derived_grid_has_12x20_cases_and_zero_errors():
    cases = [(sign * 30 + division * 1.5 + 0.25) for sign in range(12) for division in range(20)]
    assert len(cases) == 240
    assert all(varga_sign(longitude, 20, METHOD) == source_expected(longitude) for longitude in cases)


def test_exact_boundaries_and_just_below_are_lower_inclusive_upper_exclusive():
    for sign in range(12):
        base = sign * 30
        for division in range(1, 20):
            boundary = base + division * 1.5
            assert varga_sign(boundary, 20, METHOD) == source_expected(boundary)
            below = boundary - 0.000001
            assert varga_sign(below, 20, METHOD) == source_expected(below)


def test_all_modalities_and_wraparound_are_correct():
    assert all(varga_sign(sign * 30 + 0.1, 20, METHOD) == expected for sign, expected in ((0, "Aries"), (3, "Aries"), (6, "Aries"), (9, "Aries"), (1, "Sagittarius"), (4, "Sagittarius"), (7, "Sagittarius"), (10, "Sagittarius"), (2, "Leo"), (5, "Leo"), (8, "Leo"), (11, "Leo")))
    assert varga_sign(29 * 30 + 28.6, 20, METHOD) == "Pisces"
    assert varga_sign(29 * 30 + 29.999999, 20, METHOD) == "Pisces"


def test_supported_points_and_ascendant_use_selected_method():
    engine = KundliEngine()
    points = {"Ascendant": 29.999999, "Sun": 0.0, "Moon": 7.5, "Mars": 15.0, "Mercury": 22.5, "Jupiter": 60.0, "Venus": 120.0, "Saturn": 210.0, "Rahu": 300.0, "Ketu": 330.0}
    assert all(engine._varga_sign(longitude, 20, METHOD) == source_expected(longitude) for longitude in points.values())
    assert all(engine._divisional_charts(points)["D20"][point] == source_expected(longitude) for point, longitude in points.items())


def test_legacy_generic_method_is_preserved_only_for_comparison():
    engine = KundliEngine()
    assert engine._varga_sign(45.0, 20, "general") != engine._varga_sign(45.0, 20, METHOD)
    assert engine._varga_sign(45.0, 20, "general") in SIGNS


def test_no_selected_method_odd_even_leakage():
    movable = [varga_sign(sign * 30 + 0.1, 20, METHOD) for sign in (0, 3, 6, 9)]
    fixed = [varga_sign(sign * 30 + 0.1, 20, METHOD) for sign in (1, 4, 7, 10)]
    dual = [varga_sign(sign * 30 + 0.1, 20, METHOD) for sign in (2, 5, 8, 11)]
    assert movable == ["Aries"] * 4
    assert fixed == ["Sagittarius"] * 4
    assert dual == ["Leo"] * 4


def test_deterministic_development_and_holdout_benchmarks():
    development = [(sign * 30 + division * 1.5 + degree) for sign in range(12) for division in range(20) for degree in (0.1, 0.75, 1.49)]
    holdout = [((index * 37) % 360) + ((index % 19) * 0.071) for index in range(80)]
    assert len(development) == 720
    assert len(holdout) == 80
    assert all(varga_sign(longitude, 20, METHOD) == source_expected(longitude) for longitude in development + holdout)


def test_canonical_fact_preserves_calculation_interpretation_separation():
    fact = canonical_varga_fact("VEDA-GRAHA-SUN", 45.0, "D20")
    assert fact["varga_sign"] == "VEDA-RASHI-LIBRA"
    assert fact["calculation_status"] == "PARTIALLY_VALIDATED"
    assert fact["interpretation_status"] == "NOT_VALIDATED"
