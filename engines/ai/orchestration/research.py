"""Explicit, conservative research escalation and document/case ingestion adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engines.ai.knowledge.knowledge_lifecycle import DocumentLearningService

from .patterns import EmpiricalPattern, ExpertReasoningPattern


@dataclass(frozen=True, slots=True)
class ResearchEscalationDecision:
    required: bool
    reason: str
    explicit_request: bool = False
    knowledge_gap: bool = False
    unresolved_conflict: bool = False
    service_invoked: bool = False


def decide_research_escalation(*, explicit_request: bool = False, retrieved_count: int = 0, unresolved_conflict: bool = False) -> ResearchEscalationDecision:
    gap = retrieved_count == 0
    required = explicit_request or gap or unresolved_conflict
    reason = "EXPLICIT_RESEARCH_REQUEST" if explicit_request else "UNRESOLVED_CONFLICT" if unresolved_conflict else "KNOWLEDGE_COVERAGE_INSUFFICIENT" if gap else "NO_ESCALATION"
    return ResearchEscalationDecision(required, reason, explicit_request, gap, unresolved_conflict, False)


@dataclass(slots=True)
class IngestedCase:
    document_id: str
    claims: list[dict[str, Any]] = field(default_factory=list)
    expert_patterns: list[ExpertReasoningPattern] = field(default_factory=list)
    empirical_patterns: list[EmpiricalPattern] = field(default_factory=list)


class DocumentCaseIngestionRunner:
    """Reuse STD-001 ingestion; optional structured fields create research records."""

    def __init__(self, learning_service: DocumentLearningService | None = None) -> None:
        self.learning_service = learning_service or DocumentLearningService()

    def ingest(self, path: str | Path, *, domain: str = "RESEARCH", reasoning_sequence: list[str] | None = None, author: str = "UNKNOWN", outcome: str | None = None, case_source: str | None = None) -> IngestedCase:
        document = self.learning_service.register_document(path, domain=domain)
        expert_patterns: list[ExpertReasoningPattern] = []
        empirical_patterns: list[EmpiricalPattern] = []
        if reasoning_sequence:
            expert_patterns.append(ExpertReasoningPattern(pattern_id=f"{document.document_id}:EXPERT:1", author=author, source_id=document.document_id, domain=domain.upper(), factors=tuple(reasoning_sequence), reasoning_sequence=tuple(reasoning_sequence)))
        if outcome is not None:
            empirical_patterns.append(EmpiricalPattern(pattern_id=f"{document.document_id}:EMPIRICAL:1", dataset_source=case_source or document.document_id, sample_size=1, features=tuple(reasoning_sequence or ()), outcome=outcome, support_count=1, limitations=("SINGLE_CASE",)))
        return IngestedCase(document.document_id, document.candidate_claims, expert_patterns, empirical_patterns)


__all__ = ["DocumentCaseIngestionRunner", "IngestedCase", "ResearchEscalationDecision", "decide_research_escalation"]
