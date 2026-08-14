"""P023 education synthesis engine.

Shadow-only education synthesis using governed evidence aggregation.
Produces experimental predictions marked explicitly as SHADOW_ONLY.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from engines.intelligence.education_evidence_aggregation import (
    EducationEvidenceAggregator,
)


@dataclass
class EducationSynthesisOutput:
    """Synthesis output contract for education."""

    synthesis_id: str
    subject_id: Optional[str]
    created_at: str
    domain: str = "EDUCATION"
    prediction_state: str = "SHADOW_ONLY"

    # Evidence layers
    supporting_evidence: list[dict[str, Any]] = None
    opposing_evidence: list[dict[str, Any]] = None
    conditional_evidence: list[dict[str, Any]] = None

    # Context
    varga_context: dict[str, Any] = None
    dasha_context: dict[str, Any] = None
    yoga_context: dict[str, Any] = None
    strength_context: dict[str, Any] = None
    transit_context: dict[str, Any] = None

    # Synthesis
    overall_interpretation: str = "INSUFFICIENT_EVIDENCE"
    confidence_summary: str = "RESEARCH_REQUIRED"
    key_factors: list[str] = None

    # Metadata
    interpretation_status: str = "SHADOW_ONLY"
    experimental: bool = True
    backtesting_ready: bool = True

    # Explainability
    explainability_trace: dict[str, Any] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.supporting_evidence is None:
            self.supporting_evidence = []
        if self.opposing_evidence is None:
            self.opposing_evidence = []
        if self.conditional_evidence is None:
            self.conditional_evidence = []
        if self.varga_context is None:
            self.varga_context = {}
        if self.dasha_context is None:
            self.dasha_context = {}
        if self.yoga_context is None:
            self.yoga_context = {}
        if self.strength_context is None:
            self.strength_context = {}
        if self.transit_context is None:
            self.transit_context = {}
        if self.key_factors is None:
            self.key_factors = []
        if self.explainability_trace is None:
            self.explainability_trace = {}


class EducationSynthesisEngine:
    """P023 Education Synthesis Engine.

    Reuses P020 synthesis pattern:
    - Non-deterministic output
    - Explicit state marking (SHADOW_ONLY, EXPERIMENTAL)
    - No production activation
    - Research and backtesting-ready
    """

    def __init__(self):
        self.aggregator = EducationEvidenceAggregator()

    def synthesize(
        self,
        subject_id: Optional[str] = None,
        natal_factors: dict[str, Any] | None = None,
        varga_facts: dict[str, Any] | None = None,
        dasha_context: dict[str, Any] | None = None,
        transit_context: dict[str, Any] | None = None,
        yoga_facts: dict[str, Any] | None = None,
        strength_facts: dict[str, Any] | None = None,
    ) -> EducationSynthesisOutput:
        """Synthesize education profile."""

        synthesis_id = f"EDU_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Populate aggregator with evidence
        self._populate_evidence(
            natal_factors or {},
            varga_facts or {},
            dasha_context or {},
            transit_context or {},
            yoga_facts or {},
            strength_facts or {},
        )

        # Detect conflicts
        self.aggregator.detect_conflicts()

        # Generate synthesis
        synthesis = self.aggregator.synthesize_narrative()

        # Extract key factors
        key_factors = [
            r.claim
            for r in self.aggregator.evidence_records
            if r.direction.value == "SUPPORTING"
        ][:3]

        # Generate explainability trace
        trace = {
            "evidence_count": len(self.aggregator.evidence_records),
            "conflict_count": len(self.aggregator.conflicts),
            "supporting_count": synthesis["supporting_count"],
            "opposing_count": synthesis["opposing_count"],
            "conditional_count": synthesis["conditional_count"],
            "blocked_count": synthesis["blocked_count"],
            "confidence": synthesis["overall_confidence"],
        }

        output = EducationSynthesisOutput(
            synthesis_id=synthesis_id,
            subject_id=subject_id,
            created_at=datetime.utcnow().isoformat(),
            supporting_evidence=[
                {
                    "claim": r.claim,
                    "source": r.source_layer,
                    "confidence": r.confidence.value,
                }
                for r in self.aggregator.evidence_records
                if r.direction.value == "SUPPORTING"
            ],
            opposing_evidence=[
                {
                    "claim": r.claim,
                    "source": r.source_layer,
                    "confidence": r.confidence.value,
                }
                for r in self.aggregator.evidence_records
                if r.direction.value == "OPPOSING"
            ],
            conditional_evidence=[
                {
                    "claim": r.claim,
                    "source": r.source_layer,
                    "confidence": r.confidence.value,
                }
                for r in self.aggregator.evidence_records
                if r.direction.value == "CONDITIONAL"
            ],
            varga_context=varga_facts or {},
            dasha_context=dasha_context or {},
            yoga_context=yoga_facts or {},
            strength_context=strength_facts or {},
            transit_context=transit_context or {},
            overall_interpretation=synthesis["overall_interpretation"],
            confidence_summary=synthesis["overall_confidence"],
            key_factors=key_factors,
            explainability_trace=trace,
        )

        return output

    def _populate_evidence(
        self,
        natal_factors: dict[str, Any],
        varga_facts: dict[str, Any],
        dasha_context: dict[str, Any],
        transit_context: dict[str, Any],
        yoga_facts: dict[str, Any],
        strength_facts: dict[str, Any],
    ) -> None:
        """Populate evidence records from input facts."""

        # This is a placeholder implementation.
        # In full P023, this would:
        # - Parse natal factors (4th/5th/9th house, lords, occupants)
        # - Parse Varga facts (D24 calculations and interpretation)
        # - Parse Dasha context (timing windows)
        # - Parse Transit context (current influences)
        # - Parse Yoga context (education yogas)
        # - Parse Strength context (unvalidated components marked clearly)
        # - Apply P023-approved rules to generate evidence
        # - Preserve conflicts and blocked dependencies

        if not any(
            [natal_factors, varga_facts, dasha_context, transit_context, yoga_facts, strength_facts]
        ):
            # No input provided
            return

        # Placeholder: add minimal evidence for testing
        from engines.intelligence.education_evidence_aggregation import EvidenceDirection, ConfidenceBand

        self.aggregator.add_evidence(
            source_layer="NATAL",
            evidence_type="FOUNDATION",
            direction=EvidenceDirection.NEUTRAL,
            claim="Natal factors received",
            confidence=ConfidenceBand.MODERATE,
            validation_state="APPROVED_CORE",
            provisional=False,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert output to dictionary."""
        output = EducationSynthesisOutput(
            synthesis_id="EDU_test",
            subject_id=None,
            created_at=datetime.utcnow().isoformat(),
            supporting_evidence=[],
            opposing_evidence=[],
            conditional_evidence=[],
            varga_context={},
            dasha_context={},
            yoga_context={},
            strength_context={},
            transit_context={},
            overall_interpretation="INSUFFICIENT_EVIDENCE",
            confidence_summary="RESEARCH_REQUIRED",
            key_factors=[],
        )

        return {
            "synthesis_id": output.synthesis_id,
            "subject_id": output.subject_id,
            "created_at": output.created_at,
            "domain": output.domain,
            "prediction_state": output.prediction_state,
            "overall_interpretation": output.overall_interpretation,
            "confidence_summary": output.confidence_summary,
            "interpretation_status": output.interpretation_status,
            "experimental": output.experimental,
            "backtesting_ready": output.backtesting_ready,
        }
