"""Universal prospective prediction and outcome-evaluation contract."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    outcome_id: str
    subject_id: str
    domain: str
    event_type: str
    event_start: str | None = None
    event_end: str | None = None
    event_direction: str | None = None
    evidence_source: str = "UNVERIFIED"
    verification_quality: str = "UNVERIFIED"
    notes: str = ""


@dataclass(slots=True)
class PredictionRecord:
    prediction_id: str
    request_id: str
    subject_id: str
    domain: str
    prediction_created_at: str
    prediction_type: str
    prediction_direction: str
    prediction_description: str
    window_start: str
    window_end: str
    event_definition: str
    prediction_state: str
    confidence_state: str
    deterministic_facts: list[dict[str, Any]] = field(default_factory=list)
    classical_evidence: list[dict[str, Any]] = field(default_factory=list)
    expert_reasoning_evidence: list[dict[str, Any]] = field(default_factory=list)
    empirical_evidence: list[dict[str, Any]] = field(default_factory=list)
    ml_evidence: list[dict[str, Any]] = field(default_factory=list)
    opposing_evidence: list[dict[str, Any]] = field(default_factory=list)
    cancelling_evidence: list[dict[str, Any]] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    method_version: str = "STD-002-EXPERIMENTAL-1"
    rule_versions: list[str] = field(default_factory=list)
    knowledge_versions: list[str] = field(default_factory=list)
    model_version: str | None = None
    agent_workflow_version: str = "STD-002-1"
    actual_outcome: dict[str, Any] | None = None
    outcome_timestamp: str | None = None
    comparison_state: str | None = None
    timing_error: int | None = None
    direction_correct: bool | None = None
    confidence_calibration_result: str | None = None
    _outcome_locked: bool = field(default=False, repr=False)

    def snapshot(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("_outcome_locked", None)
        return copy.deepcopy(value)

    def record_outcome(self, outcome: OutcomeRecord, *, comparison: dict[str, Any] | None = None) -> None:
        if self._outcome_locked:
            raise RuntimeError("prediction outcome is immutable once recorded")
        self.actual_outcome = asdict(outcome)
        self.outcome_timestamp = utc_now()
        result = comparison or compare_prediction_outcome(self, outcome)
        self.comparison_state = result["comparison_state"]
        self.timing_error = result.get("timing_error")
        self.direction_correct = result.get("direction_correct")
        self._outcome_locked = True

    def to_dict(self) -> dict[str, Any]:
        value = self.snapshot()
        value["outcome_locked"] = self._outcome_locked
        return value


def compare_prediction_outcome(prediction: PredictionRecord, outcome: OutcomeRecord) -> dict[str, Any]:
    direction_correct = (
        prediction.prediction_direction == outcome.event_direction
        if prediction.prediction_direction and outcome.event_direction
        else None
    )
    event_match = prediction.event_definition.lower() in outcome.event_type.lower() or outcome.event_type.lower() in prediction.event_definition.lower()
    return {
        "comparison_state": "MATCH" if event_match and direction_correct is not False else "PARTIAL" if event_match or direction_correct else "MISMATCH",
        "event_correct": event_match,
        "direction_correct": direction_correct,
        "timing_error": None,
    }


class PredictionRegistry:
    def __init__(self) -> None:
        self._records: dict[str, PredictionRecord] = {}

    def create(self, *, request_id: str, subject_id: str, domain: str, prediction_type: str, prediction_direction: str, prediction_description: str, window_start: str, window_end: str, event_definition: str, confidence_state: str, **kwargs: Any) -> PredictionRecord:
        seed = "|".join((request_id, subject_id, domain, prediction_description, window_start, window_end))
        prediction_id = f"PRED-{hashlib.sha256(seed.encode()).hexdigest()[:16]}"
        record = PredictionRecord(prediction_id=prediction_id, request_id=request_id, subject_id=subject_id, domain=domain, prediction_created_at=utc_now(), prediction_type=prediction_type, prediction_direction=prediction_direction, prediction_description=prediction_description, window_start=window_start, window_end=window_end, event_definition=event_definition, prediction_state=kwargs.pop("prediction_state", "EXPERIMENTAL_PREDICTION"), confidence_state=confidence_state, **kwargs)
        self._records[prediction_id] = record
        return record

    def get(self, prediction_id: str) -> PredictionRecord | None:
        return self._records.get(prediction_id)

    def record_outcome(self, prediction_id: str, outcome: OutcomeRecord) -> dict[str, Any]:
        record = self._records[prediction_id]
        record.record_outcome(outcome)
        return record.to_dict()

    def evaluate(self, *, domain: str | None = None) -> dict[str, Any]:
        records = [item for item in self._records.values() if (domain is None or item.domain == domain) and item.actual_outcome]
        if not records:
            return {"sample_size": 0, "state": "INSUFFICIENT_SAMPLE", "direction_accuracy": None, "event_accuracy": None}
        return {"sample_size": len(records), "state": "CALIBRATION_ACTIVE", "direction_accuracy": round(sum(item.direction_correct is True for item in records) / len(records), 3), "event_accuracy": round(sum(item.comparison_state == "MATCH" for item in records) / len(records), 3)}

    def all(self) -> list[PredictionRecord]:
        return list(self._records.values())


__all__ = ["OutcomeRecord", "PredictionRecord", "PredictionRegistry", "compare_prediction_outcome"]
