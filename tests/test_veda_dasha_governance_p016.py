from datetime import datetime, timezone

from engines.ai.knowledge.dasha_governance import (
    DASHA_SEQUENCE,
    TOTAL_YEARS,
    build_phase_bundle,
    canonical_timing_facts,
    nakshatra_info,
    validate_bundle,
)


def test_sequence_and_nominal_cycle_are_governed():
    assert DASHA_SEQUENCE == ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    assert TOTAL_YEARS == 120.0


def test_nakshatra_boundaries_and_padas_are_deterministic():
    assert nakshatra_info(0.0)["index"] == 0
    assert nakshatra_info(13.3333333334)["index"] == 1
    assert nakshatra_info(13.3333333333)["pada"] == 4
    assert nakshatra_info(359.999999)["index"] == 26


def test_canonical_period_hierarchy_is_continuous_and_contained():
    facts = canonical_timing_facts(95.0, datetime(1984, 11, 3, 1, tzinfo=timezone.utc), datetime(2000, 1, 1, tzinfo=timezone.utc), "Asia/Kolkata")
    periods = facts["mahadashas"]
    assert facts["calculation_version"] == "P016_CANONICAL_TIMING"
    assert len(periods) == 18
    for left, right in zip(periods, periods[1:]):
        assert left["end_utc"] == right["start_utc"]
    for maha in periods:
        children = maha["antardashas"]
        assert len(children) == 9
        assert children[0]["parent_lord"] == maha["lord"]
        assert children[0]["start_utc"] == maha["start_utc"]
        assert children[-1]["end_utc"] == maha["end_utc"]


def test_timezone_is_presentation_only_and_high_stakes_is_restricted():
    facts = canonical_timing_facts(10.0, datetime(1984, 11, 3, 1, tzinfo=timezone.utc), timezone_name="Asia/Kolkata")
    assert facts["mahadashas"][0]["start_local"].endswith("+05:30")
    assert "DEATH" in facts["high_stakes_restrictions"]
    assert facts["interpretation_status"] == "FOUNDATION_RESEARCH_REQUIRED"


def test_p016_bundle_has_no_unexplained_shadow_divergence():
    bundle = build_phase_bundle()
    result = validate_bundle(bundle)
    assert result["is_valid"] is True
    assert result["unexplained_divergences"] == []
