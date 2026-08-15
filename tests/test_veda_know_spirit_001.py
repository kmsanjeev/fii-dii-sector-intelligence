"""Focused KNOW-SPIRIT-001 governance and independent D20 audit checks."""

from engines.ai.knowledge.spirituality_governance import SPIRITUALITY_DOMAIN
from engines.ai.knowledge.varga_governance import VARGA_METHODS, canonical_varga_fact, varga_sign


def _source_d20_sign(longitude: float) -> str:
    """Independent diagnostic fixture from BPHS Ch. 6.17 category starts."""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign = int((longitude % 360.0) / 30.0)
    degree = (longitude % 30.0)
    amsa = min(int(degree / 1.5), 19)
    start = {"movable": 0, "fixed": 8, "dual": 4}["movable" if sign in {0, 3, 6, 9} else "fixed" if sign in {1, 4, 7, 10} else "dual"]
    return signs[(start + amsa) % 12]


def test_activity_is_registered_without_autonomous_promotion():
    audit = SPIRITUALITY_DOMAIN["know_spirit_001"]
    assert audit["status"] == "IN_IMPLEMENTATION"
    assert audit["d20_calculation_decision"] == "D20_METHOD_VARIANTS_REQUIRE_SPLIT"
    assert audit["d20_interpretation_decision"] == "D20_INTERPRETATION_RESEARCH_CANDIDATE"
    assert audit["approved_core_promoted"] == 0


def test_d20_current_runtime_metadata_is_source_selected_but_qualified():
    assert VARGA_METHODS["D20"]["method"] == "d20_vimshamsha_bphs_category_start_v1"
    fact = canonical_varga_fact("VEDA-GRAHA-SUN", 15.0, "D20")
    assert fact["validation_status"] == "VALIDATED_WITH_CONDITIONS"
    assert fact["interpretation_status"] == "NOT_VALIDATED"
    assert fact["method_id"] == "D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1"
    assert fact["method_version"] == "1.0"
    assert fact["calculation_status"] == "PARTIALLY_VALIDATED"
    assert fact["mapping_status"] == "SOURCE_MAPPING_INCOMPLETE"


def test_independent_bphs_category_starts_are_routed_for_all_modalities():
    for longitude in (15.0, 45.0, 75.0, 105.0, 135.0, 165.0, 195.0, 225.0, 255.0, 285.0, 315.0, 345.0):
        assert varga_sign(longitude, 20, "d20_vimshamsha_bphs_category_start_v1") == _source_d20_sign(longitude)


def test_d20_is_not_interpretively_enabled_by_source_scope_alone():
    assert SPIRITUALITY_DOMAIN["d20_audit"]["interpretation_status"] == "NOT_VALIDATED"
    assert SPIRITUALITY_DOMAIN["varga_policy"]["D20"] == "CALCULATION_AVAILABLE_INTERPRETATION_NOT_VALIDATED"
    assert "ENLIGHTENMENT_CERTAINTY" in SPIRITUALITY_DOMAIN["blocked_outputs"]
