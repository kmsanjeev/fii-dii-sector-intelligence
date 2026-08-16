from scripts.veda_signal_progeny_001 import CONTRACT, evaluate, signal_hash


def test_progeny_signal_is_frozen_narrow_and_deterministic():
    assert CONTRACT["signal_id"] == "VEDA-SIGNAL-PROGENY-OCCURRENCE-001"
    assert signal_hash() == signal_hash()
    assert CONTRACT["timing_method"] == "VIMSHOTTARI_JUPITER_MAHADASHA_SUN_ANTARDASHA"
    assert "D7 calculation/interpretation is not consumed" in " ".join(CONTRACT["method_limits"])


def test_progeny_signal_requires_structure_and_timing_and_allows_indeterminate():
    facts = {
        "fifth_lord_house": 5,
        "fifth_lord_exalted": False,
        "fifth_lord_conjunct_jupiter": False,
        "fifth_lord_aspected_by_jupiter": False,
        "mahadasha": "Jupiter",
        "antardasha": "Sun",
        "sun_house": 9,
        "sun_strong": True,
        "sun_exalted": False,
        "sun_own_sign": False,
    }
    assert evaluate(facts)["state"] == "SIGNAL_PRESENT"
    assert evaluate({})["state"] == "INDETERMINATE"
    facts["sun_house"] = 8
    assert evaluate(facts)["state"] == "CONDITIONAL_BLOCKED"
