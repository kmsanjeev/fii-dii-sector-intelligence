from __future__ import annotations

from engines.ai.orchestration.cases import CaseRegistry, assess_quality, normalize_case
from engines.ai.orchestration.persistence import DurablePredictionRegistry
from engines.ai.orchestration.response_benchmark import capture_provider_response, default_cases
from engines.ai.orchestration.validation import audit_leakage


def _case(**overrides):
    payload = {
        "case_id": "CASE-003-1",
        "subject_id": "SUBJECT-003-1",
        "source_id": "SOURCE-003-1",
        "domain": "CAREER",
        "case_class": "HISTORICAL_VERIFIED",
        "birth_data_provenance": "DOCUMENT_VERIFIED",
        "event_provenance": "DOCUMENT_VERIFIED",
        "verification_quality": "DOCUMENT_VERIFIED",
        "prediction_cutoff": "2025-01-01T00:00:00Z",
        "knowledge_cutoff": "2025-01-01T00:00:00Z",
        "leakage_status": "VALID",
        "outcome": {"event_type": "JOB_CHANGE", "event_start": "2025-06-01"},
    }
    payload.update(overrides)
    return normalize_case(payload)


def test_case_quality_and_empirical_eligibility(tmp_path) -> None:
    case = _case()
    assert assess_quality(case) == "HIGH"
    store = CaseRegistry(tmp_path / "cases.sqlite3")
    stored, state = store.add(case)
    assert state == "ADDED"
    assert stored.empirical_eligible is True
    assert len(store.eligible()) == 1


def test_duplicate_case_family_is_not_counted_twice(tmp_path) -> None:
    store = CaseRegistry(tmp_path / "cases.sqlite3")
    first = _case(case_family="FAM-1", independent_source_family="ORIGINAL")
    second = _case(case_id="CASE-003-2", case_family="FAM-1", independent_source_family="ORIGINAL")
    assert store.add(first)[1] == "ADDED"
    assert store.add(second)[1] == "DUPLICATE_CASE_FAMILY"
    assert sum(store.counts().values()) == 1


def test_unverified_fixture_does_not_become_empirical(tmp_path) -> None:
    store = CaseRegistry(tmp_path / "cases.sqlite3")
    fixture = _case(case_id="FIXTURE-1", case_class="FIXTURE_ONLY", quality="UNVERIFIED", leakage_status="UNREVIEWED")
    store.add(fixture)
    assert store.eligible() == []


def test_provider_benchmark_preserves_metadata() -> None:
    case = default_cases()[0]
    captured = capture_provider_response(case, provider="test-provider", model="test-model", prompt_version="PRED003-1", retrieval_mode="ASSISTED", responder=lambda _: "Provider response")
    assert captured.provider == "test-provider"
    assert captured.model == "test-model"
    assert captured.answer == "Provider response"


def test_human_evaluation_is_separate_from_predictions(tmp_path) -> None:
    store = DurablePredictionRegistry(tmp_path / "pred003.sqlite3")
    identifier = store.record_human_evaluation("STD003-GENERAL", {"PRECISION": 4, "RELEVANCE": 5})
    assert identifier
