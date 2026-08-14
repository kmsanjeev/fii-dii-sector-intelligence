from __future__ import annotations

import pytest

from engines.ai.orchestration import (
    AgentOrchestrator,
    EmpiricalPattern,
    ExpertReasoningPattern,
    OutcomeRecord,
    PatternRegistry,
    PredictionRegistry,
    SelfCritique,
    convergence_summary,
)
from engines.ai.orchestration.contracts import EvidenceType, ReasoningEvidence, ReasoningLayer
from engines.ai.orchestration.reasoning import CounterHypothesis
from engines.ai.orchestration.persistence import DurablePredictionRegistry, score_prediction


def test_structured_evidence_separates_classical_and_empirical_layers() -> None:
    evidence = ReasoningEvidence(
        evidence_id="E1",
        evidence_type=EvidenceType.CLASSICAL_SUPPORT,
        layer=ReasoningLayer.CLASSICAL,
        claim="A source-backed rule is conditionally supportive.",
        source_ids=["SRC-1"],
    )
    payload = evidence.to_dict()
    assert payload["layer"] == "CLASSICAL"
    assert payload["evidence_type"] == "CLASSICAL_SUPPORT"
    assert payload["source_ids"] == ["SRC-1"]


def test_pattern_registry_keeps_expert_and_empirical_patterns_distinct() -> None:
    registry = PatternRegistry()
    registry.add_expert(ExpertReasoningPattern("EXP-1", "case author", "SRC-1", factors=("Dasha",)))
    registry.add_empirical(EmpiricalPattern("EMP-1", "cases.csv", 2, features=("Dasha",), support_count=1, failure_count=1))
    assert registry.counts() == {"EXPERT_REASONING_PATTERN": 1, "EMPIRICAL_PATTERN": 1}
    assert len(registry.find(factors={"dasha"})) == 2


def test_prediction_is_prospective_and_outcome_is_immutable() -> None:
    registry = PredictionRegistry()
    prediction = registry.create(
        request_id="REQ-1",
        subject_id="S-1",
        domain="MARRIAGE",
        prediction_type="EXPERIMENTAL_PREDICTION",
        prediction_direction="SUPPORT",
        prediction_description="A relationship-support window is hypothesized.",
        window_start="2027-01-01",
        window_end="2027-06-30",
        event_definition="relationship",
        confidence_state="MODERATE",
    )
    assert prediction.actual_outcome is None
    registry.record_outcome("PRED-" + prediction.prediction_id.split("PRED-", 1)[-1], OutcomeRecord("O-1", "S-1", "MARRIAGE", "relationship", event_direction="SUPPORT"))
    with pytest.raises(RuntimeError):
        prediction.record_outcome(OutcomeRecord("O-2", "S-1", "MARRIAGE", "relationship", event_direction="SUPPORT"))
    assert registry.evaluate(domain="MARRIAGE")["sample_size"] == 1


def test_orchestrator_uses_minimal_routes_and_shared_retrieval() -> None:
    class StubRetriever:
        def retrieve(self, query, domain=None, *, mode=None):
            return [{"doc_id": "D1", "trust_zone": "APPROVED_CORE", "domain": domain or "ALL", "text": query}]

    orchestrator = AgentOrchestrator(StubRetriever())
    factual = orchestrator.run("What is my chart Moon Nakshatra?")
    predictive = orchestrator.run("When is marriage most likely?", domain="MARRIAGE")
    assert factual.route == ["ORCHESTRATOR", "JYOTISHA_REASONING", "RESPONSE"]
    assert "INTUITION_PATTERN" in predictive.route
    assert predictive.request.mode == "SHADOW"
    assert predictive.audit_ledger["workflow_version"] == "STD-002-1"


def test_production_safe_retrieval_keeps_research_labels_available_only_when_mode_allows() -> None:
    class StubRetriever:
        def retrieve(self, query, domain=None, *, mode=None):
            return [{"doc_id": "D1", "trust_zone": "RESEARCH_CANDIDATE", "domain": domain, "text": query}]

    orchestrator = AgentOrchestrator(StubRetriever())
    result = orchestrator.run("Research marriage timing methods", domain="MARRIAGE", mode="RESEARCH")
    assert result.request.mode == "RESEARCH"
    assert result.retrieval["retrieval_mode"] == "RESEARCH"


def test_convergence_controls_correlated_evidence_and_supports_counter_hypothesis() -> None:
    rows = [
        ReasoningEvidence("E1", EvidenceType.CLASSICAL_SUPPORT, ReasoningLayer.CLASSICAL, "support", evidence_family="planet", underlying_fact="Mars"),
        ReasoningEvidence("E2", EvidenceType.TIMING_SUPPORT, ReasoningLayer.INTUITIVE_EMPIRICAL, "timing", evidence_family="timing", underlying_fact="Mars"),
    ]
    summary = convergence_summary(rows)
    assert summary["classification"] == "CROSS_LAYER_CONVERGENCE"
    assert summary["double_counting_risk"] is True
    critique = SelfCritique(alternatives=(CounterHypothesis("A different manifestation is possible."),), double_counting_risk=True)
    assert critique.to_dict()["alternatives"][0]["status"] == "HYPOTHESIS"


def test_agent_failure_is_logged_without_fabricating_evidence() -> None:
    class BrokenRetriever:
        def retrieve(self, *args, **kwargs):
            raise RuntimeError("unavailable")

    result = AgentOrchestrator(BrokenRetriever()).run("Research career timing", domain="CAREER")
    assert result.retrieval["results"] == []
    assert result.audit_ledger["failure_fallback"] is True
    assert result.request.evidence_ids == []


def test_stage_a_shadow_trace_classifies_prediction_intent() -> None:
    trace = AgentOrchestrator().shadow_trace("When is career timing likely?", domain="CAREER")
    assert trace["intent_type"] == "TIMING"
    assert trace["prediction_intent"] is True
    assert trace["response_path_unchanged"] is True
