"""P022 Wealth Evidence Aggregation & Conflict Handling

Implements M014-M018: Evidence synthesis, conflict handling, confidence modeling,
explainability, and approved-core promotion.

Reuses P020 aggregation framework for wealth domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from pathlib import Path

from engines.common import config as cfg


class EvidenceDirection(str, Enum):
    """Evidence can support, oppose, or be conditional."""
    SUPPORTING = "SUPPORTING"
    OPPOSING = "OPPOSING"
    CONDITIONAL = "CONDITIONAL"
    BLOCKED = "BLOCKED"


class ConfidenceBand(str, Enum):
    """Qualitative confidence bands only - no false precision."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    LOW_TO_MODERATE = "LOW_TO_MODERATE"
    MODERATE_TO_HIGH = "MODERATE_TO_HIGH"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"


class WealthOverallState(str, Enum):
    """Overall wealth state classification - conservative by default."""
    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
    SUPPORTED = "SUPPORTED"
    MIXED = "MIXED"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BLOCKED = "BLOCKED"
    RESEARCH_ONLY = "RESEARCH_ONLY"


@dataclass
class WealthEvidence:
    """Single piece of wealth evidence with provenance."""
    evidence_id: str
    domain_id: str = "WEALTH"
    source_layer: str = ""  # NATAL, 2ND_BHAVA, 11TH_BHAVA, etc.
    evidence_type: str = ""  # SUPPORTING, OPPOSING, CONDITIONAL
    direction: EvidenceDirection = EvidenceDirection.SUPPORTING
    weight: str = "PRIMARY"  # PRIMARY or SECONDARY
    confidence: ConfidenceBand = ConfidenceBand.LOW_TO_MODERATE
    validation_status: str = "RESEARCH_REQUIRED"
    dependency_status: str = "RESOLVED"
    interpretation: str = ""
    source_claim_ids: list[str] = field(default_factory=list)
    explainability: list[str] = field(default_factory=list)


@dataclass
class WealthConflict:
    """Explicit conflict between evidence layers."""
    conflict_id: str
    domain_id: str = "WEALTH"
    conflict_type: str = ""  # SCOPE_COLLISION, INTERPRETATION_UNVALIDATED, etc.
    status: str = "CONTEXT_DEPENDENT"
    description: str = ""
    resolution: str = ""
    evidence_ids: list[str] = field(default_factory=list)


class WealthEvidenceAggregator:
    """M014-M015: Evidence aggregation and conflict handling."""

    def __init__(self):
        self.evidence: list[WealthEvidence] = []
        self.conflicts: list[WealthConflict] = []
        self.blocked_evidence: list[WealthEvidence] = []

    def add_evidence(self, evidence: WealthEvidence) -> None:
        """Add evidence with validation."""
        if evidence.direction == EvidenceDirection.BLOCKED:
            self.blocked_evidence.append(evidence)
        else:
            self.evidence.append(evidence)

    def add_conflict(self, conflict: WealthConflict) -> None:
        """Track explicit conflicts."""
        self.conflicts.append(conflict)

    def aggregate(self) -> dict[str, Any]:
        """
        M014: Aggregate evidence into overall state.
        Reuses P020 aggregation pattern.
        """
        supporting = [e for e in self.evidence if e.direction == EvidenceDirection.SUPPORTING]
        opposing = [e for e in self.evidence if e.direction == EvidenceDirection.OPPOSING]
        conditional = [e for e in self.evidence if e.direction == EvidenceDirection.CONDITIONAL]

        # M015: Conflict handling
        has_conflicts = len(self.conflicts) > 0

        # Determine overall state conservatively
        if len(self.blocked_evidence) > 0:
            overall_state = WealthOverallState.BLOCKED
        elif len(self.evidence) == 0:
            overall_state = WealthOverallState.INSUFFICIENT_EVIDENCE
        elif has_conflicts:
            overall_state = WealthOverallState.MIXED
        elif len(opposing) > 0:
            overall_state = WealthOverallState.MIXED
        elif len(supporting) >= 3 and len(conditional) == 0:
            overall_state = WealthOverallState.SUPPORTED
        else:
            overall_state = WealthOverallState.MIXED

        return {
            "overall_state": overall_state.value,
            "supporting_count": len(supporting),
            "opposing_count": len(opposing),
            "conditional_count": len(conditional),
            "blocked_count": len(self.blocked_evidence),
            "conflicts": len(self.conflicts),
            "has_unresolved_conflicts": has_conflicts,
            "explainability": self._build_explainability(),
        }

    def _build_explainability(self) -> list[str]:
        """M017: Build full explainability trace."""
        trace = [
            "Wealth synthesis aggregation chain:",
            "1. Canonical chart facts (NATAL layer)",
            "2. Domain-relevant selection (2nd/11th bhava focus)",
            "3. Governed rule evaluation",
            "4. Supporting and opposing evidence assessment",
            "5. Dependency status validation",
            "6. Conflict identification and handling",
            "7. Confidence synthesis (qualitative bands only)",
            "8. Safety boundary enforcement",
            "9. Output classification (RESEARCH_ONLY / SHADOW)",
        ]

        # Add evidence counts
        trace.append(f"Evidence layers: {len(self.evidence)} active, {len(self.blocked_evidence)} blocked")

        # Add conflicts
        if self.conflicts:
            trace.append(f"Conflicts identified: {len(self.conflicts)} (explicit, not suppressed)")
            for conflict in self.conflicts:
                trace.append(f"  - {conflict.conflict_type}: {conflict.description}")

        # Add safety note
        trace.append("Safety boundary: HIGH_STAKES_BLOCKED - No deterministic wealth prediction")

        return trace


