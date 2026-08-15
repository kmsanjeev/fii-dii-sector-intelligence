from engines.ai.knowledge.muhurta_bala_governance import KNOW_MUH_002


def test_classical_bala_context_is_promoted_without_formula_promotion():
    claims = KNOW_MUH_002["claims"]
    assert KNOW_MUH_002["status"] == "PASS_WITH_CONDITION"
    assert KNOW_MUH_002["approved_core_promoted"] == 0
    assert claims["COMBINED_TARA_CHANDRA_BALA_CONTEXT"]["status"] == "VALIDATED_KNOWLEDGE"
    assert claims["COMBINED_TARA_CHANDRA_BALA_CONTEXT"]["formula_validated"] is False
    assert claims["COMBINED_TARA_CHANDRA_BALA_CONTEXT"]["production_activation"] == "DISABLED"


def test_individual_bala_algorithms_remain_research_candidates():
    claims = KNOW_MUH_002["claims"]
    assert claims["TARABALA_ALGORITHM"]["status"] == "RESEARCH_CANDIDATE"
    assert claims["CHANDRABALA_ALGORITHM"]["status"] == "RESEARCH_CANDIDATE"
    assert all(not row["formula_validated"] for row in claims.values())
