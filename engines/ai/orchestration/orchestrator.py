"""Minimal role-based VEDA orchestrator using shared STD-001 services."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from engines.ai.knowledge.unified_retriever import RetrievalMode, UnifiedHybridRetriever

from .contracts import AgentRole, RequestContext
from .research import decide_research_escalation


@dataclass(slots=True)
class WorkflowResult:
    request: RequestContext
    route: list[str]
    retrieval: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    audit_ledger: dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """Routes only the roles needed for a request; agents share one retriever."""

    workflow_version = "STD-002-1"

    def __init__(self, retriever: UnifiedHybridRetriever | None = None) -> None:
        self.retriever = retriever or UnifiedHybridRetriever(top_k=8)

    def route(self, query: str, *, domain: str | None = None, subject_id: str | None = None, mode: str | None = None) -> RequestContext:
        text = query.lower()
        prediction = any(term in text for term in ("when", "predict", "timing", "likely", "window", "forecast"))
        research = any(term in text for term in ("research", "classical", "source", "book", "what does veda know"))
        outcome = any(term in text for term in ("was the prediction correct", "prediction from", "outcome", "actual event", "evaluate prediction"))
        backtest = any(term in text for term in ("backtest", "historical cases", "historical prediction"))
        document = any(term in text for term in ("uploaded document", "learn this document", "ingest document"))
        if outcome:
            intent_type = "OUTCOME_UPDATE"
        elif backtest:
            intent_type = "BACKTEST"
        elif document:
            intent_type = "DOCUMENT_LEARNING"
        elif research:
            intent_type = "RESEARCH"
        elif prediction:
            intent_type = "TIMING" if any(term in text for term in ("when", "timing", "window")) else "PREDICTIVE"
        elif any(term in text for term in ("what is", "which", "where", "nakshatra", "ascendant")):
            intent_type = "FACTUAL"
        elif domain or any(term in text for term in ("strength", "indicator", "analysis", "career", "wealth", "marriage", "health")):
            intent_type = "INTERPRETIVE"
        else:
            intent_type = "GENERAL"
        resolved_mode = mode or ("RESEARCH" if research else "SHADOW" if prediction else "PRODUCTION_SAFE")
        request_id = "REQ-" + hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
        capabilities = ["CHART_FACTS", "RETRIEVAL"]
        if prediction:
            capabilities.extend(["CLASSICAL_REASONING", "PATTERN_REASONING", "PREDICTION_REGISTRY"])
        if research:
            capabilities.extend(["RESEARCH_PLATFORM", "KNOWLEDGE_VALIDATION"])
        if outcome:
            capabilities.extend(["OUTCOME_REGISTRY", "PREDICTION_EVALUATION"])
        return RequestContext(request_id=request_id, subject_id=subject_id, domain=domain, query=query, mode=resolved_mode, intent_type=intent_type, required_capabilities=capabilities)

    def run(self, query: str, *, domain: str | None = None, subject_id: str | None = None, mode: str | None = None) -> WorkflowResult:
        request = self.route(query, domain=domain, subject_id=subject_id, mode=mode)
        route = [AgentRole.ORCHESTRATOR.value]
        if request.mode in {"RESEARCH", "SHADOW", "BACKTEST", "ADMIN_AUDIT"}:
            route.extend([AgentRole.RESEARCH.value] if request.mode == "RESEARCH" else [])
        route.append(AgentRole.JYOTISHA_REASONING.value if domain or any(term in query.lower() for term in ("chart", "kundli", "dasha", "planet", "house")) else AgentRole.RESPONSE.value)
        if request.mode in {"SHADOW", "BACKTEST"}:
            route.extend([AgentRole.INTUITION_PATTERN.value, AgentRole.PREDICTION.value])
        if route[-1] != AgentRole.RESPONSE.value:
            route.append(AgentRole.RESPONSE.value)
        mode_value = RetrievalMode(request.mode)
        warnings: list[str] = []
        try:
            results = self.retriever.retrieve(query, domain=domain, mode=mode_value)[:8]
        except Exception as exc:  # safe fallback preserves upstream request context
            results = []
            warnings.append(f"RETRIEVAL_UNAVAILABLE:{type(exc).__name__}")
        retrieval = {
            "results": results,
            "retrieval_mode": mode_value.value,
            "summary": {"source_count": len(results), "sources": results},
            "knowledge_usage_trace": {
                "available_knowledge": "unified corpus inputs",
                "retrieved_knowledge_count": len(results),
                "filtered_knowledge": "trust zones excluded by retrieval mode",
                "selected_trust_zones": sorted({str(item.get("trust_zone") or "") for item in results}),
            },
        }
        request.evidence_ids = [str(item.get("entity") or item.get("doc_id") or "") for item in results]
        escalation = decide_research_escalation(explicit_request=request.intent_type == "RESEARCH", retrieved_count=len(results))
        if escalation.required and request.intent_type == "RESEARCH":
            request.warnings.append("RESEARCH_REQUIRED:" + escalation.reason)
        return WorkflowResult(request=request, route=route, retrieval=retrieval, warnings=warnings, audit_ledger={"workflow_id": request.request_id, "request_id": request.request_id, "agents_invoked": route, "knowledge_retrieved": request.evidence_ids, "facts_used": [], "rules_used": [], "patterns_used": [], "prediction_created": request.mode in {"SHADOW", "BACKTEST"}, "failure_fallback": bool(warnings), "workflow_version": self.workflow_version})

    def shadow_trace(self, query: str, *, domain: str | None = None) -> dict[str, Any]:
        """Cheap Stage-A trace for normal chat; it never changes the reply."""
        request = self.route(query, domain=domain)
        return {
            "mode": "SHADOW",
            "request_id": request.request_id,
            "intent_type": request.intent_type,
            "domain": request.domain,
            "retrieval_mode": request.mode,
            "required_capabilities": request.required_capabilities,
            "prediction_intent": request.intent_type in {"PREDICTIVE", "TIMING"},
            "response_path_unchanged": True,
            "workflow_version": self.workflow_version,
        }


__all__ = ["AgentOrchestrator", "WorkflowResult"]
