"""P024 marriage synthesis engine.

The engine builds shadow / experimental relationship synthesis from governed
evidence layers. It never turns a single placement into a certainty and it
keeps D1, D9, Dasha, Yoga/Dosha, strength, and transit context distinct.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from engines.intelligence.marriage_evidence_aggregation import (
    ConfidenceBand,
    EvidenceDirection,
    MarriageEvidenceAggregator,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stamp(value: str | None = None) -> str:
    return value or _utc_now()


@dataclass(slots=True)
class MarriagePredictionRecord:
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
    method_version: str = "P024_SHADOW_1"
    rule_versions: list[str] = field(default_factory=list)
    confidence_state: str = "RESEARCH_REQUIRED"
    actual_outcome: str | None = None
    outcome_recorded_at: str | None = None
    comparison_result: str | None = None
    notes: str | None = None

    def record_outcome(self, actual_outcome: str, *, outcome_recorded_at: str | None = None) -> None:
        self.actual_outcome = actual_outcome
        self.outcome_recorded_at = _stamp(outcome_recorded_at)
        self.comparison_result = "MATCH" if actual_outcome == self.prediction_state else "MISMATCH"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MarriageSynthesisOutput:
    synthesis_id: str
    subject_id: str | None
    created_at: str
    domain: str = "MARRIAGE"
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
    d9_context: dict[str, Any] = field(default_factory=dict)
    dasha_context: dict[str, Any] = field(default_factory=dict)
    yoga_dosha_context: dict[str, Any] = field(default_factory=dict)
    strength_context: dict[str, Any] = field(default_factory=dict)
    transit_context: dict[str, Any] = field(default_factory=dict)
    key_factors: list[str] = field(default_factory=list)
    explainability_trace: list[str] = field(default_factory=list)
    experimental: bool = True
    shadow: bool = True
    backtesting_ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarriageSynthesisEngine:
    """Shadow-first marriage synthesis engine."""

    def __init__(self) -> None:
        self.aggregator = MarriageEvidenceAggregator()

    def _add_context_evidence(
        self,
        *,
        facts: dict[str, Any],
        source_layer: str,
        claim: str,
        direction: EvidenceDirection,
        evidence_type: str,
        method_variant: str,
        confidence: ConfidenceBand = ConfidenceBand.MODERATE,
        rule_id: str | None = None,
        source_id: str | None = None,
        passage_id: str | None = None,
        source_class: str | None = None,
        source_family: str | None = None,
        notes: str = "",
    ) -> None:
        self.aggregator.add_evidence(
            source_layer=source_layer,
            evidence_type=evidence_type,
            direction=direction,
            claim=claim,
            basis=facts,
            confidence=confidence,
            validation_state=facts.get("validation_state", "RESEARCH_REQUIRED"),
            provisional=bool(facts.get("provisional", True)),
            notes=notes,
            rule_id=rule_id,
            source_id=source_id,
            passage_id=passage_id,
            source_class=source_class,
            source_family=source_family,
            retrieval_status=facts.get("retrieval_status", "REFERENCE_NOT_VERIFIED"),
            citation_status=facts.get("citation_status", "REFERENCE_NOT_VERIFIED"),
            method_variant=method_variant,
        )

    def _populate_evidence(
        self,
        natal_factors: dict[str, Any],
        d9_facts: dict[str, Any],
        dasha_context: dict[str, Any],
        transit_context: dict[str, Any],
        yoga_facts: dict[str, Any],
        strength_facts: dict[str, Any],
    ) -> None:
        if natal_factors:
            self._add_context_evidence(
                facts=natal_factors,
                source_layer="D1",
                claim="Marriage synthesis begins with natal D1 structure and the 7th-house relationship field.",
                direction=EvidenceDirection.SUPPORTING,
                evidence_type="NATAL",
                method_variant="D1_NATAL_RELATIONSHIP_BASELINE",
                confidence=ConfidenceBand.HIGH if natal_factors.get("seventh_house") or natal_factors.get("seventh_lord") else ConfidenceBand.MODERATE,
                rule_id="VEDA-RUL-P024-NATAL-001",
                source_id="VEDA-PSG-000011",
                passage_id="VEDA-PSG-000011",
                source_class="TRADITIONAL_SECONDARY",
                source_family="B V Raman",
                notes="D1 carries the natal base; no single placement determines the outcome.",
            )
        if d9_facts:
            direction = EvidenceDirection.SUPPORTING if d9_facts.get("d1_d9_alignment", True) else EvidenceDirection.CONDITIONAL
            self._add_context_evidence(
                facts=d9_facts,
                source_layer="D9",
                claim="D9 refines marriage context; it does not replace the D1 foundation.",
                direction=direction,
                evidence_type="VARGA",
                method_variant="D1_D9_BOUNDED_SPECIALIZATION",
                confidence=ConfidenceBand.MODERATE,
                rule_id="VEDA-RUL-P024-D9-001",
                source_id="VEDA-REL-000019",
                passage_id="REFERENCE_NOT_VERIFIED",
                source_class="GOVERNED_RESEARCH",
                source_family="P015/P024",
                notes="D9 interpretation remains research-labelled unless explicitly promoted later.",
            )
        if yoga_facts:
            direction = EvidenceDirection.CANCELLING if yoga_facts.get("cancellation_present") else EvidenceDirection.CONDITIONAL
            self._add_context_evidence(
                facts=yoga_facts,
                source_layer="YOGA_DOSHA",
                claim="Marriage yogas and doshas contribute context, and cancellations or modifications must be preserved.",
                direction=direction,
                evidence_type="YOGA_DOSHA",
                method_variant="SCHOOL_VARIANT_PRESERVATION",
                confidence=ConfidenceBand.MODERATE,
                rule_id="VEDA-RUL-P024-YOGA-001",
                source_id="VEDA-RUL-DOSHA-000001" if yoga_facts.get("manglik_present") else "VEDA-RUL-CANCEL-000001",
                passage_id="REFERENCE_NOT_VERIFIED",
                source_class="GOVERNED_RESEARCH",
                source_family="P017",
                notes="Dosha assessment is incomplete without the tradition-specific cancellation framework.",
            )
        if dasha_context:
            direction = EvidenceDirection.SUPPORTING if dasha_context.get("relationship_window") else EvidenceDirection.CONDITIONAL
            self._add_context_evidence(
                facts=dasha_context,
                source_layer="DASHA",
                claim="Dasha timing can open relationship or marriage windows, but only as an experimental windowing signal.",
                direction=direction,
                evidence_type="TIMING",
                method_variant="TIMING_WINDOW_HYPOTHESIS",
                confidence=ConfidenceBand.MODERATE if dasha_context.get("relationship_window") else ConfidenceBand.LOW,
                rule_id="VEDA-RUL-P024-DASHA-001",
                source_id="VEDA-PSG-000006",
                passage_id="VEDA-PSG-000006",
                source_class="CLASSICAL_PRIMARY",
                source_family="Varahamihira",
                notes="Dasha interpretation uses planetary qualities, house placement, aspect, and yoga together.",
            )
        if transit_context:
            direction = EvidenceDirection.OPPOSING if transit_context.get("challenge") else EvidenceDirection.CONDITIONAL
            self._add_context_evidence(
                facts=transit_context,
                source_layer="TRANSIT",
                claim="Transit is contextual timing only and can oppose or sharpen a marriage window, but cannot override the core foundation.",
                direction=direction,
                evidence_type="TIMING",
                method_variant="GOCHAR_CONTEXT_ONLY",
                confidence=ConfidenceBand.LOW if transit_context.get("challenge") else ConfidenceBand.MODERATE,
                rule_id="VEDA-RUL-P024-TRANSIT-001",
                source_id="VEDA-PSG-000013",
                passage_id="VEDA-PSG-000013",
                source_class="REFERENCE_EDITION",
                source_family="Wisdom Library",
                notes="Transit remains research-stage context; it is not upgraded into certainty.",
            )
        if strength_facts:
            direction = EvidenceDirection.CONDITIONAL if strength_facts.get("validated") else EvidenceDirection.RESEARCH_ONLY
            self._add_context_evidence(
                facts=strength_facts,
                source_layer="STRENGTH",
                claim="Strength systems may modulate confidence, but unvalidated strength must remain clearly labelled.",
                direction=direction,
                evidence_type="STRENGTH",
                method_variant="UNVALIDATED_STRENGTH_PROPAGATION",
                confidence=ConfidenceBand.LOW,
                rule_id="VEDA-RUL-P024-STRENGTH-001",
                source_id="VEDA-P018-R1-11_SHADBALA_AGGREGATION.md",
                passage_id="REFERENCE_NOT_VERIFIED",
                source_class="GOVERNED_RESEARCH",
                source_family="P018/P018-R1",
                notes="Strength outputs are not silently treated as authoritative unless a later phase validates them.",
            )
        if self.aggregator.evidence_records and not any(record.direction == EvidenceDirection.BLOCKED_DEPENDENCY for record in self.aggregator.evidence_records):
            self._add_context_evidence(
                facts={"dependency_state": "open"},
                source_layer="DEPENDENCY",
                claim="Dependency completeness is tracked explicitly so blocked evidence is visible in explainability traces.",
                direction=EvidenceDirection.RESEARCH_ONLY,
                evidence_type="CONTRACT",
                method_variant="DEPENDENCY_TRANSPARENCY",
                confidence=ConfidenceBand.MODERATE,
                rule_id="VEDA-RUL-P024-BLOCK-001",
                source_id="VEDA-P020-02_EVIDENCE_AND_CONFLICTS.md",
                passage_id="REFERENCE_NOT_VERIFIED",
                source_class="GOVERNED_RESEARCH",
                source_family="P020",
                notes="The synthesis chain preserves blocked and conflicting evidence separately.",
            )

    def synthesize(
        self,
        *,
        subject_id: str | None = None,
        natal_factors: dict[str, Any] | None = None,
        d9_facts: dict[str, Any] | None = None,
        dasha_context: dict[str, Any] | None = None,
        transit_context: dict[str, Any] | None = None,
        yoga_facts: dict[str, Any] | None = None,
        strength_facts: dict[str, Any] | None = None,
        prediction_mode: str = "RESEARCH_ONLY",
    ) -> MarriageSynthesisOutput:
        self.aggregator = MarriageEvidenceAggregator()
        self._populate_evidence(
            natal_factors or {},
            d9_facts or {},
            dasha_context or {},
            transit_context or {},
            yoga_facts or {},
            strength_facts or {},
        )
        self.aggregator.detect_conflicts()
        synthesis = self.aggregator.synthesize_narrative()
        evidence_rows = self.aggregator.to_dict()["evidence_records"]

        supporting = [row for row in evidence_rows if row["direction"] == EvidenceDirection.SUPPORTING.value]
        opposing = [row for row in evidence_rows if row["direction"] == EvidenceDirection.OPPOSING.value]
        conditional = [row for row in evidence_rows if row["direction"] == EvidenceDirection.CONDITIONAL.value]
        cancelling = [row for row in evidence_rows if row["direction"] == EvidenceDirection.CANCELLING.value]
        experimental = [row for row in evidence_rows if row["direction"] == EvidenceDirection.EXPERIMENTAL.value]
        blocked = [row for row in evidence_rows if row["direction"] == EvidenceDirection.BLOCKED_DEPENDENCY.value]

        key_factors = [
            row["claim"]
            for row in supporting[:3]
        ]
        if not key_factors and conditional:
            key_factors = [conditional[0]["claim"]]

        explainability_trace = [
            "MARRIAGE SYNTHESIS",
            f"overall_state={synthesis['overall_state']}",
            f"supporting={synthesis['supporting_count']}",
            f"opposing={synthesis['opposing_count']}",
            f"conditional={synthesis['conditional_count']}",
            f"cancelling={synthesis['cancelling_count']}",
            f"blocked_dependencies={synthesis['blocked_dependency_count']}",
            "TRACE: D1 -> D9 -> Dasha -> Yoga/Dosha -> Strength -> Transit",
            "TRACE: claims -> passages -> sources",
        ]

        output = MarriageSynthesisOutput(
            synthesis_id=f"MRG_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            subject_id=subject_id,
            created_at=_utc_now(),
            prediction_mode=prediction_mode,
            prediction_state=prediction_mode,
            overall_state=synthesis["overall_state"],
            confidence_summary=synthesis["overall_confidence"],
            interpretation_status="SHADOW_ONLY" if prediction_mode != "RESEARCH_ONLY" else "RESEARCH_ONLY",
            supporting_evidence=supporting,
            opposing_evidence=opposing,
            conditional_evidence=conditional,
            cancelling_evidence=cancelling,
            experimental_evidence=experimental,
            blocked_dependencies=blocked,
            d1_context=natal_factors or {},
            d9_context=d9_facts or {},
            dasha_context=dasha_context or {},
            yoga_dosha_context=yoga_facts or {},
            strength_context=strength_facts or {},
            transit_context=transit_context or {},
            key_factors=key_factors,
            explainability_trace=explainability_trace,
            experimental=prediction_mode in {"EXPERIMENTAL", "SHADOW"},
            shadow=prediction_mode == "SHADOW",
            backtesting_ready=True,
        )
        return output

    def create_prediction_record(
        self,
        *,
        prediction_type: str,
        prediction_state: str,
        window_start: str,
        window_end: str,
        confidence_state: str,
        method_version: str = "P024_SHADOW_1",
        rule_versions: list[str] | None = None,
        supporting_evidence: list[dict[str, Any]] | None = None,
        opposing_evidence: list[dict[str, Any]] | None = None,
        cancelling_evidence: list[dict[str, Any]] | None = None,
    ) -> MarriagePredictionRecord:
        return MarriagePredictionRecord(
            prediction_id=f"P024-MRG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            domain="MARRIAGE",
            created_at=_utc_now(),
            window_start=window_start,
            window_end=window_end,
            prediction_type=prediction_type,
            prediction_state=prediction_state,
            supporting_evidence=supporting_evidence or [],
            opposing_evidence=opposing_evidence or [],
            cancelling_evidence=cancelling_evidence or [],
            method_version=method_version,
            rule_versions=rule_versions or [],
            confidence_state=confidence_state,
        )


__all__ = [
    "MarriagePredictionRecord",
    "MarriageSynthesisEngine",
    "MarriageSynthesisOutput",
]