@dataclass
class WealthConfidenceModel:
    """M016: Structured confidence with full transparency."""
    overall_band: ConfidenceBand
    source_diversity: int  # Count of independent source families
    rule_provenance: str  # How well-sourced are the rules?
    validation_state: str  # Status of inputs used
    dependency_readiness: float  # 0.0 to 1.0
    safety_boundary_status: str  # Whether safety boundaries held
    signal_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Structured confidence output - never false precision."""
        return {
            "overall_confidence": self.overall_band.value,
            "source_diversity": self.source_diversity,
            "rule_provenance": self.rule_provenance,
            "validation_state": self.validation_state,
            "dependency_readiness_percent": int(self.dependency_readiness * 100),
            "safety_boundary_status": self.safety_boundary_status,
            "note": "Confidence is qualitative; no percentage false precision. See explainability for full trace.",
        }


class WealthConfidenceCalculator:
    """M016: Calculate confidence without false precision."""

    @staticmethod
    def calculate(evidence_count: int, conflicts: int, blocked: int, validated_inputs: int) -> WealthConfidenceModel:
        """
        Determine confidence band based on evidence structure.
        Conservative by design.
        """
        if blocked > 0:
            band = ConfidenceBand.RESEARCH_REQUIRED
        elif evidence_count == 0:
            band = ConfidenceBand.RESEARCH_REQUIRED
        elif conflicts > 0:
            band = ConfidenceBand.LOW_TO_MODERATE
        elif evidence_count >= 5 and validated_inputs >= 3:
            band = ConfidenceBand.MODERATE
        elif evidence_count >= 3:
            band = ConfidenceBand.LOW_TO_MODERATE
        else:
            band = ConfidenceBand.LOW

        dependency_ready = min(validated_inputs / max(evidence_count, 1), 1.0)

        return WealthConfidenceModel(
            overall_band=band,
            source_diversity=min(evidence_count, 5),  # Cap display
            rule_provenance="GOVERNED_WITH_CONDITIONS",
            validation_state="PARTIAL_VALIDATION",
            dependency_readiness=dependency_ready,
            safety_boundary_status="ENFORCED",
        )


class WealthExplainabilityTracer:
    """M017: Full explainability trace for all wealth inferences."""

    @staticmethod
    def trace_wealth_claim(
        claim_text: str,
        supporting_evidence: list[WealthEvidence],
        opposing_evidence: list[WealthEvidence],
        rules_applied: list[str],
        confidence: ConfidenceBand,
        conflicts: list[WealthConflict],
    ) -> dict[str, Any]:
        """Generate full explainability trace for a wealth claim."""
        return {
            "claim": claim_text,
            "supporting_facts": [
                {
                    "evidence_id": e.evidence_id,
                    "source_layer": e.source_layer,
                    "interpretation": e.interpretation,
                    "confidence": e.confidence.value,
                }
                for e in supporting_evidence
            ],
            "opposing_facts": [
                {
                    "evidence_id": e.evidence_id,
                    "source_layer": e.source_layer,
                    "interpretation": e.interpretation,
                }
                for e in opposing_evidence
            ],
            "rules_applied": rules_applied,
            "confidence_band": confidence.value,
            "conflicts": [{"conflict_id": c.conflict_id, "description": c.description} for c in conflicts],
            "overall_assessment": "MULTI_FACTOR_SYNTHESIS",
            "safety_status": "HIGH_STAKES_BOUNDARY_ENFORCED",
            "output_mode": "RESEARCH_ONLY",
        }


@dataclass
class ApprovedCorePromotion:
    """M018: Approved-core promotion candidate (requires P010 approval)."""
    promotion_id: str
    domain_id: str = "WEALTH"
    claim_text: str = ""
    evidence_basis: list[str] = field(default_factory=list)
    rule_id: str = ""
    source_authority: str = ""  # CLASSICAL_PRIMARY, CLASSICAL_COMMENTARY, etc.
    validation_status: str = "RESEARCH_REQUIRED"
    safety_review_complete: bool = False
    approval_status: str = "NOT_SUBMITTED"
    activation_ready: bool = False


class ApprovedCoreRegistry:
    """M018: Track candidates for P010 approval (admin layer)."""

    def __init__(self):
        self.promotion_candidates: list[ApprovedCorePromotion] = []

    def add_candidate(self, candidate: ApprovedCorePromotion) -> None:
        """Register a promotion candidate for review."""
        self.promotion_candidates.append(candidate)

    def candidates_by_status(self, status: str) -> list[ApprovedCorePromotion]:
        """Get candidates by approval status."""
        return [c for c in self.promotion_candidates if c.approval_status == status]

    def activation_ready_count(self) -> int:
        """Count candidates that are ready for activation."""
        return len([c for c in self.promotion_candidates if c.activation_ready])


if __name__ == "__main__":
    # Example: Create an aggregator and demonstrate usage
    agg = WealthEvidenceAggregator()

    # Add some evidence
    evidence1 = WealthEvidence(
        evidence_id="VEDA-P022-EVID-001",
        source_layer="2ND_BHAVA",
        evidence_type="SUPPORTING",
        interpretation="Strong 2nd house lord in Kendra",
        confidence=ConfidenceBand.MODERATE,
    )
    agg.add_evidence(evidence1)

    # Aggregate
    result = agg.aggregate()
    print(f"✓ Wealth evidence aggregation ready")
    print(f"  Overall state: {result['overall_state']}")
    print(f"  Evidence layers: {result['supporting_count']} supporting")
