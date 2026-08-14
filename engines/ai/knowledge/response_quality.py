"""Deterministic response-quality and safety-message utilities."""

from __future__ import annotations

import re
from typing import Any


def response_quality_metrics(bundle: dict[str, Any]) -> dict[str, int]:
    results = list(bundle.get("results") or [])
    texts = [" ".join(str(item.get("text") or "").split()) for item in results]
    return {
        "chart_facts_used": sum(1 for item in results if item.get("entity_keys")),
        "domain_evidence_items": len({str(item.get("domain") or "") for item in results}),
        "unique_evidence_items": len({str(item.get("doc_id") or "") for item in results}),
        "trust_zone_diversity": len({str(item.get("trust_zone") or "") for item in results}),
        "generic_statement_count": sum(1 for text in texts if len(text) < 80),
        "duplicate_sentence_count": len(texts) - len(set(texts)),
    }


def deduplicate_safety_messages(text: str) -> str:
    """Remove repeated identical safety lines while preserving the first one."""

    seen: set[str] = set()
    output: list[str] = []
    for line in str(text or "").splitlines():
        normalized = re.sub(r"\s+", " ", line).strip().lower()
        is_safety = any(term in normalized for term in ("not medical", "not a diagnosis", "not financial advice", "not a trading instruction", "consult a qualified"))
        if is_safety and normalized in seen:
            continue
        if is_safety:
            seen.add(normalized)
        output.append(line)
    return "\n".join(output)


__all__ = ["response_quality_metrics", "deduplicate_safety_messages"]
