"""Universal document-learning and existing-knowledge comparison adapter."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engines.ai.knowledge.unified_retriever import RetrievalMode, UnifiedHybridRetriever


@dataclass(slots=True)
class LearnedDocument:
    document_id: str
    title: str
    source_path: str
    domain: str
    passages: list[str] = field(default_factory=list)
    candidate_claims: list[dict[str, Any]] = field(default_factory=list)


class DocumentLearningService:
    """Register, segment, compare, and label documents without Core promotion."""

    def __init__(self, retriever: UnifiedHybridRetriever | None = None) -> None:
        self.retriever = retriever or UnifiedHybridRetriever(top_k=8)

    def register_document(self, path: str | Path, *, domain: str = "RESEARCH") -> LearnedDocument:
        source = Path(path)
        text = source.read_text(encoding="utf-8")
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.strip()), source.stem)
        document_id = f"DOC_{hashlib.sha256(str(source.resolve()).encode('utf-8')).hexdigest()[:16]}"
        passages = [chunk.strip() for chunk in re.split(r"\n\s*\n+", text) if chunk.strip()]
        claims = [
            {
                "claim_id": f"{document_id}_CLM_{index:04d}",
                "document_id": document_id,
                "passage_id": f"{document_id}_PSG_{index:04d}",
                "claim": passage[:2000],
                "domain": domain.upper(),
                "trust_zone": "RESEARCH_CANDIDATE",
                "validation_state": "RESEARCH_REQUIRED",
                "approval_status": "PENDING",
                "source_path": str(source),
            }
            for index, passage in enumerate(passages, start=1)
        ]
        return LearnedDocument(document_id, title, str(source), domain.upper(), passages, claims)

    def compare_with_existing(self, claim: str, *, domain: str | None = None) -> dict[str, Any]:
        results = self.retriever.retrieve(claim, domain=domain, mode=RetrievalMode.RESEARCH)
        normalized = " ".join(claim.lower().split())
        exact = [item for item in results if normalized and normalized in str(item.get("text") or "").lower()]
        supporting = [item for item in results if any(term in str(item.get("text") or "").lower() for term in normalized.split()[:5])]
        zones = sorted({str(item.get("trust_zone") or "") for item in results})
        if exact:
            classification = "EXISTING_EXACT"
        elif supporting:
            classification = "EXISTING_SUPPORTING"
        else:
            classification = "NEW_KNOWLEDGE"
        return {
            "classification": classification,
            "results": results,
            "trust_zones": zones,
            "existing_exact": exact,
            "existing_supporting": supporting,
            "candidate_required": classification != "EXISTING_EXACT",
        }

    def create_research_candidate(self, claim: str, *, document_id: str, domain: str = "RESEARCH") -> dict[str, Any]:
        comparison = self.compare_with_existing(claim, domain=domain)
        return {
            "candidate_id": f"RCND_{hashlib.sha256((document_id + claim).encode('utf-8')).hexdigest()[:16]}",
            "document_id": document_id,
            "claim": claim,
            "domain": domain.upper(),
            "trust_zone": "RESEARCH_CANDIDATE",
            "validation_state": "RESEARCH_REQUIRED",
            "comparison": comparison["classification"],
            "existing_knowledge": comparison["results"],
            "approval_status": "PENDING",
            "promotion_requires_admin": True,
        }


__all__ = ["DocumentLearningService", "LearnedDocument"]
