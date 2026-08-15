"""P028 relationship synthesis over the governed P027 evidence contract."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Iterable

from .p027_synthesis import P027SynthesisEngine, SynthesisEvidence


class RelationshipType(StrEnum):
    ROMANTIC_RELATIONSHIP = "ROMANTIC_RELATIONSHIP"
    MARRIAGE = "MARRIAGE"
    LONG_TERM_PARTNERSHIP = "LONG_TERM_PARTNERSHIP"
    BUSINESS_PARTNERSHIP = "BUSINESS_PARTNERSHIP"
    PROFESSIONAL_PARTNERSHIP = "PROFESSIONAL_PARTNERSHIP"


class DimensionState(StrEnum):
    VERY_WEAK = "VERY_WEAK"
    WEAK = "WEAK"
    MIXED = "MIXED"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(slots=True)
class RelationshipSubject:
    chart_id: str
    subject_id: str
    label: str
    birth_data_quality: str = "UNKNOWN"
    relationship_promise: str = "INSUFFICIENT_DATA"
    promise_evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CompatibilityResult:
    relationship_id: str
    chart_a_id: str
    chart_b_id: str
    subject_a_id: str
    subject_b_id: str
    subject_a_label: str
    subject_b_label: str
    relationship_type: str
    analysis_domain: str
    method_version: str
    dimensions: dict[str, str]
    overall_state: str
    dominant_strengths: list[str]
    vulnerabilities: list[str]
    friction_areas: list[str]
    asymmetries: list[dict[str, str]]
    traditional_matching: dict[str, Any]
    timing: dict[str, Any]
    conditions: list[str]
    contradictions: list[dict[str, Any]]
    confidence: str
    evidence: list[dict[str, Any]]
    reasoning_trace: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class P028CompatibilityEngine:
    """Multidimensional relationship synthesis; never produces a magic score."""

    method_version = "P028_COMPATIBILITY_1"
    supported_relationships = {item.value for item in RelationshipType}
    dimensions = ("EMOTIONAL_ALIGNMENT", "COMMUNICATION_ALIGNMENT", "ATTRACTION_BONDING", "VALUES_ALIGNMENT", "DOMESTIC_ALIGNMENT", "MUTUAL_SUPPORT", "CONFLICT_RESILIENCE", "LONG_TERM_STABILITY", "TIMING_ALIGNMENT")

    def analyze(self, *, relationship_id: str, subject_a: RelationshipSubject, subject_b: RelationshipSubject, relationship_type: str, evidence: Iterable[SynthesisEvidence | dict[str, Any]], traditional_matching: dict[str, Any] | Any | None = None, timing: dict[str, Any] | None = None, analysis_domain: str = "RELATIONSHIP") -> CompatibilityResult:
        if relationship_type not in self.supported_relationships:
            raise ValueError(f"Unsupported relationship type: {relationship_type}")
        rows = [row if isinstance(row, SynthesisEvidence) else SynthesisEvidence.from_dict(row) for row in evidence]
        if traditional_matching is not None and hasattr(traditional_matching, "to_dict"):
            traditional_matching = traditional_matching.to_dict()
        if traditional_matching:
            traditional_rows = traditional_matching.get("components", {})
            rows.extend(SynthesisEvidence(evidence_id=f"P028R1-{name}", claim=f"{name} score {item.get('score')}/{item.get('maximum')}", evidence_type="TRADITIONAL_MATCHING", direction="SUPPORTS" if (item.get("score") or 0) >= (item.get("maximum") or 1) / 2 else "OPPOSES", authority_class=traditional_matching.get("authority", "RESEARCH_CANDIDATE"), knowledge_zone=traditional_matching.get("authority", "RESEARCH_CANDIDATE"), lineage_id=item.get("lineage_id", "TRADITIONAL_MATCHING"), method_variant=traditional_matching.get("method_id")) for name, item in traditional_rows.items())
        if any(row.chart_id not in {subject_a.chart_id, subject_b.chart_id} for row in rows if row.chart_id):
            raise ValueError("Evidence chart_id is outside the declared subject pair")
        if any(row.chart_id == subject_a.chart_id and row.subject_id not in {None, subject_a.subject_id} for row in rows):
            raise ValueError("Chart A evidence has a foreign subject")
        if any(row.chart_id == subject_b.chart_id and row.subject_id not in {None, subject_b.subject_id} for row in rows):
            raise ValueError("Chart B evidence has a foreign subject")
        synthesis = P027SynthesisEngine().synthesize(f"Compatibility for {subject_a.label} and {subject_b.label}", rows, domain=analysis_domain)
        dimensions = {name: self._dimension(rows, name) for name in self.dimensions}
        strengths = [name for name, state in dimensions.items() if state in {DimensionState.STRONG.value, DimensionState.VERY_STRONG.value}]
        friction = [name for name, state in dimensions.items() if state in {DimensionState.WEAK.value, DimensionState.VERY_WEAK.value}]
        asymmetries = self._asymmetry(rows)
        match = traditional_matching or {"state": "NOT_IMPLEMENTED", "method_version": None, "score": None, "limitation": "Ashtakoota/Guna Milan is not implemented in the repository; no score is fabricated."}
        return CompatibilityResult(relationship_id, subject_a.chart_id, subject_b.chart_id, subject_a.subject_id, subject_b.subject_id, subject_a.label, subject_b.label, relationship_type, analysis_domain, self.method_version, dimensions, "MIXED" if synthesis.contradictions else ("SUPPORTED" if strengths else "INSUFFICIENT_DATA"), strengths, ["INDIVIDUAL_PROMISE_A" if subject_a.relationship_promise == "INSUFFICIENT_DATA" else "" , "INDIVIDUAL_PROMISE_B" if subject_b.relationship_promise == "INSUFFICIENT_DATA" else ""], friction, asymmetries, match, timing or {"state": "INSUFFICIENT_DATA"}, [*synthesis.conditions], [asdict(item) for item in synthesis.contradictions], synthesis.confidence.value, [row.to_dict() for row in rows], ["P024 individual relationship promise is an input, not replaced.", "P027 evidence roles, lineage, contradiction, and confidence reused.", "Astrological compatibility is separate from current conversational emotion.", "No single score determines relationship outcome.", *synthesis.reasoning_trace])

    def _dimension(self, rows: list[SynthesisEvidence], name: str) -> str:
        selected = [row for row in rows if (row.domain or "").upper() == name or (row.factor or "").upper() == name]
        if not selected:
            return DimensionState.INSUFFICIENT_DATA.value
        support = sum(1 for row in selected if row.direction.upper() in {"SUPPORTS", "SUPPORTING", "POSITIVE"})
        oppose = sum(1 for row in selected if row.direction.upper() in {"OPPOSES", "OPPOSING", "NEGATIVE"})
        if support and oppose:
            return DimensionState.MIXED.value
        return DimensionState.STRONG.value if support >= 2 else DimensionState.MODERATE.value if support else DimensionState.WEAK.value

    def _asymmetry(self, rows: list[SynthesisEvidence]) -> list[dict[str, str]]:
        return [{"direction": row.direction, "claim": row.claim, "chart_id": row.chart_id or "UNKNOWN", "subject_id": row.subject_id or "UNKNOWN"} for row in rows if row.direction.upper() in {"A_TO_B", "B_TO_A", "MUTUAL"}]


__all__ = ["CompatibilityResult", "DimensionState", "P028CompatibilityEngine", "RelationshipSubject", "RelationshipType"]
