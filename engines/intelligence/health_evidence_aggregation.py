"""P026 P020-compatible directional health evidence aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class EvidenceDirection(str, Enum):
    SUPPORTING = "SUPPORTING"
    OPPOSING = "OPPOSING"
    CONDITIONAL = "CONDITIONAL"
    CANCELLING = "CANCELLING"
    CONFLICTING = "CONFLICTING"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    EXPERIMENTAL = "EXPERIMENTAL"
    BLOCKED_DEPENDENCY = "BLOCKED_DEPENDENCY"


class ConfidenceBand(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(slots=True)
class EvidenceRecord:
    evidence_id: str
    source_layer: str
    evidence_type: str
    direction: EvidenceDirection
    claim: str
    basis: dict[str, Any] = field(default_factory=dict)
    confidence: ConfidenceBand = ConfidenceBand.RESEARCH_REQUIRED
    validation_state: str = "RESEARCH_REQUIRED"
    provisional: bool = True
    notes: str = ""
    source_id: str | None = None
    passage_id: str | None = None
    method_variant: str | None = None


class HealthEvidenceAggregator:
    def __init__(self) -> None:
        self.evidence_records: list[EvidenceRecord] = []
        self.conflicts: list[dict[str, Any]] = []

    def add_evidence(self, *, source_layer: str, evidence_type: str, direction: EvidenceDirection, claim: str, basis: dict[str, Any] | None = None, confidence: ConfidenceBand = ConfidenceBand.RESEARCH_REQUIRED, validation_state: str = "RESEARCH_REQUIRED", provisional: bool = True, notes: str = "", source_id: str | None = None, passage_id: str | None = None, method_variant: str | None = None) -> EvidenceRecord:
        record = EvidenceRecord(f"P026-EVID-{len(self.evidence_records) + 1:06d}", source_layer, evidence_type, direction, claim, basis or {}, confidence, validation_state, provisional, notes, source_id, passage_id, method_variant)
        self.evidence_records.append(record)
        return record

    def detect_conflicts(self) -> list[dict[str, Any]]:
        directions = {row.direction for row in self.evidence_records}
        self.conflicts = []
        if EvidenceDirection.SUPPORTING in directions and EvidenceDirection.OPPOSING in directions:
            self.conflicts.append({"type": "SUPPORT_OPPOSITION", "status": "PRESERVED", "resolution": "QUALIFIED_SYNTHESIS"})
        if EvidenceDirection.CONDITIONAL in directions and EvidenceDirection.CANCELLING in directions:
            self.conflicts.append({"type": "CONDITIONAL_MITIGATION", "status": "PRESERVED", "resolution": "CONTEXT_REQUIRED"})
        return self.conflicts

    def synthesize_narrative(self) -> dict[str, Any]:
        self.detect_conflicts()
        buckets = {direction: [row for row in self.evidence_records if row.direction == direction] for direction in EvidenceDirection}
        if buckets[EvidenceDirection.BLOCKED_DEPENDENCY]:
            state = "BLOCKED_DEPENDENCY"
        elif buckets[EvidenceDirection.SUPPORTING] and buckets[EvidenceDirection.OPPOSING]:
            state = "CONFLICTED"
        elif buckets[EvidenceDirection.SUPPORTING] and buckets[EvidenceDirection.CANCELLING]:
            state = "SUPPORTED_WITH_MITIGATION"
        elif buckets[EvidenceDirection.SUPPORTING]:
            state = "SUPPORTED"
        elif buckets[EvidenceDirection.OPPOSING]:
            state = "CHALLENGE"
        elif buckets[EvidenceDirection.CONDITIONAL]:
            state = "CONDITIONAL"
        else:
            state = "INSUFFICIENT_EVIDENCE"
        confidence = ConfidenceBand.HIGH if buckets[EvidenceDirection.SUPPORTING] and not buckets[EvidenceDirection.OPPOSING] else ConfidenceBand.MODERATE if self.evidence_records else ConfidenceBand.INSUFFICIENT
        return {"overall_state": state, "overall_confidence": confidence.value, **{f"{key.value.lower()}_count": len(value) for key, value in buckets.items()}, "conflict_count": len(self.conflicts), "evidence_preserved": bool(self.evidence_records), "conflicts_acknowledged": bool(self.conflicts)}

    def to_dict(self) -> dict[str, Any]:
        return {"evidence_records": [{**asdict(row), "direction": row.direction.value, "confidence": row.confidence.value} for row in self.evidence_records], "conflicts": self.conflicts, "synthesis": self.synthesize_narrative()}


__all__ = ["ConfidenceBand", "EvidenceDirection", "EvidenceRecord", "HealthEvidenceAggregator"]
