import pytest

from scripts.veda_signal_marriage_001 import (
    EVENT_CLASS,
    SIGNAL_ID,
    build_audit,
    contract_hash,
    evaluate_signal,
    precision_is_allowed,
)


def test_contract_is_deterministic_and_narrow():
    first = build_audit()
    second = build_audit()
    assert first["signal_id"] == SIGNAL_ID
    assert first["event_class"] == EVENT_CLASS == "MARRIAGE"
    assert first["signal_hash"] == second["signal_hash"] == contract_hash()
    assert first["signal_governance"] == "SOURCE_GOVERNABLE"
    assert first["production_activation"] is False
    assert first["holdout_accessed"] is False


def test_signal_uses_only_explicit_seventh_house_membership():
    assert evaluate_signal(
        mahadasha_lord="Venus", seventh_lord="Mars", planets_in_seventh=["Venus"], planets_aspecting_seventh=[]
    ) == "SIGNAL_PRESENT"
    assert evaluate_signal(
        mahadasha_lord="Jupiter", seventh_lord="Mars", planets_in_seventh=[], planets_aspecting_seventh=[]
    ) == "SIGNAL_ABSENT"
    assert evaluate_signal(
        mahadasha_lord=None, seventh_lord="Mars", planets_in_seventh=[], planets_aspecting_seventh=[]
    ) == "SIGNAL_INDETERMINATE"


def test_date_precision_never_invents_precision():
    assert precision_is_allowed("EXACT", "2020-04-12", "2020-04-12")
    assert not precision_is_allowed("EXACT", "2020-04", "2020-04-12")
    assert precision_is_allowed("MONTH", "2020-04-12", "2020-04-01")
    assert not precision_is_allowed("MONTH", "2020-05-12", "2020-04-01")
    assert precision_is_allowed("YEAR", "2020-11-12", "2020")
    assert not precision_is_allowed("YEAR", "2021-01-01", "2020")
    with pytest.raises(AssertionError):
        assert precision_is_allowed("DAY", "2020-04-12", "2020-04-12")
