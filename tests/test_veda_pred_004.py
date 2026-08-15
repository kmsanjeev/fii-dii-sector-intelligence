from engines.ai.knowledge.prospective_pilot_governance import PRED_004


def test_pilot_reuses_shared_contract_without_fake_records():
    assert PRED_004["status"] == "PASS_WITH_CONDITION"
    assert PRED_004["predictions_created"] == 0
    assert PRED_004["resolved_outcomes"] == 0
    assert PRED_004["required_lock_state"] == "LOCKED"
    assert PRED_004["approved_core_promoted"] == 0


def test_outcome_states_are_explicit_and_non_retroactive():
    assert "PENDING" in PRED_004["outcome_states"]
    assert "OBSERVED_MISS" in PRED_004["outcome_states"]
    assert "UNRESOLVED" in PRED_004["outcome_states"]
