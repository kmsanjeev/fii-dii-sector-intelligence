"""VEDA-P031 spirituality, dharma and inner-development synthesis.

The engine consumes governed domain facts. It does not calculate astronomy,
diagnose mental health, or make deterministic claims about enlightenment,
liberation, sainthood, or formal renunciation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


STATES = {"STRONG", "MODERATE", "MIXED", "WEAK", "INSUFFICIENT_DATA"}
TIMING_STATES = {"NOT_ACTIVE", "SUPPORTIVE", "STRONGLY_SUPPORTIVE", "MIXED", "DELAYED", "CRISIS_WINDOW", "INSUFFICIENT_DATA"}
DIMENSIONS = (
    "dharma_orientation", "spiritual_inclination", "philosophical_orientation", "religious_orientation",
    "inner_development", "practice_orientation", "contemplation", "meditation_orientation", "higher_knowledge",
    "guru_orientation", "seva_service", "devotional_orientation", "occult_inquiry", "pilgrimage", "detachment", "renunciatory_tendency",
    "householder_spirituality", "solitude_retreat", "transformation", "spiritual_crisis", "material_spiritual_balance",
)


@dataclass(slots=True)
class SpiritualityDharmaSynthesis:
    domain: str = "SPIRITUALITY_DHARMA"
    subject_id: str | None = None
    source_state: str = "RESEARCH_CANDIDATE"
    birth_time_quality: str = "UNKNOWN"
    spiritual_interest: str = "INSUFFICIENT_DATA"
    belief_orientation: str = "INSUFFICIENT_DATA"
    study_orientation: str = "INSUFFICIENT_DATA"
    practice_discipline: str = "INSUFFICIENT_DATA"
    spiritual_experience: str = "INSUFFICIENT_DATA"
    dharma_orientation: str = "INSUFFICIENT_DATA"
    spiritual_inclination: str = "INSUFFICIENT_DATA"
    philosophical_orientation: str = "INSUFFICIENT_DATA"
    religious_orientation: str = "INSUFFICIENT_DATA"
    inner_development: str = "INSUFFICIENT_DATA"
    practice_orientation: str = "INSUFFICIENT_DATA"
    contemplation: str = "INSUFFICIENT_DATA"
    meditation_orientation: str = "INSUFFICIENT_DATA"
    higher_knowledge: str = "INSUFFICIENT_DATA"
    guru_orientation: str = "INSUFFICIENT_DATA"
    seva_service: str = "INSUFFICIENT_DATA"
    devotional_orientation: str = "INSUFFICIENT_DATA"
    occult_inquiry: str = "INSUFFICIENT_DATA"
    pilgrimage: str = "INSUFFICIENT_DATA"
    detachment: str = "INSUFFICIENT_DATA"
    renunciatory_tendency: str = "INSUFFICIENT_DATA"
    householder_spirituality: str = "INSUFFICIENT_DATA"
    solitude_retreat: str = "INSUFFICIENT_DATA"
    transformation: str = "INSUFFICIENT_DATA"
    spiritual_crisis: str = "INSUFFICIENT_DATA"
    material_spiritual_balance: str = "INSUFFICIENT_DATA"
    spiritual_modes: list[str] = field(default_factory=lambda: ["UNDETERMINED"])
    dominant_spiritual_scenario: str = "UNDETERMINED"
    alternative_scenarios: list[str] = field(default_factory=list)
    timing: str = "INSUFFICIENT_DATA"
    timing_window: str = "UNRESOLVED"
    conditions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    confidence: str = "VERY_LOW"
    missing_data: list[str] = field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = field(default_factory=list)
    opposing_evidence: list[dict[str, Any]] = field(default_factory=list)
    reasoning_trace: list[str] = field(default_factory=list)
    trust_state: str = "RESEARCH_CANDIDATE"
    safety_status: str = "NO_ENLIGHTENMENT_OR_CLINICAL_DIAGNOSIS"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _state(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "INSUFFICIENT_DATA"
    if value >= 0.75:
        return "STRONG"
    if value >= 0.5:
        return "MODERATE"
    if value >= 0.25:
        return "MIXED"
    return "WEAK"


def _score(scores: dict[str, Any], key: str) -> str:
    return _state(scores.get(key))


class SpiritualityDharmaSynthesisEngine:
    """Deterministic P031 synthesis over already-calculated governed facts."""

    def synthesize(self, chart: dict[str, Any] | None = None, *, subject_id: str | None = None) -> SpiritualityDharmaSynthesis:
        chart = chart or {}
        scores = chart.get("spiritual_scores") or {}
        result = SpiritualityDharmaSynthesis(subject_id=subject_id or chart.get("subject_id"), source_state=str(chart.get("source_state", "RESEARCH_CANDIDATE")))
        result.birth_time_quality = str(chart.get("birth_time_quality", "UNKNOWN")).upper()
        for name in ("spiritual_interest", "belief_orientation", "study_orientation", "practice_discipline", "spiritual_experience"):
            setattr(result, name, _score(scores, name))
        for name in DIMENSIONS:
            setattr(result, name, _score(scores, name))

        result.missing_data.extend(chart.get("missing_data") or [])
        if not chart.get("house_facts"):
            result.missing_data.append("HOUSE_EVIDENCE_NOT_SUPPLIED")
        result.missing_data.extend(self._varga_gaps(chart))
        if result.birth_time_quality == "UNKNOWN":
            result.missing_data.append("BIRTH_TIME_QUALITY_UNKNOWN")
        elif result.birth_time_quality in {"APPROXIMATE", "RANGE"}:
            result.missing_data.append("VARGA_BIRTH_TIME_SENSITIVITY")

        # Core distinctions are platform governance, not classical guarantees.
        interest = _score(scores, "spiritual_interest")
        practice = _score(scores, "practice_discipline")
        experience = _score(scores, "spiritual_experience")
        if interest in {"STRONG", "MODERATE"} and practice in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.conditions.append("Spiritual interest does not establish sustained practice or spiritual maturity.")
            result.alternatives.append("INTEREST_OR_STUDY_WITHOUT_ESTABLISHED_PRACTICE")
        if experience in {"STRONG", "MODERATE"}:
            result.conditions.append("Reported or supplied experience is not treated as enlightenment, moksha, or realization.")
        if result.religious_orientation in {"STRONG", "MODERATE"} and result.inner_development in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.conditions.append("Religious or ritual orientation is distinct from inner development.")
        if result.philosophical_orientation in {"STRONG", "MODERATE"} and result.practice_orientation in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.conditions.append("Philosophical interest is distinct from lived practice.")
        if result.occult_inquiry in {"STRONG", "MODERATE"}:
            result.conditions.append("Occult or hidden-subject interest is not equated with spiritual development or maturity.")
        if result.detachment in {"STRONG", "MODERATE"}:
            result.conditions.append("Detachment is not interpreted as depression, social failure, or relationship dysfunction.")
        if result.solitude_retreat in {"STRONG", "MODERATE"}:
            result.conditions.append("Solitude or retreat orientation is not interpreted as social failure or clinical withdrawal.")
        if result.pilgrimage in {"STRONG", "MODERATE"} and result.renunciatory_tendency in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.alternatives.append("PILGRIMAGE_OR_DEVOTION_WITHOUT_RENUNCIATION")
        if result.renunciatory_tendency in {"STRONG", "MODERATE"}:
            result.conditions.append("Renunciatory tendency does not establish formal sannyasa or actual renunciation.")
        if result.householder_spirituality in {"STRONG", "MODERATE"}:
            result.conditions.append("Spiritual development may be expressed through family, work, service, study, devotion, or ethical living.")
        if result.spiritual_crisis in {"STRONG", "MODERATE"}:
            result.conditions.append("Spiritual crisis means questioning or reorientation in this model; it is not a clinical diagnosis.")
        if result.dharma_orientation in {"STRONG", "MODERATE"} and result.religious_orientation in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.alternatives.append("DHARMA_OR_ETHICAL_PURPOSE_WITHOUT_INSTITUTIONAL_RELIGIOSITY")
        if result.spiritual_inclination in {"STRONG", "MODERATE"} and result.inner_development in {"WEAK", "MIXED", "INSUFFICIENT_DATA"}:
            result.contradictions.append("Spiritual inclination is stronger than demonstrated inner-development evidence.")
        if result.material_spiritual_balance == "STRONG":
            result.conditions.append("Material emphasis remains distinct from spiritual orientation; neither is treated as moral failure.")
        if (chart.get("pilgrimage_context") or {}).get("signal"):
            result.conditions.append("P030 pilgrimage context may describe travel or sacred movement; it does not establish spiritual maturity or renunciation.")
            result.alternatives.append("PILGRIMAGE_AS_TRAVEL_CONTEXT")
        if (chart.get("education_context") or {}).get("signal"):
            result.conditions.append("P023 education context may support study or higher-knowledge interpretation; it does not establish realization.")
            result.alternatives.append("EDUCATION_AS_HIGHER_KNOWLEDGE_CONTEXT")
        if result.spiritual_inclination in {"STRONG", "MODERATE"} and result.practice_discipline in {"STRONG", "MODERATE"}:
            result.dominant_spiritual_scenario = "PRACTICE_ORIENTED_DEVELOPMENT"
        elif result.study_orientation in {"STRONG", "MODERATE"}:
            result.dominant_spiritual_scenario = "STUDY_AND_HIGHER_KNOWLEDGE"
        elif result.devotional_orientation in {"STRONG", "MODERATE"}:
            result.dominant_spiritual_scenario = "DEVOTIONAL_ORIENTATION"
        elif result.householder_spirituality in {"STRONG", "MODERATE"}:
            result.dominant_spiritual_scenario = "HOUSEHOLDER_SPIRITUALITY"
        elif result.spiritual_inclination != "INSUFFICIENT_DATA":
            result.dominant_spiritual_scenario = "SPIRITUAL_INCLINATION"
        result.spiritual_modes = self._modes(result)
        result.alternative_scenarios = list(dict.fromkeys(result.alternatives))

        dasha = chart.get("dasha_activation")
        transit = chart.get("transit_trigger")
        has_structure = any(getattr(result, name) != "INSUFFICIENT_DATA" for name in DIMENSIONS)
        if not has_structure:
            result.timing = "INSUFFICIENT_DATA"
        elif dasha == "SUPPORTIVE" and transit == "SUPPORTIVE":
            result.timing = "CRISIS_WINDOW" if result.spiritual_crisis in {"STRONG", "MODERATE"} else "STRONGLY_SUPPORTIVE"
            result.timing_window = "DASHA_TRANSIT_CONVERGENCE"
        elif dasha == "SUPPORTIVE":
            result.timing = "SUPPORTIVE"
            result.timing_window = "DASHA_SUPPORT"
        elif transit == "DELAYED":
            result.timing = "DELAYED"
            result.timing_window = "TRANSIT_DELAY"
        elif transit == "STRESS" or result.spiritual_crisis in {"STRONG", "MODERATE"}:
            result.timing = "MIXED"
            result.timing_window = "QUESTIONING_OR_STRESS_WINDOW"
        else:
            result.timing = "NOT_ACTIVE"
            result.timing_window = "NO_GOVERNED_WINDOW"
            result.conditions.append("Spiritual potential is not treated as a timed event without governed Dasha/Transit support.")

        if result.timing in {"SUPPORTIVE", "STRONGLY_SUPPORTIVE", "CRISIS_WINDOW"}:
            result.supporting_evidence.append(self._evidence("P016_P019_CONVERGENCE", "Supplied Dasha/Transit timing context", "CONDITIONAL", "SPIRITUAL_TIMING"))
        if has_structure:
            result.supporting_evidence.append(self._evidence("P031_INPUT_FACTS", "Supplied spirituality-domain facts", "PRIMARY", "SPIRITUAL_STRUCTURE"))
        if result.contradictions:
            result.opposing_evidence.append(self._evidence("P031_CONTRADICTION", "Conflicting spiritual dimensions retained", "OPPOSING", "SPIRITUAL_CONTRADICTION"))

        result.confidence = "MODERATE" if result.timing in {"SUPPORTIVE", "STRONGLY_SUPPORTIVE", "CRISIS_WINDOW"} and not result.contradictions and not result.missing_data else "LOW_TO_MODERATE" if has_structure else "VERY_LOW"
        result.reasoning_trace = [
            "Existing governed chart/domain facts are consumed; astronomy is not recalculated.",
            "Dharma, religiosity, interest, practice, experience, detachment, solitude, pilgrimage, and renunciation remain separate dimensions.",
            "Householder spirituality is supported as a valid alternative to renunciation.",
            "Spiritual potential precedes Dasha/Transit timing refinement.",
            "D20 calculation availability does not authorize D20 spiritual interpretation.",
            "No enlightenment, moksha, sainthood, formal-renunciation, or clinical diagnosis claim is generated.",
        ]
        return result

    @staticmethod
    def _modes(result: SpiritualityDharmaSynthesis) -> list[str]:
        modes: list[str] = []
        if result.devotional_orientation in {"STRONG", "MODERATE"}:
            modes.append("DEVOTIONAL")
        if result.philosophical_orientation in {"STRONG", "MODERATE"} or result.study_orientation in {"STRONG", "MODERATE"}:
            modes.append("PHILOSOPHICAL")
        if result.contemplation in {"STRONG", "MODERATE"} or result.meditation_orientation in {"STRONG", "MODERATE"}:
            modes.append("CONTEMPLATIVE")
        if result.religious_orientation in {"STRONG", "MODERATE"}:
            modes.append("RITUAL")
        if result.seva_service in {"STRONG", "MODERATE"}:
            modes.append("SERVICE")
        if result.renunciatory_tendency in {"STRONG", "MODERATE"}:
            modes.append("ASCETIC")
        if result.transformation in {"STRONG", "MODERATE"}:
            modes.append("MYSTICAL")
        if result.occult_inquiry in {"STRONG", "MODERATE"}:
            modes.append("OCCULT_INQUIRY")
        return modes or ["UNDETERMINED"]

    @staticmethod
    def _varga_gaps(chart: dict[str, Any]) -> list[str]:
        metadata = chart.get("varga_metadata") or {}
        d20 = metadata.get("D20") or {}
        gaps = ["D20_INTERPRETATION_NOT_VALIDATED"] if d20.get("calculation_status") in {"VALIDATED", "AVAILABLE", "IMPLEMENTED"} else ["D20_NOT_AVAILABLE_OR_NOT_VALIDATED"]
        for varga in ("D9", "D12"):
            if varga not in metadata:
                gaps.append(f"{varga}_SPIRITUAL_INTERPRETATION_NOT_VALIDATED")
        return gaps

    @staticmethod
    def _evidence(source: str, claim: str, role: str, lineage: str) -> dict[str, Any]:
        return {"source_engine": source, "claim": claim, "role": role, "evidence_type": "DOMAIN_SYNTHESIS", "lineage_id": lineage, "authority_class": "RESEARCH_CANDIDATE"}


__all__ = ["SpiritualityDharmaSynthesis", "SpiritualityDharmaSynthesisEngine"]
