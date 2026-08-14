"""Leakage-safe validation and pilot utilities for VEDA-PRED-002.

These utilities operate on PRED-001 records and deliberately keep synthetic
fixtures separate from empirical aggregates.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .persistence import DurablePredictionRegistry
from .prediction import OutcomeRecord, PredictionRecord, PredictionRegistry


DATASET_CLASSES = ("REAL_VERIFIED", "REAL_USER_REPORTED", "HISTORICAL_DOCUMENTED", "WORKED_CASE", "SYNTHETIC", "TEST_FIXTURE", "UNVERIFIED", "UNUSABLE")
MODES = ("OFF", "SHADOW", "ASSISTED")


@dataclass(frozen=True, slots=True)
class DatasetInventoryItem:
    path: str
    classification: str
    domain: str | None = None
    subjects: int = 0
    time_coverage: str | None = None
    event_coverage: str | None = None
    verification_quality: str = "UNVERIFIED"
    outcome_known_at_prediction: bool | None = None
    leakage_risk: str = "UNKNOWN"


def inventory_paths(root: str | Path, *, classifier: Callable[[Path], str] | None = None) -> list[DatasetInventoryItem]:
    """Inventory files without interpreting them as empirical evidence."""
    base = Path(root)
    if not base.exists():
        return []
    classify = classifier or (lambda path: "TEST_FIXTURE" if "test" in str(path).lower() or "fixture" in str(path).lower() else "UNVERIFIED")
    return [DatasetInventoryItem(str(path), classify(path)) for path in sorted(path for path in base.rglob("*") if path.is_file())]


@dataclass(frozen=True, slots=True)
class LeakageFinding:
    field: str
    reason: str
    severity: str = "INVALID"


@dataclass(frozen=True, slots=True)
class LeakageAudit:
    valid: bool
    status: str
    findings: tuple[LeakageFinding, ...] = ()


def _instant(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def audit_leakage(*, prediction: dict[str, Any] | PredictionRecord, prediction_cutoff: str, knowledge_cutoff: str | None = None, outcome_cutoff: str | None = None, data_available_at_prediction: str | None = None, retrieved_documents: list[dict[str, Any]] | None = None, case_metadata: dict[str, Any] | None = None) -> LeakageAudit:
    """Reject future outcome/research data before a historical prediction runs."""
    payload = prediction.to_dict() if isinstance(prediction, PredictionRecord) else dict(prediction)
    cutoff = _instant(prediction_cutoff)
    findings: list[LeakageFinding] = []
    if cutoff is None:
        findings.append(LeakageFinding("prediction_cutoff", "invalid cutoff"))
    for field in ("actual_outcome", "outcome_timestamp", "comparison_state"):
        if payload.get(field):
            findings.append(LeakageFinding(field, "post-outcome field present before prediction"))
    for field in ("knowledge_cutoff", "data_cutoff"):
        value = _instant(str(payload.get(field) or ""))
        if cutoff and value and value > cutoff:
            findings.append(LeakageFinding(field, "cutoff is after prediction cutoff"))
    available = _instant(data_available_at_prediction)
    if cutoff and available and available > cutoff:
        findings.append(LeakageFinding("data_available_at_prediction", "data became available after prediction cutoff"))
    for document in retrieved_documents or []:
        published = _instant(str(document.get("published_at") or document.get("created_at") or ""))
        if cutoff and published and published > cutoff:
            findings.append(LeakageFinding("retrieved_documents", "future document retrieved"))
        if document.get("outcome") or document.get("actual_outcome"):
            findings.append(LeakageFinding("retrieved_documents", "outcome-bearing document retrieved"))
    metadata = case_metadata or {}
    if metadata.get("future_outcome") or metadata.get("outcome_known_before_prediction"):
        findings.append(LeakageFinding("case_metadata", "future outcome exposed in case metadata"))
    if outcome_cutoff and cutoff and (_instant(outcome_cutoff) or cutoff) < cutoff:
        findings.append(LeakageFinding("outcome_cutoff", "outcome cutoff precedes prediction cutoff unexpectedly", "WARNING"))
    return LeakageAudit(not findings, "VALID" if not findings else "LEAKAGE_INVALID", tuple(findings))


class HistoricalPredictionHarness:
    """Run a case with a strict pre-outcome audit and then reveal its outcome."""

    def __init__(self, store: DurablePredictionRegistry) -> None:
        self.store = store

    def run(self, record: PredictionRecord, *, prediction_cutoff: str, outcome: OutcomeRecord, knowledge_cutoff: str | None = None, retrieved_documents: list[dict[str, Any]] | None = None, case_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        audit = audit_leakage(prediction=record, prediction_cutoff=prediction_cutoff, knowledge_cutoff=knowledge_cutoff, retrieved_documents=retrieved_documents, case_metadata=case_metadata)
        self.store.record_audit_event("HISTORICAL_LEAKAGE_AUDIT", {"prediction_id": record.prediction_id, "audit": asdict(audit)}, event_id=f"leakage:{record.prediction_id}")
        if not audit.valid:
            return {"status": "LEAKAGE_INVALID", "audit": asdict(audit), "prediction_id": record.prediction_id}
        record.prediction_cutoff = prediction_cutoff
        record.knowledge_cutoff = knowledge_cutoff or prediction_cutoff
        record.data_cutoff = prediction_cutoff
        record.case_class = "HISTORICAL_CASE"
        self.store.create(record, lock=True)
        result = self.store.record_outcome(record.prediction_id, outcome)
        result["audit"] = asdict(audit)
        return result


def make_prospective(record: PredictionRecord) -> PredictionRecord:
    """Mark a locked record as prospective without inventing an outcome."""
    record.case_class = "PROSPECTIVE_CASE"
    record.actual_outcome = None
    record.outcome_timestamp = None
    return record


@dataclass(frozen=True, slots=True)
class CombinationRecommendation:
    combination: str
    sample_size: int
    recommendation: str
    version: str = "PRED-002-1"


def combination_recommendation(combination: str, *, sample_size: int, hits: int, minimum_recurrence: int = 3) -> CombinationRecommendation:
    if sample_size < minimum_recurrence:
        state = "INSUFFICIENT_SAMPLE"
    elif hits == sample_size:
        state = "RETAIN"
    elif hits * 2 >= sample_size:
        state = "CONTEXT_DEPENDENT"
    else:
        state = "DECREASE_RELATIVE_IMPORTANCE"
    return CombinationRecommendation(combination, sample_size, state)


HUMAN_RATING_DIMENSIONS = ("PRECISION", "RELEVANCE", "DEPTH", "CHART_SPECIFICITY", "TIMING_USEFULNESS", "NON_REPETITION", "INSIGHT", "CONFIDENCE_QUALITY", "OVERALL_USEFULNESS")


def human_evaluation_rubric() -> dict[str, Any]:
    return {"dimensions": HUMAN_RATING_DIMENSIONS, "scale": "1-5", "ratings_captured": 0, "human_validated": False}


__all__ = ["DATASET_CLASSES", "MODES", "DatasetInventoryItem", "LeakageAudit", "LeakageFinding", "HistoricalPredictionHarness", "audit_leakage", "make_prospective", "CombinationRecommendation", "combination_recommendation", "human_evaluation_rubric"]
