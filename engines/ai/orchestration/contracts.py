"""Structured handoff contracts for VEDA-STD-002 agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class AgentRole(StrEnum):
    ORCHESTRATOR = "ORCHESTRATOR"
    RESEARCH = "RESEARCH"
    INGESTION = "INGESTION"
    VALIDATION = "VALIDATION"
    JYOTISHA_REASONING = "JYOTISHA_REASONING"
    INTUITION_PATTERN = "INTUITION_PATTERN"
    PREDICTION = "PREDICTION"
    OUTCOME_BACKTESTING = "OUTCOME_BACKTESTING"
    RESPONSE = "RESPONSE"


class ReasoningLayer(StrEnum):
    DETERMINISTIC_FACT = "DETERMINISTIC_FACT"
    CLASSICAL = "CLASSICAL"
    INTUITIVE_EMPIRICAL = "INTUITIVE_EMPIRICAL"


class EvidenceType(StrEnum):
    DETERMINISTIC_FACT = "DETERMINISTIC_FACT"
    CLASSICAL_SUPPORT = "CLASSICAL_SUPPORT"
    CLASSICAL_OPPOSITION = "CLASSICAL_OPPOSITION"
    CLASSICAL_CONDITIONAL = "CLASSICAL_CONDITIONAL"
    CLASSICAL_CANCELLATION = "CLASSICAL_CANCELLATION"
    EXPERT_REASONING_SUPPORT = "EXPERT_REASONING_SUPPORT"
    EMPIRICAL_SUPPORT = "EMPIRICAL_SUPPORT"
    ML_SUPPORT = "ML_SUPPORT"
    TIMING_SUPPORT = "TIMING_SUPPORT"
    TIMING_OPPOSITION = "TIMING_OPPOSITION"
    UNVALIDATED_SIGNAL = "UNVALIDATED_SIGNAL"
    CONFLICT = "CONFLICT"


@dataclass(slots=True)
class ReasoningEvidence:
    evidence_id: str
    evidence_type: EvidenceType
    layer: ReasoningLayer
    claim: str
    domain: str | None = None
    trust_zone: str = "RESEARCH_CANDIDATE"
    validation_state: str = "RESEARCH_REQUIRED"
    source_ids: list[str] = field(default_factory=list)
    rule_ids: list[str] = field(default_factory=list)
    method_variant: str | None = None
    confidence_state: str = "INSUFFICIENT_SAMPLE"
    evidence_family: str | None = None
    underlying_fact: str | None = None
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_type"] = self.evidence_type.value
        value["layer"] = self.layer.value
        return value


@dataclass(slots=True)
class RequestContext:
    request_id: str
    subject_id: str | None = None
    domain: str | None = None
    query: str = ""
    mode: str = "PRODUCTION_SAFE"
    trust_constraints: dict[str, Any] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    evidence_ids: list[str] = field(default_factory=list)
    rule_ids: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    prediction_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dependency_states: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentContext:
    context_type: str
    request: RequestContext
    payload: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    dependency_states: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["request"] = self.request.to_dict()
        return value


def make_context(context_type: str, request: RequestContext, **payload: Any) -> AgentContext:
    """Create a typed-by-name handoff without passing opaque prose."""
    return AgentContext(context_type=context_type, request=request, payload=payload)


__all__ = [
    "AgentContext",
    "AgentRole",
    "EvidenceType",
    "ReasoningEvidence",
    "ReasoningLayer",
    "RequestContext",
    "make_context",
]
