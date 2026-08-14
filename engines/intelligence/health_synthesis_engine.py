"""P026 experimental/shadow health synthesis with a medical boundary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from engines.intelligence.health_evidence_aggregation import ConfidenceBand, EvidenceDirection, HealthEvidenceAggregator


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class HealthPredictionRecord:
    prediction_id: str
    domain: str
    created_at: str
    window_start: str
    window_end: str
    prediction_type: str
    prediction_state: str
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    opposing_evidence: list[dict[str, Any]] = field(default_factory=list)
    cancelling_evidence: list[dict[str, Any]] = field(default_factory=list)
    method_version: str = "P026_SHADOW_1"
    rule_versions: list[str] = field(default_factory=list)
    confidence_state: str = "RESEARCH_REQUIRED"
    actual_outcome: str | None = None
    outcome_recorded_at: str | None = None
    comparison_result: str | None = None
    notes: str = ""

    def record_outcome(self, actual_outcome: str, *, outcome_recorded_at: str | None = None) -> None:
        self.actual_outcome = actual_outcome
        self.outcome_recorded_at = outcome_recorded_at or _now()
        self.comparison_result = "MATCH" if actual_outcome == self.prediction_state else "MISMATCH"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HealthSynthesisOutput:
    synthesis_id: str
    subject_id: str | None
    created_at: str
    domain: str = "HEALTH"
    prediction_mode: str = "RESEARCH_ONLY"
    prediction_state: str = "SHADOW"
    overall_state: str = "INSUFFICIENT_EVIDENCE"
    confidence_summary: str = "RESEARCH_REQUIRED"
    interpretation_status: str = "SHADOW_ONLY"
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    opposing_evidence: list[dict[str, Any]] = field(default_factory=list)
    conditional_evidence: list[dict[str, Any]] = field(default_factory=list)
    cancelling_evidence: list[dict[str, Any]] = field(default_factory=list)
    experimental_evidence: list[dict[str, Any]] = field(default_factory=list)
    blocked_dependencies: list[dict[str, Any]] = field(default_factory=list)
    d1_context: dict[str, Any] = field(default_factory=dict)
    varga_context: dict[str, Any] = field(default_factory=dict)
    dasha_context: dict[str, Any] = field(default_factory=dict)
    yoga_dosha_context: dict[str, Any] = field(default_factory=dict)
    strength_context: dict[str, Any] = field(default_factory=dict)
    transit_context: dict[str, Any] = field(default_factory=dict)
    medical_boundary_notice: str = "ASTROLOGICAL_HEALTH_INDICATOR_NOT_CLINICAL_DIAGNOSIS"
    explainability_trace: list[str] = field(default_factory=list)
    experimental: bool = True
    shadow: bool = True
    backtesting_ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HealthSynthesisEngine:
    def __init__(self) -> None:
        self.aggregator = HealthEvidenceAggregator()

    def _context(self, facts: dict[str, Any], layer: str, claim: str, direction: EvidenceDirection, evidence_type: str, variant: str, confidence: ConfidenceBand = ConfidenceBand.MODERATE) -> None:
        self.aggregator.add_evidence(source_layer=layer, evidence_type=evidence_type, direction=direction, claim=claim, basis=facts, confidence=confidence, validation_state=facts.get("validation_state", "RESEARCH_REQUIRED"), provisional=True, source_id=facts.get("source_id"), passage_id=facts.get("passage_id", "REFERENCE_NOT_VERIFIED"), method_variant=variant)

    def synthesize(self, *, subject_id: str | None = None, natal_factors: dict[str, Any] | None = None, varga_facts: dict[str, Any] | None = None, dasha_context: dict[str, Any] | None = None, transit_context: dict[str, Any] | None = None, yoga_facts: dict[str, Any] | None = None, strength_facts: dict[str, Any] | None = None, prediction_mode: str = "RESEARCH_ONLY") -> HealthSynthesisOutput:
        self.aggregator = HealthEvidenceAggregator()
        natal_factors, varga_facts, dasha_context, transit_context, yoga_facts, strength_facts = natal_factors or {}, varga_facts or {}, dasha_context or {}, transit_context or {}, yoga_facts or {}, strength_facts or {}
        if natal_factors:
            self._context(natal_factors, "D1", "D1 Lagna and relevant health Bhavas form the natal health foundation; no single factor determines disease or recovery.", EvidenceDirection.SUPPORTING, "NATAL_VITALITY", "D1_LAGNA_BHAVA_SYNTHESIS", ConfidenceBand.HIGH if natal_factors.get("lagna") or natal_factors.get("lagnesha") else ConfidenceBand.MODERATE)
        if varga_facts:
            self._context(varga_facts, "VARGA", "Relevant Varga context may specialize health research but cannot replace D1 or establish a clinical diagnosis.", EvidenceDirection.CONDITIONAL, "VARGA", "D1_VARGA_BOUNDED_SPECIALIZATION")
        if dasha_context:
            self._context(dasha_context, "DASHA", "Dasha may identify an experimental health-support or health-challenge window, not medical prognosis.", EvidenceDirection.OPPOSING if dasha_context.get("challenge") else EvidenceDirection.EXPERIMENTAL, "TIMING", "HEALTH_TIMING_HYPOTHESIS")
        if transit_context:
            self._context(transit_context, "TRANSIT", "Transit is contextual timing evidence and cannot establish disease onset or recovery.", EvidenceDirection.SUPPORTING if transit_context.get("support") else EvidenceDirection.CONDITIONAL, "TIMING", "GOCHAR_CONTEXT_ONLY", ConfidenceBand.LOW)
        if yoga_facts:
            self._context(yoga_facts, "YOGA_DOSHA", "Health Yoga/Dosha formation is preserved with mitigation and interpretation status.", EvidenceDirection.CANCELLING if yoga_facts.get("mitigation_present") else EvidenceDirection.CONDITIONAL, "YOGA_DOSHA", "MITIGATION_VARIANT_PRESERVATION")
        if strength_facts:
            self._context(strength_facts, "STRENGTH", "Unvalidated strength informs research and shadow context only.", EvidenceDirection.CONDITIONAL if strength_facts.get("validated") else EvidenceDirection.RESEARCH_ONLY, "STRENGTH", "UNVALIDATED_STRENGTH_PROPAGATION", ConfidenceBand.LOW)
        synthesis = self.aggregator.synthesize_narrative()
        rows = self.aggregator.to_dict()["evidence_records"]
        by = lambda direction: [row for row in rows if row["direction"] == direction.value]
        return HealthSynthesisOutput(synthesis_id=f"HLT_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}", subject_id=subject_id, created_at=_now(), prediction_mode=prediction_mode, prediction_state=prediction_mode, overall_state=synthesis["overall_state"], confidence_summary=synthesis["overall_confidence"], interpretation_status="SHADOW_ONLY" if prediction_mode != "RESEARCH_ONLY" else "RESEARCH_ONLY", supporting_evidence=by(EvidenceDirection.SUPPORTING), opposing_evidence=by(EvidenceDirection.OPPOSING), conditional_evidence=by(EvidenceDirection.CONDITIONAL), cancelling_evidence=by(EvidenceDirection.CANCELLING), experimental_evidence=by(EvidenceDirection.EXPERIMENTAL), blocked_dependencies=by(EvidenceDirection.BLOCKED_DEPENDENCY), d1_context=natal_factors, varga_context=varga_facts, dasha_context=dasha_context, yoga_dosha_context=yoga_facts, strength_context=strength_facts, transit_context=transit_context, medical_boundary_notice="ASTROLOGICAL_HEALTH_INDICATOR_NOT_CLINICAL_DIAGNOSIS", explainability_trace=["HEALTH SYNTHESIS", f"overall_state={synthesis['overall_state']}", "TRACE: support/opposition/mitigation -> rules -> D1/Varga/Dasha/Yoga/Strength/Transit facts", "TRACE: claims -> passages -> sources"], experimental=prediction_mode in {"EXPERIMENTAL", "SHADOW"}, shadow=prediction_mode == "SHADOW")

    def create_prediction_record(self, *, prediction_type: str, prediction_state: str, window_start: str, window_end: str, confidence_state: str, method_version: str = "P026_SHADOW_1", rule_versions: list[str] | None = None, supporting_evidence: list[dict[str, Any]] | None = None, opposing_evidence: list[dict[str, Any]] | None = None, cancelling_evidence: list[dict[str, Any]] | None = None, notes: str = "") -> HealthPredictionRecord:
        return HealthPredictionRecord(f"P026-HLT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", "HEALTH", _now(), window_start, window_end, prediction_type, prediction_state, supporting_evidence or [], opposing_evidence or [], cancelling_evidence or [], method_version, rule_versions or [], confidence_state, notes=notes)


__all__ = ["HealthPredictionRecord", "HealthSynthesisEngine", "HealthSynthesisOutput"]
