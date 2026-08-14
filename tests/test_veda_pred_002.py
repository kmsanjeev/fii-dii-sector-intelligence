from __future__ import annotations

from engines.ai.orchestration import AgentOrchestrator
from engines.ai.orchestration.persistence import DurablePredictionRegistry
from engines.ai.orchestration.prediction import OutcomeRecord, PredictionRegistry
from engines.ai.orchestration.validation import HistoricalPredictionHarness, audit_leakage, combination_recommendation, human_evaluation_rubric, make_prospective


def _prediction():
    return PredictionRegistry().create(
        request_id="REQ-PRED-002",
        subject_id="CASE-PRED-002",
        domain="CAREER",
        prediction_type="EXPERIMENTAL_PREDICTION",
        prediction_direction="TRANSITION",
        prediction_description="A job change is hypothesized in the defined window.",
        window_start="2027-01-01",
        window_end="2027-06-30",
        event_definition="JOB_CHANGE",
        confidence_state="MODERATE",
    )


def test_leakage_audit_rejects_post_outcome_material() -> None:
    record = _prediction()
    audit = audit_leakage(
        prediction=record,
        prediction_cutoff="2026-12-01T00:00:00Z",
        retrieved_documents=[{"doc_id": "future", "published_at": "2027-02-01T00:00:00Z"}],
        case_metadata={"future_outcome": "JOB_CHANGE"},
    )
    assert audit.status == "LEAKAGE_INVALID"
    assert {item.field for item in audit.findings} == {"retrieved_documents", "case_metadata"}


def test_historical_harness_locks_before_revealing_outcome(tmp_path) -> None:
    store = DurablePredictionRegistry(tmp_path / "pred002.sqlite3")
    record = _prediction()
    outcome = OutcomeRecord("OUT-PRED-002", record.subject_id, record.domain, "JOB_CHANGE", "2027-03-01", event_direction="TRANSITION", verification_quality="DOCUMENT_VERIFIED")
    result = HistoricalPredictionHarness(store).run(record, prediction_cutoff="2026-12-01T00:00:00Z", outcome=outcome)
    assert result["comparison_state"] == "CORRECT"
    assert store.get(record.prediction_id).lock_state == "RESOLVED"


def test_contaminated_historical_case_is_not_scored(tmp_path) -> None:
    store = DurablePredictionRegistry(tmp_path / "invalid.sqlite3")
    record = _prediction()
    outcome = OutcomeRecord("OUT-INVALID", record.subject_id, record.domain, "JOB_CHANGE", "2027-03-01", event_direction="TRANSITION")
    result = HistoricalPredictionHarness(store).run(record, prediction_cutoff="2026-12-01T00:00:00Z", outcome=outcome, case_metadata={"outcome_known_before_prediction": True})
    assert result["status"] == "LEAKAGE_INVALID"
    assert store.counts()["evaluations"] == 0


def test_prospective_record_has_no_fake_outcome_and_combination_is_gated() -> None:
    record = make_prospective(_prediction())
    assert record.case_class == "PROSPECTIVE_CASE"
    assert record.actual_outcome is None
    assert combination_recommendation("D1+DASHA", sample_size=2, hits=2).recommendation == "INSUFFICIENT_SAMPLE"
    assert combination_recommendation("D1+DASHA", sample_size=3, hits=2).recommendation == "CONTEXT_DEPENDENT"


def test_stage_modes_are_explicit() -> None:
    orchestrator = AgentOrchestrator()
    assert orchestrator.shadow_trace("When is career timing likely?", mode="OFF")["mode"] == "OFF"
    assert orchestrator.shadow_trace("When is career timing likely?", mode="SHADOW")["mode"] == "SHADOW"
    assisted = orchestrator.shadow_trace("When is career timing likely?", mode="ASSISTED")
    assert assisted["mode"] == "ASSISTED"
    assert assisted["assisted_evidence"]["route"] == "TIMING"


def test_human_rubric_is_empty_until_human_feedback() -> None:
    rubric = human_evaluation_rubric()
    assert rubric["ratings_captured"] == 0
    assert rubric["human_validated"] is False
