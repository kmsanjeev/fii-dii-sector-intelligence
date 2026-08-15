import json

import pytest

from scripts.veda_loop import NoAvailableTrackError, activity_identity, candidate_decisions, classify_activity_result, classify_failure, classify_material_progress, classify_output, classify_stop_reason, completion_state, compose_prompt, partial_completion, relevant_input_fingerprint, resume_from_transient_stop, select_next_priority, select_track


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
    assert classify_output("data/veda/research/astrology/sources/VEDA-SRC-000011.json") == "AUTHORITATIVE_ACTIVITY_OUTPUT"
    assert classify_output("data/veda/validation/foundation/p018_strength/ashtakavarga_boundary_fixture.json") == "AUTHORITATIVE_ACTIVITY_OUTPUT"
    assert classify_output(".veda-loop/iterations.jsonl") == "RUNTIME"
    assert classify_output("notes/user-work.md") == "UNRELATED"


def test_all_blocked_tracks_are_a_controlled_stop_condition():
    state = {"verified_empirical_cases": 0, "prospective_predictions": 0, "blocked_tracks": ["EMPIRICAL", "PROSPECTIVE", "TIMING", "CLASSICAL_KNOWLEDGE", "CALCULATION_VALIDATION", "CALIBRATION_ML", "RAG", "MUHURTA", "PRASHNA", "GOVERNANCE", "CLASSICAL_SOURCE_EXPANSION", "TIMING_VALIDATION", "METHOD_COMPARISON", "TAJIKA_FOUNDATION", "ASHTAKAVARGA_VALIDATION", "SHADBALA_VALIDATION", "MUHURTA_SOURCE_EXPANSION", "EMPIRICAL_INPUT_PREPARATION", "PROSPECTIVE_SUBJECT_DISCOVERY"]}
    with pytest.raises(NoAvailableTrackError):
        select_track(state)


def _r3_state(**overrides):
    state = {"verified_empirical_cases": 25, "prospective_predictions": 1, "resolved_predictions": 10, "blocked_tracks": ["EMPIRICAL", "PROSPECTIVE", "TIMING", "CLASSICAL_KNOWLEDGE", "CALCULATION_VALIDATION", "CALIBRATION_ML", "RAG", "MUHURTA", "PRASHNA", "GOVERNANCE"], "available_tracks": ["TIMING_VALIDATION", "METHOD_COMPARISON", "TAJIKA_FOUNDATION"], "last_commit": "abc", "activity_history": [], "cooldowns": {}}
    state.update(overrides)
    return state


def test_same_activity_same_input_no_delta_is_suppressed():
    state = _r3_state(activity_history=[{"activity_id": "TIMING_VALIDATION", "track": "TIMING_VALIDATION", "input_fingerprint": relevant_input_fingerprint(_r3_state(), "TIMING_VALIDATION"), "material_progress": "NO_NEW_INFORMATION"}])
    assert select_track(state) == "METHOD_COMPARISON"
    timing = next(item for item in candidate_decisions(state) if item["track"] == "TIMING_VALIDATION")
    assert "SAME_INPUT_NO_PROGRESS" in timing["rejected"]


def test_changed_input_allows_previously_suppressed_activity():
    state = _r3_state(activity_history=[{"activity_id": "TIMING_VALIDATION", "track": "TIMING_VALIDATION", "input_fingerprint": "old", "material_progress": "NO_NEW_INFORMATION"}])
    assert next(item for item in candidate_decisions(state) if item["track"] == "TIMING_VALIDATION")["selected"]


def test_same_input_repeat_is_suppressed_even_after_zero_commit_gain():
    base = _r3_state()
    state = _r3_state(activity_history=[{"activity_id": "METHOD_COMPARISON", "track": "METHOD_COMPARISON", "input_fingerprint": relevant_input_fingerprint(base, "METHOD_COMPARISON"), "material_progress": "MEDIUM_INFORMATION_GAIN"}])
    method = next(item for item in candidate_decisions(state) if item["track"] == "METHOD_COMPARISON")
    assert not method["selected"]
    assert "SAME_INPUT_REPEAT" in method["rejected"]


def test_method_comparison_has_concrete_high_information_question():
    item = next(item for item in candidate_decisions(_r3_state()) if item["track"] == "METHOD_COMPARISON")
    assert item["expected_information_gain"] == "HIGH"
    assert "two legitimate methods" in item["question"]


def test_document_only_output_is_not_material_progress():
    assert classify_activity_result(starting_head="a", ending_head="a", output="# report", activity_outputs=["docs/current-state/rm-002/report.md"], exit_code=0) == "DOCUMENTATION_ONLY"
    assert classify_activity_result(starting_head="a", ending_head="a", output="new validated timing rule", activity_outputs=[], exit_code=0) == "MEDIUM_INFORMATION_GAIN"


def test_output_fingerprint_inputs_are_stable():
    state = _r3_state()
    assert relevant_input_fingerprint(state, "METHOD_COMPARISON") == relevant_input_fingerprint(state, "METHOD_COMPARISON")


def test_low_value_stop_with_novel_next_priority_resumes():
    state = _r3_state(next_priority="TAJIKA_FOUNDATION", stop_reason="LOW_VALUE_REPETITION: prior activity repeated")
    result = resume_from_transient_stop(state, dry_run=True)
    assert result == {"classification": "TRANSIENT_RUN_STOP", "resumed": True, "selected": "TAJIKA_FOUNDATION", "reason": None}


def test_human_and_programme_stops_remain_stopped():
    assert classify_stop_reason("FOUNDER_APPROVAL_REQUIRED") == "HUMAN_BLOCK"
    assert classify_stop_reason("USER_REQUESTED_STOP") == "PROGRAMME_STOP"
    assert not resume_from_transient_stop(_r3_state(next_priority="TAJIKA_FOUNDATION", stop_reason="FOUNDER_APPROVAL_REQUIRED"), dry_run=True)["resumed"]
    assert not resume_from_transient_stop(_r3_state(next_priority="TAJIKA_FOUNDATION", stop_reason="NO_MEANINGFUL_NEXT_ACTIVITY"), dry_run=True)["resumed"]


def test_transient_resume_clears_stop_and_preserves_history(monkeypatch):
    state = _r3_state(next_priority="TAJIKA_FOUNDATION", stop_reason="MAX_LOOPS_REACHED")
    monkeypatch.setattr("scripts.veda_loop.save_state", lambda value: None)
    result = resume_from_transient_stop(state)
    assert result["resumed"]
    assert state["stop_reason"] is None
    assert state["controller_state"] == "READY"
    assert state["programme_status"] == "ACTIVE"
    assert state["stop_history"][0]["classification"] == "TRANSIENT_RUN_STOP"


def test_cooldown_on_one_track_does_not_block_unrelated_priority():
    state = _r3_state(next_priority="TAJIKA_FOUNDATION", cooldowns={"METHOD_COMPARISON": {"input_fingerprint": relevant_input_fingerprint(_r3_state(), "METHOD_COMPARISON")}})
    assert resume_from_transient_stop({**state, "stop_reason": "LOW_VALUE_REPETITION"}, dry_run=True)["selected"] == "TAJIKA_FOUNDATION"
