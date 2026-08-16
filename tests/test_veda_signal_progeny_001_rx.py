from __future__ import annotations

from scripts.veda_signal_progeny_001 import evaluate
from scripts.veda_signal_progeny_001_rx import _metrics, _reachability


def test_fixed_signal_fixtures_are_reachable_and_safe():
    positive = evaluate({"fifth_lord_house": 5, "fifth_lord_exalted": False, "fifth_lord_conjunct_jupiter": True, "fifth_lord_aspected_by_jupiter": False, "mahadasha": "Jupiter", "antardasha": "Sun", "sun_house": 5, "sun_exalted": False, "sun_own_sign": False, "sun_strong": True, "sun_house_from_mahadasha_lord": 5})
    negative = evaluate({"fifth_lord_house": 5, "fifth_lord_exalted": False, "fifth_lord_conjunct_jupiter": True, "fifth_lord_aspected_by_jupiter": False, "mahadasha": "Jupiter", "antardasha": "Sun", "sun_house": 12, "sun_exalted": False, "sun_own_sign": False, "sun_strong": True, "sun_house_from_mahadasha_lord": 12})
    indeterminate = evaluate({"fifth_lord_house": None, "mahadasha": "Jupiter"})
    assert positive["state"] == "SIGNAL_PRESENT"
    assert negative["state"] == "CONDITIONAL_BLOCKED"
    assert indeterminate["state"] == "INDETERMINATE"


def test_prevalence_thresholds_are_frozen_and_deterministic():
    assert _reachability(0.0) == "ZERO_PREVALENCE"
    assert _reachability(0.005) == "NEAR_ZERO_PREVALENCE"
    assert _reachability(0.015) == "VERY_LOW_PREVALENCE"
    assert _reachability(0.05) == "LOW_PREVALENCE"
    assert _reachability(0.15) == "NORMAL_PREVALENCE"


def test_population_audit_is_two_run_deterministic():
    rows = [
        {"structural_condition": True, "structural_and_timing_seconds": 100.0, "jupiter_md_seconds": 200.0, "jupiter_sun_ad_seconds": 100.0, "signal_present_seconds": 50.0, "indeterminate_seconds": 0.0, "observation_seconds": 1000.0, "subject_prevalence": 0.05},
        {"structural_condition": False, "structural_and_timing_seconds": 0.0, "jupiter_md_seconds": 0.0, "jupiter_sun_ad_seconds": 0.0, "signal_present_seconds": 0.0, "indeterminate_seconds": 0.0, "observation_seconds": 1000.0, "subject_prevalence": 0.0},
    ]
    first = _metrics(rows)
    second = _metrics(rows)
    assert first == second
    assert first["subjects_analyzed"] == 2
    assert first["time_weighted_signal_prevalence"] == 0.025
    assert first["structural_and_timing_rate"] == 0.5
