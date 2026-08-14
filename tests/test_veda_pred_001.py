from __future__ import annotations

from engines.ai.orchestration.persistence import DurablePredictionRegistry, score_prediction
from engines.ai.orchestration.prediction import OutcomeRecord, PredictionRegistry
from engines.ai.chatbot.chat_engine import ChatEngine
from engines.ai.orchestration.persistence import EVENT_TYPES, CONFIDENCE_BANDS, false_negative_status
from engines.ai.orchestration.response_benchmark import compare_metrics, default_cases, evaluate_response
from engines.ai.orchestration import DocumentCaseIngestionRunner, WeightProfile, decide_research_escalation


def _record() -> object:
    return PredictionRegistry().create(
        request_id="REQ-PRED-1",
        subject_id="SUBJECT-1",
        domain="CAREER",
        prediction_type="EXPERIMENTAL_PREDICTION",
        prediction_direction="TRANSITION",
        prediction_description="A meaningful career transition is hypothesized.",
        window_start="2027-01-01",
        window_end="2027-06-30",
        event_definition="JOB_CHANGE",
        confidence_state="MODERATE",
        window_granularity="BROAD_WINDOW",
    )


def test_durable_prediction_lock_outcome_evaluation_and_rebuild(tmp_path) -> None:
    store = DurablePredictionRegistry(tmp_path / "predictions.sqlite3")
    prediction = _record()
    stored = store.create(prediction)
    assert stored.lock_state == "LOCKED"
    assert store.create(prediction).prediction_id == prediction.prediction_id
    outcome = OutcomeRecord("OUT-1", "SUBJECT-1", "CAREER", "JOB_CHANGE", "2027-03-15", event_direction="TRANSITION", verification_quality="USER_REPORTED")
    score = store.record_outcome(prediction.prediction_id, outcome)
    assert score["comparison_state"] == "CORRECT"
    assert score["timing_hit"] is True
    assert store.counts() == {"predictions": 1, "outcomes": 1, "evaluations": 1}
    assert store.rebuild_performance()["domains"] == 1


def test_timing_error_and_false_positive_scoring() -> None:
    prediction = _record()
    late = OutcomeRecord("OUT-2", "SUBJECT-1", "CAREER", "JOB_CHANGE", "2027-08-01", event_direction="TRANSITION")
    score = score_prediction(prediction, late)
    assert score["timing_hit"] is False
    assert score["days_late"] == 32
    assert false_negative_status(observation_coverage="PARTIAL") == "INSUFFICIENT_OBSERVATION_COVERAGE"
    assert false_negative_status(observation_coverage="COMPLETE") == "MEASURABLE"


def test_supersession_and_false_positive_are_explicit(tmp_path) -> None:
    store = DurablePredictionRegistry(tmp_path / "supersede.sqlite3")
    prediction = _record()
    store.create(prediction)
    replacement = _record()
    replacement.request_id = "REQ-PRED-2"
    replacement.prediction_description = "Updated hypothesis with preserved history."
    replacement = store.supersede(prediction.prediction_id, replacement)
    assert replacement.supersedes_prediction_id == prediction.prediction_id
    result = store.resolve_no_event(replacement.prediction_id)
    assert result["comparison_state"] == "FALSE_POSITIVE"


def test_insufficient_sample_is_explicit(tmp_path) -> None:
    store = DurablePredictionRegistry(tmp_path / "empty.sqlite3")
    assert store.counts() == {"predictions": 0, "outcomes": 0, "evaluations": 0}
    assert store.confidence_calibration()["state"] == "INSUFFICIENT_SAMPLE"


def test_actual_chat_path_records_stage_a_orchestration_trace(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    engine = ChatEngine()
    monkeypatch.setattr(engine, "_get_rag_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(engine, "_get_external_research_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(engine, "_active_providers", lambda: [{"name": "OpenAI", "env_var": "OPENAI_API_KEY", "base_url": "https://api.openai.com/v1", "model": "test", "extra_headers": {}}])
    monkeypatch.setattr(engine, "_get_client", lambda provider: object())
    monkeypatch.setattr(engine, "_run_turn", lambda *args, **kwargs: {"status": "ok", "reply": "A bounded response."})
    assert engine.chat("When is career timing likely?") == "A bounded response."
    assert engine.last_orchestration["intent_type"] == "TIMING"
    assert engine.last_orchestration["response_path_unchanged"] is True


def test_event_taxonomy_confidence_bands_and_response_benchmark() -> None:
    assert "JOB_CHANGE" in EVENT_TYPES["CAREER"]
    assert CONFIDENCE_BANDS == ("VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH")
    cases = default_cases()
    before = [evaluate_response(case, "Various factors may matter.") for case in cases]
    after = [evaluate_response(case, f"{case.domain} outlook: chart and Dasha evidence support a likely window.", evidence=[{"doc_id": case.case_id, "trust_zone": "RESEARCH_CANDIDATE"}]) for case in cases]
    report = compare_metrics(before, after)
    assert report["case_count"] == 9
    assert report["human_validated"] is False
    profile = WeightProfile("WP-1", "1", "CAREER", evidence_basis=("resolved_cases",), sample_size=0)
    assert profile.state == "EXPERIMENTAL"


def test_research_escalation_is_explicit_and_document_case_runner_reuses_learning(tmp_path) -> None:
    decision = decide_research_escalation(explicit_request=False, retrieved_count=0)
    assert decision.required is True
    document = tmp_path / "case.md"
    document.write_text("# Worked Case\n\nA chart and a timing outcome.", encoding="utf-8")
    ingested = DocumentCaseIngestionRunner().ingest(document, domain="CAREER", reasoning_sequence=["Dasha", "Transit"], author="Case Author", outcome="JOB_CHANGE")
    assert ingested.claims
    assert ingested.expert_patterns[0].trust_zone == "RESEARCH_CANDIDATE"
    assert ingested.empirical_patterns[0].sample_size == 1
