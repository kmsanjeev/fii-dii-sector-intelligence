"""P023 education evidence aggregation and conflict resolution.

Aggregates education-related evidence from natal, Varga, Dasha, and Transit
facts into structured synthesis-ready evidence records.

Preserves conflicts explicitly rather than suppressing them.
Handles unvalidated strength components conservatively.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from engines.common import config as cfg

ROOT = Path(__file__).resolve().parents[3]


class EvidenceDirection(Enum):
    """Direction of evidence flow."""
    SUPPORTING = "SUPPORTING"
    OPPOSING = "OPPOSING"
    CONDITIONAL = "CONDITIONAL"
    BLOCKED = "BLOCKED"
    NEUTRAL = "NEUTRAL"


class ConfidenceBand(Enum):
    """Qualitative confidence levels (no false percentages)."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"


@dataclass
class EvidenceRecord:
    """Single piece of education evidence."""
    evidence_id: str
    source_layer: str
    evidence_type: str
    direction: EvidenceDirection
    claim: str
    rule_id: Optional[str]
    rule_source: Optional[str]
    basis: dict[str, Any]
    confidence: ConfidenceBand
    validation_state: str
    provisional: bool
    notes: str = ""


@dataclass
class EducationEvidenceAggregator:
    """P023 Education Evidence Aggregator.
    
    Reuses P020 aggregation pattern:
    - Non-suppressive evidence collection
    - Explicit conflict representation
    - Confidence propagation
    - Explainability tracing
    """

    def __init__(self):
        self.evidence_records: list[EvidenceRecord] = []
        self.conflicts: list[dict[str, Any]] = []
        self.dependencies: dict[str, list[str]] = {}

    def add_evidence(
        self,
        source_layer: str,
        evidence_type: str,
        direction: EvidenceDirection,
        claim: str,
        rule_id: Optional[str] = None,
        rule_source: Optional[str] = None,
        basis: dict[str, Any] | None = None,
        confidence: ConfidenceBand = ConfidenceBand.MODERATE,
        validation_state: str = "RESEARCH_REQUIRED",
        provisional: bool = False,
        notes: str = "",
    ) -> None:
        """Add a piece of education evidence."""
        evidence_id = f"{source_layer}_{len(self.evidence_records):03d}"

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
        )
        self.evidence_records.append(record)

    def detect_conflicts(self) -> list[dict[str, Any]]:
        """Detect and record conflicting evidence."""
        conflicts = []

        for i, rec1 in enumerate(self.evidence_records):
            for rec2 in self.evidence_records[i + 1:]:
                # Check if evidence is directionally opposite
                if (
                    rec1.direction == EvidenceDirection.SUPPORTING
                    and rec2.direction == EvidenceDirection.OPPOSING
                ):
                    conflicts.append({
                        "conflict_id": f"CONFLICT_{len(conflicts):03d}",
                        "evidence_1": rec1.evidence_id,
                        "evidence_2": rec2.evidence_id,
                        "claim_1": rec1.claim,
                        "claim_2": rec2.claim,
                        "source_1": rec1.source_layer,
                        "source_2": rec2.source_layer,
                        "status": "UNRESOLVED",
                        "resolution_required": True,
                    })

        self.conflicts = conflicts
        return conflicts

    def synthesize_narrative(self) -> dict[str, Any]:
        """Generate synthesis narrative preserving all evidence."""
        supporting = [r for r in self.evidence_records if r.direction == EvidenceDirection.SUPPORTING]
        opposing = [r for r in self.evidence_records if r.direction == EvidenceDirection.OPPOSING]
        conditional = [r for r in self.evidence_records if r.direction == EvidenceDirection.CONDITIONAL]
        blocked = [r for r in self.evidence_records if r.direction == EvidenceDirection.BLOCKED]

        # Aggregate confidence
        confidence = self._aggregate_confidence(
            supporting, opposing, conditional, blocked
        )

        # Overall interpretation
        interpretation = self._interpret_evidence(
            supporting, opposing, conditional, blocked
        )

        return {
            "supporting_count": len(supporting),
            "opposing_count": len(opposing),
            "conditional_count": len(conditional),
            "blocked_count": len(blocked),
            "unresolved_conflicts": len(self.conflicts),
            "overall_confidence": confidence.value,
            "overall_interpretation": interpretation,
            "evidence_preserved": len(self.evidence_records) > 0,
            "conflicts_acknowledged": len(self.conflicts),
        }

    def _aggregate_confidence(
        self,
        supporting: list[EvidenceRecord],
        opposing: list[EvidenceRecord],
        conditional: list[EvidenceRecord],
        blocked: list[EvidenceRecord],
    ) -> ConfidenceBand:
        """Aggregate confidence from evidence streams."""
        if not self.evidence_records:
            return ConfidenceBand.RESEARCH_REQUIRED

        if blocking := len(blocked):
            if supporting == 0:
                return ConfidenceBand.RESEARCH_REQUIRED
            if opposing > 0:
                return ConfidenceBand.MODERATE

        if len(supporting) > len(opposing):
            # More supporting than opposing
            avg_supporting = sum(
                1 for r in supporting if r.confidence != ConfidenceBand.LOW
            ) / max(1, len(supporting))
            if avg_supporting >= 0.7:
                return ConfidenceBand.HIGH
            elif avg_supporting >= 0.5:
                return ConfidenceBand.MODERATE
            else:
                return ConfidenceBand.LOW

        elif len(opposing) > len(supporting):
            return ConfidenceBand.MODERATE

        else:
            # Mixed or equal
            if conditional:
                return ConfidenceBand.MODERATE
            else:
                return ConfidenceBand.LOW

    def _interpret_evidence(
        self,
        supporting: list[EvidenceRecord],
        opposing: list[EvidenceRecord],
        conditional: list[EvidenceRecord],
        blocked: list[EvidenceRecord],
    ) -> str:
        """Generate interpretation text based on evidence."""
        if not self.evidence_records:
            return "INSUFFICIENT_EVIDENCE"

        if blocked:
            if supporting and not opposing:
                return "SUPPORTED_WITH_BLOCKED_DEPENDENCIES"
            elif supporting and opposing:
                return "CONFLICTED_WITH_BLOCKED_DEPENDENCIES"
            else:
                return "BLOCKED"

        if supporting and not opposing:
            if conditional:
                return "SUPPORTED_WITH_CONDITIONS"
            else:
                return "SUPPORTED"

        elif opposing and not supporting:
            return "OPPOSED"

        elif supporting and opposing:
            return "CONFLICTED"

        elif conditional:
            return "CONDITIONAL_ONLY"

        else:
            return "INCONCLUSIVE"

    def to_dict(self) -> dict[str, Any]:
        """Convert aggregator to dictionary."""
        return {
            "evidence_records": [
                {
                    "evidence_id": r.evidence_id,
                    "source_layer": r.source_layer,
                    "evidence_type": r.evidence_type,
                    "direction": r.direction.value,
                    "claim": r.claim,
                    "rule_id": r.rule_id,
                    "rule_source": r.rule_source,
                    "basis": r.basis,
                    "confidence": r.confidence.value,
                    "validation_state": r.validation_state,
                    "provisional": r.provisional,
                    "notes": r.notes,
                }
                for r in self.evidence_records
            ],
            "conflicts": self.conflicts,
            "synthesis": self.synthesize_narrative(),
        }
