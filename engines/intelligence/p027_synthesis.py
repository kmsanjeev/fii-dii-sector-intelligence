"""P027 governed evidence synthesis and multi-chart reasoning.

This module consumes evidence emitted by existing Jyotisha engines. It does
not recalculate chart facts, rules, Vargas, Dashas, or transits.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Iterable


class EvidenceRole(StrEnum):
    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"
    MODIFYING = "MODIFYING"
    CONDITIONAL = "CONDITIONAL"
    TIMING = "TIMING"
    OPPOSING = "OPPOSING"
    REDUNDANT = "REDUNDANT"
    WEAK = "WEAK"
    EXPERIMENTAL = "EXPERIMENTAL"


class ContradictionSeverity(StrEnum):
    NONE = "NO_CONTRADICTION"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    UNRESOLVED = "UNRESOLVED"


class ConfidenceBand(StrEnum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass(slots=True)
class SynthesisEvidence:
    evidence_id: str
    claim: str
    source_engine: str = "UNKNOWN"
    source_phase: str | None = None
    chart_id: str | None = None
    subject_id: str | None = None
    chart_type: str | None = None
    domain: str | None = None
    evidence_type: str = "CONTEXT"
    factor: str | None = None
    rule_id: str | None = None
    rule_family: str | None = None
    direction: str = "SUPPORTS"
    strength: str = "MODERATE"
    confidence: str = "MODERATE"
    authority_class: str = "RESEARCH_CANDIDATE"
    knowledge_zone: str = "RESEARCH_CANDIDATE"
    role: EvidenceRole | None = None
    supports: str | None = None
    opposes: str | None = None
    modifies: str | None = None
    conditions: list[str] = field(default_factory=list)
    times: list[str] = field(default_factory=list)
    time_scope: str | None = None
    lineage_id: str | None = None
    duplicates: list[str] = field(default_factory=list)
    method_variant: str | None = None
    validation_state: str = "UNKNOWN"
    citations: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "SynthesisEvidence":
        values = dict(row)
        role = values.get("role")
        values["role"] = EvidenceRole(role) if role in EvidenceRole._value2member_map_ else None
        values.setdefault("evidence_id", f"evidence-{len(values)}")
        values.setdefault("claim", "Unspecified evidence")
        return cls(**{key: value for key, value in values.items() if key in cls.__dataclass_fields__})

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["role"] = self.role.value if self.role else None
        return value


@dataclass(slots=True)
class Contradiction:
    evidence_a: str
    evidence_b: str
    reason: str
    severity: ContradictionSeverity
    resolution: str = "UNRESOLVED"
    relative_authority: str = "UNKNOWN"


@dataclass(slots=True)
class TimingSynthesis:
    structural_promise: str = "UNKNOWN"
    dasha: list[str] = field(default_factory=list)
    sub_dasha: list[str] = field(default_factory=list)
    transit: list[str] = field(default_factory=list)
    varga_confirmation: list[str] = field(default_factory=list)
    primary_window: str | None = None
    alternative_window: str | None = None
    timing_conflict: bool = False
    confidence: ConfidenceBand = ConfidenceBand.VERY_LOW


@dataclass(slots=True)
class SynthesisResult:
    question: str
    domain: str | None
    dominant_conclusion: str
    dominant_factors: list[dict[str, Any]]
    supporting_evidence: list[str]
    opposing_evidence: list[str]
    modifying_evidence: list[str]
    conditional_evidence: list[str]
    timing_evidence: list[str]
    redundant_evidence: list[str]
    weak_evidence: list[str]
    alternatives: list[str]
    conditions: list[str]
    contradictions: list[Contradiction]
    contradiction_state: ContradictionSeverity
    convergence_state: str
    confidence: ConfidenceBand
    trust_state: str
    timing: TimingSynthesis
    chart_attribution: dict[str, str]
    reasoning_trace: list[str]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contradiction_state"] = self.contradiction_state.value
        value["confidence"] = self.confidence.value
        value["timing"]["confidence"] = self.timing.confidence.value
        return value


_AUTHORITY = {"APPROVED_CORE": 5, "VALIDATED_KNOWLEDGE": 4, "PLATFORM_EVIDENCE": 3, "RESEARCH_CANDIDATE": 2, "EXPERIMENTAL": 1}
_STRENGTH = {"VERY_HIGH": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1, "UNKNOWN": 0}
_TIMING_TYPES = {"DASHA", "SUB_DASHA", "TRANSIT", "TIMING", "ASHTAKAVARGA"}


def _rank(item: SynthesisEvidence) -> tuple[int, int, int]:
    return (_AUTHORITY.get(item.authority_class, 0), _STRENGTH.get(item.strength, 0), 1 if item.validation_state in {"VALIDATED", "VALIDATED_KNOWLEDGE"} else 0)


def _is_timing(item: SynthesisEvidence) -> bool:
    return item.evidence_type.upper() in _TIMING_TYPES or (item.source_phase or "").upper() in _TIMING_TYPES


def _confidence(rows: list[SynthesisEvidence], contradiction: ContradictionSeverity, *, missing: bool = False) -> ConfidenceBand:
    if not rows or missing:
        return ConfidenceBand.VERY_LOW
    families = {row.lineage_id or row.rule_family or row.factor or row.evidence_id for row in rows}
    authority = max(_AUTHORITY.get(row.authority_class, 0) for row in rows)
    if contradiction in {ContradictionSeverity.STRONG, ContradictionSeverity.UNRESOLVED}:
        return ConfidenceBand.LOW
    if contradiction == ContradictionSeverity.MODERATE:
        return ConfidenceBand.MODERATE if len(families) > 1 else ConfidenceBand.LOW
    if authority >= 5 and len(families) >= 3:
        return ConfidenceBand.VERY_HIGH
    if authority >= 4 and len(families) >= 2:
        return ConfidenceBand.HIGH
    return ConfidenceBand.MODERATE if len(families) > 1 else ConfidenceBand.LOW


class P027SynthesisEngine:
    """Deterministic cross-engine synthesis; existing engines remain factual owners."""

    method_version = "P027_SYNTHESIS_1"

    def synthesize(self, question: str, evidence: Iterable[SynthesisEvidence | dict[str, Any]], *, domain: str | None = None, mode: str = "PRODUCTION_SAFE", missing_data: Iterable[str] = (), birth_time_precision: str = "EXACT") -> SynthesisResult:
        rows = [item if isinstance(item, SynthesisEvidence) else SynthesisEvidence.from_dict(item) for item in evidence]
        missing = list(missing_data)
        if mode == "PRODUCTION_SAFE":
            rows = [row for row in rows if row.knowledge_zone not in {"EXPERIMENTAL", "RESEARCH_ARCHIVE"} and row.evidence_type != "ML_SIGNAL"]
        for row in rows:
            if row.role is None:
                if _is_timing(row):
                    row.role = EvidenceRole.TIMING
                elif row.direction.upper() in {"OPPOSES", "OPPOSING", "NEGATIVE"}:
                    row.role = EvidenceRole.OPPOSING
                elif row.direction.upper() in {"MODIFIES", "MODIFYING"}:
                    row.role = EvidenceRole.MODIFYING
                elif row.conditions:
                    row.role = EvidenceRole.CONDITIONAL
                elif row.authority_class in {"EXPERIMENTAL", "RESEARCH_CANDIDATE"}:
                    row.role = EvidenceRole.WEAK
                else:
                    row.role = EvidenceRole.PRIMARY if row.evidence_type.upper() in {"STRUCTURAL", "DIGNITY", "LORDSHIP", "BHAVA", "NATAL"} else EvidenceRole.SUPPORTING
        by_lineage: dict[str, list[SynthesisEvidence]] = {}
        for row in rows:
            by_lineage.setdefault(row.lineage_id or row.rule_family or row.factor or row.evidence_id, []).append(row)
        redundant_ids: list[str] = []
        for cluster in by_lineage.values():
            if len(cluster) > 1:
                strongest = max(cluster, key=_rank)
                for row in cluster:
                    if row is not strongest and row.role not in {EvidenceRole.OPPOSING, EvidenceRole.MODIFYING}:
                        row.role = EvidenceRole.REDUNDANT
                        strongest.duplicates.append(row.evidence_id)
                        redundant_ids.append(row.evidence_id)
        positives = [row for row in rows if row.role in {EvidenceRole.PRIMARY, EvidenceRole.SUPPORTING}]
        negatives = [row for row in rows if row.role == EvidenceRole.OPPOSING]
        contradictions: list[Contradiction] = []
        for positive in positives:
            for negative in negatives:
                if positive.supports and negative.opposes and positive.supports != negative.opposes:
                    continue
                severity = ContradictionSeverity.MODERATE if _rank(positive) == _rank(negative) else ContradictionSeverity.MINOR
                winner = max((positive, negative), key=_rank)
                resolution = f"{winner.evidence_id} has higher governed authority/strength" if _rank(positive) != _rank(negative) else "UNRESOLVED"
                contradictions.append(Contradiction(positive.evidence_id, negative.evidence_id, "opposing directional evidence", severity, resolution, winner.evidence_id if resolution != "UNRESOLVED" else "EQUAL"))
        contradiction_state = max((item.severity for item in contradictions), default=ContradictionSeverity.NONE, key=lambda x: list(ContradictionSeverity).index(x))
        families = {row.lineage_id or row.rule_family or row.factor or row.evidence_id for row in positives}
        convergence = "STRONG_CONVERGENCE" if len(families) >= 3 and not contradictions else "MODERATE_CONVERGENCE" if len(families) >= 2 and not contradictions else "MIXED" if contradictions else "WEAK"
        dominant = sorted(positives, key=_rank, reverse=True)[:3]
        conclusion = dominant[0].claim if dominant else "Insufficient governed evidence for a dominant conclusion."
        timing_rows = [row for row in rows if row.role == EvidenceRole.TIMING]
        structural = [row for row in rows if row.role in {EvidenceRole.PRIMARY, EvidenceRole.SUPPORTING, EvidenceRole.CONDITIONAL} and not _is_timing(row)]
        timing_conflict = bool([row for row in timing_rows if row.direction.upper() in {"OPPOSES", "OPPOSING", "NEGATIVE"}]) and bool([row for row in timing_rows if row.direction.upper() in {"SUPPORTS", "SUPPORTING", "POSITIVE"}])
        timing = TimingSynthesis("SUPPORTED" if structural else "UNKNOWN", [r.claim for r in timing_rows if (r.source_phase or r.evidence_type).upper() == "DASHA"], [r.claim for r in timing_rows if (r.source_phase or r.evidence_type).upper() == "SUB_DASHA"], [r.claim for r in timing_rows if (r.source_phase or r.evidence_type).upper() == "TRANSIT"], [r.claim for r in rows if r.evidence_type.upper() == "VARGA"], timing_rows[0].time_scope if timing_rows else None, timing_rows[1].time_scope if len(timing_rows) > 1 else None, timing_conflict, ConfidenceBand.LOW if timing_conflict else _confidence(timing_rows, ContradictionSeverity.NONE))
        confidence = _confidence(positives, contradiction_state, missing=bool(missing) or birth_time_precision in {"RANGE", "UNKNOWN"})
        trust = "CLASSICAL_CORE_PRESERVED" if all(row.authority_class != "EXPERIMENTAL" for row in rows) else "MIXED_TRUST_EXPERIMENTAL_LABELED"
        charts = {row.chart_id: row.subject_id or "UNKNOWN" for row in rows if row.chart_id}
        alternatives = sorted({condition for row in rows for condition in row.conditions if condition})
        trace = [f"{self.method_version}: accepted {len(rows)} existing evidence records", f"independent lineages={len(families)}; convergence={convergence}", f"promise rows={len(structural)}; timing rows={len(timing_rows)}", f"contradictions={len(contradictions)}; confidence={confidence.value}"]
        if missing:
            trace.append("missing data preserved: " + ", ".join(missing))
        return SynthesisResult(question, domain, conclusion, [{"evidence_id": row.evidence_id, "role": row.role.value, "claim": row.claim, "rank": _rank(row)} for row in dominant], [r.evidence_id for r in positives], [r.evidence_id for r in negatives], [r.evidence_id for r in rows if r.role == EvidenceRole.MODIFYING], [r.evidence_id for r in rows if r.role == EvidenceRole.CONDITIONAL], [r.evidence_id for r in timing_rows], redundant_ids, [r.evidence_id for r in rows if r.role == EvidenceRole.WEAK], alternatives, [condition for r in rows for condition in r.conditions], contradictions, contradiction_state, convergence, confidence, trust, timing, charts, trace)

    def compare_charts(self, chart_a: dict[str, Any], chart_b: dict[str, Any], *, subject_a: str, subject_b: str, relationship_type: str, comparison_domain: str) -> dict[str, Any]:
        """Return a safe comparative contract without pretending to implement compatibility."""
        return {"chart_a": chart_a.get("chart_id"), "chart_b": chart_b.get("chart_id"), "subject_a": subject_a, "subject_b": subject_b, "relationship_type": relationship_type, "comparison_domain": comparison_domain, "evidence": [], "state": "FOUNDATIONAL_COMPARISON_ONLY", "warning": "Compatibility-specific classical methods are not implemented by P027."}


__all__ = ["ConfidenceBand", "Contradiction", "ContradictionSeverity", "EvidenceRole", "P027SynthesisEngine", "SynthesisEvidence", "SynthesisResult", "TimingSynthesis"]
