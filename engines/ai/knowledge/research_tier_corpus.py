"""Build additive trust-tier documents from existing VEDA research stores.

This adapter deliberately does not promote anything. It exposes existing
research candidates, archives, and phase research to the unified corpus while
preserving their source and validation metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_PHASE_DOMAINS = {
    "p021": "CAREER",
    "p022": "WEALTH",
    "p023": "EDUCATION",
    "p024": "MARRIAGE",
    "p025": "PROGENY",
    "p026": "HEALTH",
}


def _read_json(path: Path) -> Any:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _phase_domain(path: Path) -> str:
    lowered = str(path).lower()
    for phase, domain in _PHASE_DOMAINS.items():
        if phase in lowered:
            return domain
    return "ASTROLOGY"


def _phase_zone(path: Path) -> str:
    name = path.name.upper()
    if any(term in name for term in ("EXPERIMENTAL", "SHADOW", "PREDICTION", "BACKTEST")):
        return "EXPERIMENTAL"
    return "RESEARCH_CANDIDATE"


def load_research_tier_documents(root: Path) -> list[dict[str, Any]]:
    """Return deterministic documents from existing candidate and phase stores."""

    documents: list[dict[str, Any]] = []
    candidate_path = root / "data" / "research" / "vedic_astrology_pilot" / "research_candidate.json"
    candidates = _read_json(candidate_path)
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict) or not candidate.get("claim"):
                continue
            zone = str(candidate.get("knowledge_zone") or "RESEARCH_CANDIDATE").upper()
            metadata = dict(candidate.get("metadata") or {})
            documents.append(
                {
                    "doc_id": candidate.get("candidate_id"),
                    "trust_zone": zone,
                    "knowledge_zone": zone,
                    "domain": str(metadata.get("domain") or candidate.get("topic_key") or "ASTROLOGY").split("::")[0].upper(),
                    "entity": candidate.get("title") or candidate.get("topic_key") or "Research candidate",
                    "text": candidate.get("claim"),
                    "summary": candidate.get("claim"),
                    "source_ids": candidate.get("source_ids") or metadata.get("source_ids") or [],
                    "claim_ids": metadata.get("claim_ids") or [],
                    "passage_ids": [metadata["passage_id"]] if metadata.get("passage_id") else [],
                    "conflict_ids": metadata.get("conflict_ids") or [],
                    "source_class": metadata.get("source_class") or "RESEARCH_RECORD",
                    "validation_state": candidate.get("validation_status") or "RESEARCH_REQUIRED",
                    "approval_status": candidate.get("approval_status") or "RESEARCH_ONLY",
                    "created_at": candidate.get("created_at"),
                    "updated_at": candidate.get("updated_at"),
                    "method_variant": metadata.get("method_variant"),
                    "high_stakes": str(candidate.get("safety_class") or "").upper() in {"HIGH", "HIGH_STAKES", "CRITICAL"},
                }
            )

    docs_root = root / "docs" / "current-state"
    for phase, domain in _PHASE_DOMAINS.items():
        phase_root = docs_root / phase
        if not phase_root.exists():
            continue
        for path in sorted(phase_root.glob("*.md")):
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            zone = _phase_zone(path)
            documents.append(
                {
                    "doc_id": f"{phase.upper()}_RESEARCH_{path.stem}",
                    "trust_zone": zone,
                    "domain": domain,
                    "entity": path.stem.replace("_", " "),
                    "text": text,
                    "summary": text,
                    "source_class": "VEDA_PHASE_RESEARCH",
                    "validation_state": "PHASE_RESEARCH",
                    "approval_status": "RESEARCH_ONLY",
                    "version": "1.0.0",
                    "version_state": "CURRENT",
                    "high_stakes": domain in {"HEALTH", "PROGENY", "WEALTH"},
                }
            )
    return sorted(documents, key=lambda item: (str(item.get("doc_id") or ""), str(item.get("trust_zone") or "")))


__all__ = ["load_research_tier_documents"]
