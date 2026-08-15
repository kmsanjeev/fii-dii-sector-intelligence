import json

import pytest

from scripts.veda_loop import NoAvailableTrackError, activity_identity, classify_failure, classify_material_progress, classify_output, completion_state, compose_prompt, partial_completion, select_next_priority, select_track


def test_priority_escalates_empirical_and_prospective_evidence():
    assert select_next_priority({"verified_empirical_cases": 0, "prospective_predictions": 0}) == "EMPIRICAL_EVIDENCE"


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


def test_activity_identity_has_no_generated_suffixes():
    identity = activity_identity({"verified_empirical_cases": 0, "prospective_predictions": 0, "blocked_tracks": ["EMPIRICAL", "PROSPECTIVE", "TIMING", "CLASSICAL_KNOWLEDGE"]})
    assert identity == {"activity_id": "CALCULATION_VALIDATION", "track": "CALCULATION_VALIDATION", "activity_type": "VALIDATION", "title": "Calculation validation"}


def test_validation_only_completion_is_distinct_from_commit_failure():
    activity = {"activity_id": "RAG_VALIDATION"}
    assert classify_material_progress(activity=activity, starting_head="a", ending_head="a", validation_gain=True) == "VALIDATION_GAIN"
    assert completion_state(exit_code=0, reconciliation={"authoritative_uncommitted": [], "invalid_authoritative": [], "unexpected": []}) == "ACTIVITY_COMPLETED_NO_REPO_CHANGE"


def test_output_classification_preserves_runtime_and_authority_boundaries():
    assert classify_output("docs/current-state/pred-004/06_SOURCE_PROVENANCE_AND_CALIBRATION.md") == "AUTHORITATIVE_ACTIVITY_OUTPUT"
    assert classify_output(".veda-loop/iterations.jsonl") == "RUNTIME"
    assert classify_output("notes/user-work.md") == "UNRELATED"


def test_all_blocked_tracks_are_a_controlled_stop_condition():
    state = {"verified_empirical_cases": 0, "prospective_predictions": 0, "blocked_tracks": ["EMPIRICAL", "PROSPECTIVE", "TIMING", "CLASSICAL_KNOWLEDGE", "CALCULATION_VALIDATION", "CALIBRATION_ML", "RAG", "MUHURTA", "PRASHNA", "GOVERNANCE", "CLASSICAL_SOURCE_EXPANSION", "TIMING_VALIDATION", "METHOD_COMPARISON", "TAJIKA_FOUNDATION", "ASHTAKAVARGA_VALIDATION", "SHADBALA_VALIDATION", "MUHURTA_SOURCE_EXPANSION", "EMPIRICAL_INPUT_PREPARATION", "PROSPECTIVE_SUBJECT_DISCOVERY"]}
    with pytest.raises(NoAvailableTrackError):
        select_track(state)
