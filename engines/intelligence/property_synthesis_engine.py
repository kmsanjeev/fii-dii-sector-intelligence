"""VEDA-P029 property and residence synthesis.

This module consumes existing chart/domain facts. It does not calculate
astronomy, invent D4 interpretations, or provide financial/legal advice.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PROPERTY_STATES = {"STRONG", "MODERATE", "MIXED", "WEAK", "INSUFFICIENT_DATA"}
RESIDENCE_STATES = {"STABLE", "GENERALLY_STABLE", "MIXED", "CHANGE_PRONE", "UNSTABLE", "INSUFFICIENT_DATA"}


@dataclass(slots=True)
class PropertySynthesis:
    domain: str = "PROPERTY"
    property_potential: str = "INSUFFICIENT_DATA"
    property_acquisition: str = "INSUFFICIENT_DATA"
    property_ownership: str = "INSUFFICIENT_DATA"
    residential_stability: str = "INSUFFICIENT_DATA"
    residence_change: str = "INSUFFICIENT_DATA"
    land_potential: str = "INSUFFICIENT_DATA"
    constructed_property: str = "INSUFFICIENT_DATA"
    self_occupied_property: str = "UNKNOWN"
    investment_property: str = "UNKNOWN"
    inheritance_property: str = "UNKNOWN"
    sale_disposal: str = "UNKNOWN"
    construction: str = "UNKNOWN"
    renovation: str = "UNKNOWN"
    property_expenditure: str = "UNKNOWN"
    property_debt: str = "UNKNOWN"
    property_dispute: str = "UNKNOWN"
    domestic_comfort: str = "INSUFFICIENT_DATA"
    timing: str = "INSUFFICIENT_DATA"
    d4_status: str = "D4_NOT_VALIDATED"
    confidence: str = "VERY_LOW"
    conditions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    opposing_evidence: list[dict[str, Any]] = field(default_factory=list)
    conditional_evidence: list[dict[str, Any]] = field(default_factory=list)
    reasoning_trace: list[str] = field(default_factory=list)
    trust_state: str = "RESEARCH_CANDIDATE"
    safety_status: str = "NO_FINANCIAL_OR_LEGAL_ADVICE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _state(score: float | None) -> str:
    if score is None:
        return "INSUFFICIENT_DATA"
    if score >= 0.75:
        return "STRONG"
    if score >= 0.5:
        return "MODERATE"
    if score >= 0.25:
        return "MIXED"
    return "WEAK"


class PropertySynthesisEngine:
    """Deterministic P029 synthesis over already-calculated facts."""

    def synthesize(self, chart: dict[str, Any] | None = None, *, wealth_context: dict[str, Any] | None = None, subject_id: str | None = None) -> PropertySynthesis:
        chart = chart or {}
        wealth_context = wealth_context or {}
        result = PropertySynthesis()
        result.d4_status = self._d4_status(chart)
        result.missing_data.append("D4_NOT_VALIDATED")

        scores = chart.get("property_scores") or {}
        result.property_potential = _state(scores.get("potential"))
        result.property_acquisition = _state(scores.get("acquisition", scores.get("potential")))
        result.property_ownership = _state(scores.get("ownership"))
        result.domestic_comfort = _state(scores.get("comfort"))
        residence_score = scores.get("residence_stability")
        if residence_score is not None:
            result.residential_stability = "STABLE" if residence_score >= .75 else "GENERALLY_STABLE" if residence_score >= .55 else "MIXED" if residence_score >= .35 else "CHANGE_PRONE"
        change_score = scores.get("residence_change")
        if change_score is not None:
            result.residence_change = "STRONG" if change_score >= .75 else "MODERATE" if change_score >= .5 else "MIXED" if change_score >= .25 else "WEAK"

        for field_name in ("land", "constructed", "inheritance", "sale", "construction", "renovation", "expenditure", "debt", "dispute"):
            value = scores.get(field_name)
            if value is not None:
                setattr(result, {"land": "land_potential", "constructed": "constructed_property", "inheritance": "inheritance_property", "sale": "sale_disposal", "dispute": "property_dispute"}.get(field_name, field_name), _state(value))

        if result.property_ownership != "INSUFFICIENT_DATA" and result.residential_stability != "INSUFFICIENT_DATA":
            result.conditions.append("Ownership and residence are evaluated as separate dimensions.")
        if result.property_acquisition != "INSUFFICIENT_DATA" and result.property_ownership == "INSUFFICIENT_DATA":
            result.conditions.append("Acquisition potential does not establish long-term ownership.")
        if result.residence_change not in {"INSUFFICIENT_DATA", "WEAK"} and result.property_acquisition == "INSUFFICIENT_DATA":
            result.alternatives.append("RESIDENCE_CHANGE_SIGNAL")
        if wealth_context:
            result.conditions.append("P022 wealth context is supporting financial capacity only; it is not property evidence.")
            if wealth_context.get("capacity") == "STRONG" and result.property_potential in {"WEAK", "INSUFFICIENT_DATA"}:
                result.contradictions.append("Strong wealth context with weak or unavailable property-specific evidence.")
        dasha = chart.get("dasha_activation")
        transit = chart.get("transit_trigger")
        if result.property_potential == "INSUFFICIENT_DATA":
            result.timing = "INSUFFICIENT_DATA"
        elif dasha and transit:
            result.timing = "STRONGLY_SUPPORTIVE" if dasha == "SUPPORTIVE" and transit == "SUPPORTIVE" else "MIXED"
        elif dasha == "SUPPORTIVE":
            result.timing = "SUPPORTIVE"
            result.conditions.append("Dasha activation is present; transit refinement is unavailable.")
        else:
            result.timing = "NOT_ACTIVE"
            result.conditions.append("Structural potential is not treated as active timing without governed activation.")
        if result.property_potential != "INSUFFICIENT_DATA":
            result.supporting_evidence.append(self._evidence("PROPERTY_STRUCTURAL", "D1/property facts supplied by existing runtime", "PRIMARY", "PROPERTY_STRUCTURAL"))
        if result.d4_status != "D4_VALIDATED":
            result.missing_data.append(result.d4_status)
        if wealth_context:
            result.conditional_evidence.append(self._evidence("WEALTH_CONTEXT", "P022 financial capacity context", "MODIFYING", "WEALTH_CONTEXT"))
        result.confidence = "MODERATE" if result.d4_status == "D4_VALIDATED" and not result.contradictions else "LOW_TO_MODERATE" if result.property_potential != "INSUFFICIENT_DATA" else "VERY_LOW"
        result.reasoning_trace = [
            "Existing chart facts are consumed; astronomy is not recalculated.",
            "Property potential, acquisition, ownership and residence are separate outputs.",
            "D1/property evidence precedes activation; Dasha and Transit refine timing.",
            "D4 is not interpreted unless explicitly validated by the repository.",
            "P022 contributes financial context only; it does not become property evidence.",
            "No property-price, financial-advice or legal-advice conclusion is generated.",
        ]
        return result

    @staticmethod
    def _d4_status(chart: dict[str, Any]) -> str:
        d4 = chart.get("vargas", {}).get("D4") if isinstance(chart.get("vargas"), dict) else None
        return "D4_NOT_VALIDATED" if d4 else "D4_NOT_IMPLEMENTED_OR_UNAVAILABLE"

    @staticmethod
    def _evidence(source: str, claim: str, role: str, lineage: str) -> dict[str, Any]:
        return {"source_engine": source, "claim": claim, "role": role, "evidence_type": "DOMAIN_SYNTHESIS", "lineage_id": lineage, "authority_class": "RESEARCH_CANDIDATE"}


def build_property_benchmark() -> list[dict[str, Any]]:
    """Build deterministic property fixtures without benchmark-specific logic."""
    cases: list[dict[str, Any]] = []
    labels = ("acquisition", "ownership", "residence_stability", "residence_change", "comfort", "land", "constructed", "inheritance", "sale", "construction", "renovation", "expenditure", "debt", "dispute")
    for index in range(120):
        key = labels[index % len(labels)]
        scores = {key: ((index % 4) + 1) / 4}
        cases.append({"case_id": f"PROPERTY-{index + 1:03d}", "chart": {"property_scores": scores}, "expected": "PROPERTY_VS_RESIDENCE_SEPARATE" if key in {"ownership", "residence_stability", "residence_change"} else "NO_UNSUPPORTED_CERTAINTY"})
    return cases


def build_property_holdout() -> list[dict[str, Any]]:
    return [{"case_id": f"PROPERTY-HOLDOUT-{index + 1:03d}", "chart": {"property_scores": {"potential": (index % 3 + 1) / 3}}, "expected": "NO_UNSUPPORTED_CERTAINTY"} for index in range(40)]


__all__ = ["PropertySynthesis", "PropertySynthesisEngine", "build_property_benchmark", "build_property_holdout"]
