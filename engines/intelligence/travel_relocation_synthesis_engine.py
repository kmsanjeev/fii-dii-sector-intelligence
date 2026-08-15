"""VEDA-P030 travel, relocation and foreign-residence synthesis.

This module consumes governed domain facts. It does not calculate astronomy,
immigration outcomes, or reinterpret unvalidated Vargas.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


MOVEMENT_STATES = {"STRONG", "MODERATE", "MIXED", "WEAK", "INSUFFICIENT_DATA"}
TIMING_STATES = {"NOT_ACTIVE", "BUILDUP", "SUPPORTIVE", "STRONGLY_SUPPORTIVE", "MIXED", "DELAYED", "STRESS", "RETURN_ACTIVE", "INSUFFICIENT_DATA"}


@dataclass(slots=True)
class TravelRelocationSynthesis:
    domain: str = "TRAVEL_RELOCATION"
    travel_potential: str = "INSUFFICIENT_DATA"
    short_travel: str = "INSUFFICIENT_DATA"
    long_distance_travel: str = "INSUFFICIENT_DATA"
    repeated_travel: str = "INSUFFICIENT_DATA"
    professional_travel: str = "INSUFFICIENT_DATA"
    educational_travel: str = "INSUFFICIENT_DATA"
    pilgrimage_travel: str = "INSUFFICIENT_DATA"
    relocation_potential: str = "INSUFFICIENT_DATA"
    temporary_relocation: str = "INSUFFICIENT_DATA"
    domestic_relocation: str = "INSUFFICIENT_DATA"
    foreign_travel: str = "INSUFFICIENT_DATA"
    foreign_residence: str = "INSUFFICIENT_DATA"
    foreign_settlement: str = "INSUFFICIENT_DATA"
    return_to_homeland: str = "INSUFFICIENT_DATA"
    residence_away_from_birthplace: str = "INSUFFICIENT_DATA"
    career_driven_relocation: str = "INSUFFICIENT_DATA"
    education_driven_relocation: str = "INSUFFICIENT_DATA"
    marriage_driven_relocation: str = "INSUFFICIENT_DATA"
    family_driven_relocation: str = "INSUFFICIENT_DATA"
    movement_timing: str = "INSUFFICIENT_DATA"
    supportive_windows: list[str] = field(default_factory=list)
    stress_windows: list[str] = field(default_factory=list)
    return_windows: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    confidence: str = "VERY_LOW"
    missing_data: list[str] = field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    opposing_evidence: list[dict[str, Any]] = field(default_factory=list)
    reasoning_trace: list[str] = field(default_factory=list)
    trust_state: str = "RESEARCH_CANDIDATE"
    safety_status: str = "NO_IMMIGRATION_LEGAL_OR_FINANCIAL_ADVICE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _state(value: float | None) -> str:
    if value is None:
        return "INSUFFICIENT_DATA"
    if value >= 0.75:
        return "STRONG"
    if value >= 0.5:
        return "MODERATE"
    if value >= 0.25:
        return "MIXED"
    return "WEAK"


def _score(scores: dict[str, Any], key: str) -> str:
    value = scores.get(key)
    return _state(value if isinstance(value, (int, float)) else None)


class TravelRelocationSynthesisEngine:
    """Deterministic P030 synthesis over already-calculated facts."""

    def synthesize(
        self,
        chart: dict[str, Any] | None = None,
        *,
        property_context: dict[str, Any] | None = None,
        career_context: dict[str, Any] | None = None,
        education_context: dict[str, Any] | None = None,
        relationship_context: dict[str, Any] | None = None,
        subject_id: str | None = None,
    ) -> TravelRelocationSynthesis:
        chart = chart or {}
        property_context = property_context or {}
        career_context = career_context or {}
        education_context = education_context or {}
        relationship_context = relationship_context or {}
        scores = chart.get("movement_scores") or {}
        result = TravelRelocationSynthesis()

        result.travel_potential = _score(scores, "travel_potential")
        for field_name in (
            "short_travel", "long_distance_travel", "repeated_travel", "professional_travel",
            "educational_travel", "pilgrimage_travel", "relocation_potential", "temporary_relocation",
            "domestic_relocation", "foreign_travel", "foreign_residence", "foreign_settlement",
            "return_to_homeland", "residence_away_from_birthplace", "career_driven_relocation",
            "education_driven_relocation", "marriage_driven_relocation", "family_driven_relocation",
        ):
            setattr(result, field_name, _score(scores, field_name))

        result.missing_data.extend(chart.get("missing_data") or [])
        if not chart.get("house_facts"):
            result.missing_data.append("HOUSE_EVIDENCE_NOT_SUPPLIED")
        result.missing_data.extend(self._varga_gaps(chart))

        # These are governance distinctions, not classical claims.
        if result.travel_potential != "INSUFFICIENT_DATA" and result.relocation_potential == "INSUFFICIENT_DATA":
            result.conditions.append("Travel potential does not establish a change of primary residence.")
            result.alternatives.append("SHORT_OR_LONG_TRAVEL_WITHOUT_RELOCATION")
        if result.relocation_potential != "INSUFFICIENT_DATA" and result.foreign_residence == "INSUFFICIENT_DATA":
            result.conditions.append("Relocation potential does not establish foreign residence or settlement.")
        if result.foreign_residence != "INSUFFICIENT_DATA" and result.foreign_settlement in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.conditions.append("Foreign residence is represented separately from permanent settlement.")
        if result.foreign_travel != "INSUFFICIENT_DATA" and result.foreign_residence in {"WEAK", "INSUFFICIENT_DATA"}:
            result.alternatives.append("FOREIGN_TRAVEL_WITHOUT_FOREIGN_RESIDENCE")
        if result.residence_away_from_birthplace != "INSUFFICIENT_DATA":
            result.conditions.append("Living away from birthplace is not automatically foreign residence.")

        if property_context:
            result.conditions.append("P029 residence/property context is consumed without inferring property acquisition.")
            if property_context.get("residence_change") and result.relocation_potential == "INSUFFICIENT_DATA":
                result.alternatives.append("P029_RESIDENCE_CHANGE_SIGNAL")
        if career_context:
            result.conditions.append("P021 career context is an association for movement, not a causal guarantee.")
        if education_context:
            result.conditions.append("P023 education context supports study-related movement only where supplied.")
        if relationship_context:
            result.conditions.append("P024/P028 relationship context supports marriage-associated movement only where supplied.")

        if result.travel_potential != "INSUFFICIENT_DATA" and result.relocation_potential != "INSUFFICIENT_DATA":
            if result.travel_potential in {"STRONG", "MODERATE"} and result.relocation_potential in {"WEAK", "MIXED"}:
                result.contradictions.append("Travel is stronger than relocation; movement need not change residence.")
        if result.foreign_residence in {"STRONG", "MODERATE"} and result.foreign_settlement in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.contradictions.append("Foreign residence is stronger than permanent-settlement evidence.")

        dasha = chart.get("dasha_activation")
        transit = chart.get("transit_trigger")
        has_structural_movement = any(
            getattr(result, name) != "INSUFFICIENT_DATA"
            for name in ("travel_potential", "relocation_potential", "foreign_travel", "foreign_residence", "return_to_homeland")
        )
        if not has_structural_movement:
            result.movement_timing = "INSUFFICIENT_DATA"
        elif dasha == "SUPPORTIVE" and transit == "SUPPORTIVE":
            result.movement_timing = "RETURN_ACTIVE" if result.return_to_homeland in {"STRONG", "MODERATE"} else "STRONGLY_SUPPORTIVE"
            result.supportive_windows.append("CURRENT_DASHA_TRANSIT_CONVERGENCE")
        elif dasha == "SUPPORTIVE":
            result.movement_timing = "SUPPORTIVE"
            result.supportive_windows.append("DASHA_SUPPORT_WITHOUT_TRANSIT_CONFIRMATION")
        elif transit in {"STRESS", "DELAYED"}:
            result.movement_timing = "STRESS" if transit == "STRESS" else "DELAYED"
            result.stress_windows.append("TRANSIT_STRESS_OR_DELAY")
        else:
            result.movement_timing = "NOT_ACTIVE"
            result.conditions.append("Movement potential is not treated as an activated event without governed timing.")

        if result.return_to_homeland in {"STRONG", "MODERATE"} and result.movement_timing in {"SUPPORTIVE", "STRONGLY_SUPPORTIVE", "RETURN_ACTIVE"}:
            result.return_windows.append("RETURN_TIMING_REQUIRES_DASHA_TRANSIT_CONFIRMATION")
        if result.travel_potential != "INSUFFICIENT_DATA":
            result.supporting_evidence.append(self._evidence("MOVEMENT_STRUCTURAL", "Supplied movement-domain facts", "PRIMARY", "MOVEMENT_STRUCTURAL"))
        if result.contradictions:
            result.opposing_evidence.append(self._evidence("P027_CONTRADICTION", "Conflicting movement layers retained", "OPPOSING", "MOVEMENT_CONTRADICTION"))

        result.confidence = "MODERATE" if result.movement_timing in {"SUPPORTIVE", "STRONGLY_SUPPORTIVE", "RETURN_ACTIVE"} and not result.contradictions and not result.missing_data else "LOW_TO_MODERATE" if result.travel_potential != "INSUFFICIENT_DATA" else "VERY_LOW"
        result.reasoning_trace = [
            "Existing chart/domain facts are consumed; astronomy is not recalculated.",
            "Travel, relocation, foreign residence and settlement are separate outputs.",
            "Structural movement potential precedes Dasha activation and Transit refinement.",
            "D4 calculation metadata is not treated as D4 travel interpretation.",
            "P029/P021/P023/P024 contexts are associations, not automatic causality.",
            "No immigration, legal, financial or career-decision advice is generated.",
        ]
        return result

    @staticmethod
    def _varga_gaps(chart: dict[str, Any]) -> list[str]:
        gaps: list[str] = []
        metadata = chart.get("varga_metadata") or {}
        d4 = metadata.get("D4") or {}
        if d4.get("calculation_status") == "VALIDATED":
            gaps.append("D4_INTERPRETATION_NOT_VALIDATED")
        else:
            gaps.append("D4_NOT_AVAILABLE_OR_NOT_VALIDATED")
        for varga in ("D9", "D10", "D12"):
            if varga not in metadata:
                gaps.append(f"{varga}_TRAVEL_INTERPRETATION_NOT_VALIDATED")
        return gaps

    @staticmethod
    def _evidence(source: str, claim: str, role: str, lineage: str) -> dict[str, Any]:
        return {"source_engine": source, "claim": claim, "role": role, "evidence_type": "DOMAIN_SYNTHESIS", "lineage_id": lineage, "authority_class": "RESEARCH_CANDIDATE"}


def build_travel_benchmark() -> list[dict[str, Any]]:
    labels = ("short_travel", "long_distance_travel", "repeated_travel", "relocation_potential", "domestic_relocation", "foreign_travel", "foreign_residence", "foreign_settlement", "return_to_homeland", "career_driven_relocation", "education_driven_relocation", "marriage_driven_relocation", "residence_away_from_birthplace", "temporary_relocation")
    return [{"case_id": f"TRAVEL-{i + 1:03d}", "chart": {"movement_scores": {labels[i % len(labels)]: ((i % 4) + 1) / 4}}, "expected": "DISTINCT_MOVEMENT_DIMENSIONS"} for i in range(160)]


def build_travel_holdout() -> list[dict[str, Any]]:
    return [{"case_id": f"TRAVEL-HOLDOUT-{i + 1:03d}", "chart": {"movement_scores": {"foreign_travel": ((i % 3) + 1) / 3, "foreign_settlement": (i % 2) / 2}}, "expected": "NO_SETTLEMENT_CERTAINTY"} for i in range(50)]


__all__ = ["TravelRelocationSynthesis", "TravelRelocationSynthesisEngine", "build_travel_benchmark", "build_travel_holdout"]
