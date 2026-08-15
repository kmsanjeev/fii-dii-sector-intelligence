import json

from scripts.veda_loop import classify_failure, compose_prompt, partial_completion, select_next_priority, select_track


def test_priority_escalates_empirical_and_prospective_evidence():
    assert select_next_priority({"verified_empirical_cases": 0, "prospective_predictions": 0}) == "EMPIRICAL_OR_PROSPECTIVE_EVIDENCE"


def test_prompt_is_bounded_to_one_activity_and_preserves_safety():
    prompt = compose_prompt({"verified_empirical_cases": 0, "prospective_predictions": 0, "loop_number": 1})
    assert "exactly ONE" in prompt
    assert "no fake empirical cases" in prompt
    assert "outer controller will invoke Codex" in prompt


def test_blocked_empirical_track_switches_to_prospective_then_timing():
    assert select_track({"verified_empirical_cases": 0, "prospective_predictions": 0, "blocked_tracks": ["EMPIRICAL"]}) == "PROSPECTIVE"
    assert select_track({"verified_empirical_cases": 0, "prospective_predictions": 0, "blocked_tracks": ["EMPIRICAL", "PROSPECTIVE"]}) == "TIMING"


def test_failure_and_partial_completion_classification_is_deterministic():
    assert classify_failure(exit_code=124, hard_timeout=True) == "CODEX_HARD_TIMEOUT"
    assert classify_failure(exit_code=1) == "CODEX_EXIT_FAILURE"
    assert partial_completion(starting_head="a", ending_head="b", output="", timed_out=True) == "ACTIVITY_COMPLETED_DESPITE_PROCESS_TIMEOUT"
    assert partial_completion(starting_head="a", ending_head="a", output="", timed_out=True) == "ACTIVITY_INCOMPLETE"
