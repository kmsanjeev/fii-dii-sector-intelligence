import json

from scripts.veda_loop import compose_prompt, select_next_priority


def test_priority_escalates_empirical_and_prospective_evidence():
    assert select_next_priority({"verified_empirical_cases": 0, "prospective_predictions": 0}) == "EMPIRICAL_OR_PROSPECTIVE_EVIDENCE"


def test_prompt_is_bounded_to_one_activity_and_preserves_safety():
    prompt = compose_prompt({"verified_empirical_cases": 0, "prospective_predictions": 0, "loop_number": 1})
    assert "exactly ONE" in prompt
    assert "no fake empirical cases" in prompt
    assert "outer controller will invoke Codex" in prompt
