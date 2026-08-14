"""Minimal role-based VEDA orchestrator using shared STD-001 services."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from engines.ai.knowledge.unified_retriever import RetrievalMode, UnifiedHybridRetriever

from .contracts import AgentRole, RequestContext


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
        resolved_mode = mode or ("RESEARCH" if research else "SHADOW" if prediction else "PRODUCTION_SAFE")
        request_id = "REQ-" + hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
        return RequestContext(request_id=request_id, subject_id=subject_id, domain=domain, query=query, mode=resolved_mode)

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
        return WorkflowResult(request=request, route=route, retrieval=retrieval, warnings=warnings, audit_ledger={"workflow_id": request.request_id, "request_id": request.request_id, "agents_invoked": route, "knowledge_retrieved": request.evidence_ids, "facts_used": [], "rules_used": [], "patterns_used": [], "prediction_created": request.mode in {"SHADOW", "BACKTEST"}, "failure_fallback": bool(warnings), "workflow_version": self.workflow_version})


__all__ = ["AgentOrchestrator", "WorkflowResult"]
