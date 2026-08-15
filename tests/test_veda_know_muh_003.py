from engines.ai.knowledge.muhurta_event_governance import KNOW_MUH_003


def test_event_families_are_scoped_and_inactive():
    assert KNOW_MUH_003["status"] == "PASS_WITH_CONDITION"
    assert KNOW_MUH_003["approved_core_promoted"] == 0
    assert KNOW_MUH_003["production_activation"] == "DISABLED"
    assert KNOW_MUH_003["claims"]["NAKSHATRA_ACTION_FAMILIES"]["status"] == "VALIDATED_KNOWLEDGE"
    assert KNOW_MUH_003["claims"]["MARRIAGE_KARANA_CONDITIONS"]["scope"] == "MARRIAGE_CONTEXT_ONLY"


def test_generic_auspiciousness_is_not_created():
    claim = KNOW_MUH_003["claims"]["GENERAL_AUSPICIOUSNESS_SCORE"]
    assert claim["status"] == "DEFERRED"
    assert claim["scope"] == "NOT_EXECUTABLE"
