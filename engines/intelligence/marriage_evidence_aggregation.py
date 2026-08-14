"""P024 marriage evidence aggregation and conflict handling.

The aggregator preserves structural evidence, explicit conflicts, cancellation
signals, and research-only / shadow-only distinctions without collapsing the
result into crude numeric scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"


@dataclass(slots=True)
class EvidenceRecord:
    evidence_id: str
    source_layer: str
    evidence_type: str
    direction: EvidenceDirection
    claim: str
    rule_id: str | None = None
    rule_source: str | None = None
    basis: dict[str, Any] = field(default_factory=dict)
    confidence: ConfidenceBand = ConfidenceBand.MODERATE
    validation_state: str = "RESEARCH_REQUIRED"
    provisional: bool = True
    notes: str = ""
    source_id: str | None = None
    passage_id: str | None = None
    source_class: str | None = None
    source_family: str | None = None
    retrieval_status: str = "REFERENCE_NOT_VERIFIED"
    citation_status: str = "REFERENCE_NOT_VERIFIED"
    method_variant: str | None = None


@dataclass(slots=True)
class MarriageEvidenceAggregator:
    """P024 marriage evidence aggregator.

    The model keeps supportive, opposing, conditional, cancelling, research,
    and blocked signals separate so the synthesis layer can explain nuance.
    """

    evidence_records: list[EvidenceRecord] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)

    def add_evidence(
        self,
        *,
        source_layer: str,
        evidence_type: str,
        direction: EvidenceDirection,
        claim: str,
        rule_id: str | None = None,
        rule_source: str | None = None,
        basis: dict[str, Any] | None = None,
        confidence: ConfidenceBand = ConfidenceBand.MODERATE,
        validation_state: str = "RESEARCH_REQUIRED",
        provisional: bool = True,
        notes: str = "",
        source_id: str | None = None,
        passage_id: str | None = None,
        source_class: str | None = None,
        source_family: str | None = None,
        retrieval_status: str = "REFERENCE_NOT_VERIFIED",
        citation_status: str = "REFERENCE_NOT_VERIFIED",
        method_variant: str | None = None,
    ) -> EvidenceRecord:
        evidence_id = f"VEDA-P024-EVID-{len(self.evidence_records) + 1:06d}"
        record = EvidenceRecord(
            evidence_id=evidence_id,
            source_layer=source_layer,
            evidence_type=evidence_type,
            direction=direction,
            claim=claim,
            rule_id=rule_id,
            rule_source=rule_source,
            basis=basis or {},
            confidence=confidence,
            validation_state=validation_state,
            provisional=provisional,
            notes=notes,
            source_id=source_id,
            passage_id=passage_id,
            source_class=source_class,
            source_family=source_family,
            retrieval_status=retrieval_status,
            citation_status=citation_status,
            method_variant=method_variant,
        )
        self.evidence_records.append(record)
        return record

    def detect_conflicts(self) -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []
        for left_index, left in enumerate(self.evidence_records):
            for right in self.evidence_records[left_index + 1 :]:
                if {left.direction, right.direction} & {EvidenceDirection.BLOCKED_DEPENDENCY}:
                    conflicts.append(
                        {
                            "conflict_id": f"VEDA-P024-CNF-{len(conflicts) + 1:06d}",
                            "left_evidence_id": left.evidence_id,
                            "right_evidence_id": right.evidence_id,
                            "conflict_type": "BLOCKED_DEPENDENCY",
                            "status": "BLOCKED",
                            "resolution_required": True,
                        }
                    )
                    continue
                if (
                    left.direction == EvidenceDirection.SUPPORTING
                    and right.direction in {EvidenceDirection.OPPOSING, EvidenceDirection.CONFLICTING}
                ) or (
                    right.direction == EvidenceDirection.SUPPORTING
                    and left.direction in {EvidenceDirection.OPPOSING, EvidenceDirection.CONFLICTING}
                ):
                    conflicts.append(
                        {
                            "conflict_id": f"VEDA-P024-CNF-{len(conflicts) + 1:06d}",
                            "left_evidence_id": left.evidence_id,
                            "right_evidence_id": right.evidence_id,
                            "conflict_type": "DIRECTIONAL_OPPOSITION",
                            "status": "UNRESOLVED",
                            "resolution_required": True,
                        }
                    )
        self.conflicts = conflicts
        return conflicts

    def _bucket(self, *directions: EvidenceDirection) -> list[EvidenceRecord]:
        wanted = set(directions)
        return [record for record in self.evidence_records if record.direction in wanted]

    def _confidence_band(self, supporting: list[EvidenceRecord], opposing: list[EvidenceRecord], cancelling: list[EvidenceRecord]) -> ConfidenceBand:
        if not self.evidence_records:
            return ConfidenceBand.RESEARCH_REQUIRED
        if any(record.direction == EvidenceDirection.BLOCKED_DEPENDENCY for record in self.evidence_records):
            return ConfidenceBand.RESEARCH_REQUIRED
        if cancelling:
            return ConfidenceBand.MODERATE if supporting else ConfidenceBand.LOW
        if supporting and not opposing:
            if any(record.confidence == ConfidenceBand.HIGH for record in supporting):
                return ConfidenceBand.HIGH
            return ConfidenceBand.MODERATE
        if supporting and opposing:
            return ConfidenceBand.MODERATE
        if opposing:
            return ConfidenceBand.LOW
        return ConfidenceBand.RESEARCH_REQUIRED

    def _interpretation_state(self, supporting: list[EvidenceRecord], opposing: list[EvidenceRecord], conditional: list[EvidenceRecord], cancelling: list[EvidenceRecord], research: list[EvidenceRecord], blocked: list[EvidenceRecord]) -> str:
        if blocked:
            return "BLOCKED_DEPENDENCY"
        if cancelling and supporting and not opposing:
            return "SUPPORTED_WITH_CANCELLATION"
        if supporting and opposing:
            return "CONFLICTED"
        if supporting and conditional:
            return "SUPPORTED_WITH_CONDITIONS"
        if supporting:
            return "SUPPORTED"
        if opposing:
            return "OPPOSED"
        if cancelling:
            return "CANCELLATION_ONLY"
        if research:
            return "RESEARCH_ONLY"
        if conditional:
            return "CONDITIONAL_ONLY"
        return "INSUFFICIENT_EVIDENCE"

    def synthesize_narrative(self) -> dict[str, Any]:
        supporting = self._bucket(EvidenceDirection.SUPPORTING)
        opposing = self._bucket(EvidenceDirection.OPPOSING)
        conditional = self._bucket(EvidenceDirection.CONDITIONAL)
        cancelling = self._bucket(EvidenceDirection.CANCELLING)
        conflicting = self._bucket(EvidenceDirection.CONFLICTING)
        research = self._bucket(EvidenceDirection.RESEARCH_ONLY, EvidenceDirection.EXPERIMENTAL)
        blocked = self._bucket(EvidenceDirection.BLOCKED_DEPENDENCY)
        confidence = self._confidence_band(supporting, opposing, cancelling)
        interpretation = self._interpretation_state(supporting, opposing, conditional, cancelling, research, blocked)

        return {
            "supporting_count": len(supporting),
            "opposing_count": len(opposing),
            "conditional_count": len(conditional),
            "cancelling_count": len(cancelling),
            "conflicting_count": len(conflicting),
            "research_only_count": len(research),
            "blocked_dependency_count": len(blocked),
            "conflict_count": len(self.conflicts),
            "overall_confidence": confidence.value,
            "overall_state": interpretation,
            "evidence_preserved": bool(self.evidence_records),
            "conflicts_acknowledged": bool(self.conflicts),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_records": [
                {
                    "evidence_id": record.evidence_id,
                    "source_layer": record.source_layer,
                    "evidence_type": record.evidence_type,
                    "direction": record.direction.value,
                    "claim": record.claim,
                    "rule_id": record.rule_id,
                    "rule_source": record.rule_source,
                    "basis": record.basis,
                    "confidence": record.confidence.value,
                    "validation_state": record.validation_state,
                    "provisional": record.provisional,
                    "notes": record.notes,
                    "source_id": record.source_id,
                    "passage_id": record.passage_id,
                    "source_class": record.source_class,
                    "source_family": record.source_family,
                    "retrieval_status": record.retrieval_status,
                    "citation_status": record.citation_status,
                    "method_variant": record.method_variant,
                }
                for record in self.evidence_records
            ],
            "conflicts": list(self.conflicts),
            "synthesis": self.synthesize_narrative(),
        }


__all__ = [
    "ConfidenceBand",
    "EvidenceDirection",
    "EvidenceRecord",
    "MarriageEvidenceAggregator",
]
