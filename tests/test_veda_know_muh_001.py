from engines.ai.knowledge.muhurta_governance import KNOW_MUH_001


def test_scoped_classical_claims_are_promoted_without_activation():
    claims = KNOW_MUH_001["claims"]
    assert KNOW_MUH_001["status"] == "PASS_WITH_CONDITION"
    assert KNOW_MUH_001["approved_core_promoted"] == 0
    assert claims["NAKSHATRA_ACTION_CLASSES"]["status"] == "VALIDATED_KNOWLEDGE"
    assert claims["TITHI_KARANA_ACTION_CLASSES"]["status"] == "VALIDATED_KNOWLEDGE"
    assert claims["MARRIAGE_SPECIFIC_KARANA_CONDITIONS"]["scope"] == "MARRIAGE_CONTEXT_ONLY"
    assert all(row["production_activation"] == "DISABLED" for row in claims.values())


def test_personal_bala_claims_remain_reference_level():
    claims = KNOW_MUH_001["claims"]
    assert claims["TARABALA"]["status"] == "RESEARCH_CANDIDATE"
    assert claims["CHANDRABALA"]["status"] == "RESEARCH_CANDIDATE"
    assert claims["TARABALA"]["authority"] == "REFERENCE_NOT_VERIFIED"
