"""
Unified Hybrid Retriever -- Phase 2C
Searches one combined durable Veda corpus instead of stitching separate
reviewed-memory, MIT capability, and platform RAG blocks inside chat.
"""

from __future__ import annotations

from typing import Any, Optional

from engines.common.logger import get_logger

logger = get_logger(__name__)

RRF_K = 60
DEFAULT_TOP_K = 6
_POSITIVE_TERMS = {
    "accumulation",
    "bullish",
    "buy",
    "breakout",
    "emerging",
    "expansion",
    "gain",
    "leading",
    "outperform",
    "positive",
    "rally",
    "rising",
    "strong",
    "support",
    "uptrend",
}
_NEGATIVE_TERMS = {
    "avoid",
    "bearish",
    "caution",
    "decline",
    "distribution",
    "downtrend",
    "drop",
    "falling",
    "lagging",
    "markdown",
    "negative",
    "risk",
    "sell",
    "weak",
    "warning",
}

DOMAIN_KEYWORDS = {
    "ASTROLOGY": ["jyotisha", "astrology", "kundli", "dasha", "yoga", "dosha", "graha", "bhava", "lagna", "nakshatra"],
    "SECTOR": ["sector", "rotation", "industry", "leading", "lagging", "early_rotation"],
    "STOCK": ["stock", "symbol", "share", "equity", "scrip", "emerging", "watchlist", "candidate"],
    "DEAL": ["deal", "bulk", "block", "trade", "transaction", "acquisition", "institutional deal"],
    "CORPORATE": ["corporate", "buyback", "dividend", "bonus", "split", "confidence", "promoter"],
    "MARKET": ["market", "regime", "fii", "dii", "accumulation", "distribution", "participant"],
    "MIT_REPO_CAPABILITY": ["repo", "mit", "capability", "skill", "workflow", "prompt", "artifact", "tool"],
    "RESEARCH": ["book", "document", "pdf", "image", "upload", "uploaded", "attachment", "study", "remember"],
}

_FILE_MEMORY_TERMS = {"book", "document", "pdf", "image", "upload", "uploaded", "attachment", "remember", "study"}
_REPO_TERMS = {"repo", "mit", "capability", "skill", "workflow", "prompt", "artifact", "tool"}
_FRESHNESS_TERMS = {"today", "current", "latest", "now", "recent", "fresh"}


class UnifiedHybridRetriever:
    def __init__(self, top_k: int = DEFAULT_TOP_K):
        self.top_k = top_k

    def retrieve(self, query: str, domain: Optional[str] = None) -> list[dict[str, Any]]:
        if domain is None:
            domain = _detect_domain(query)

        logger.debug("[UnifiedRetriever] Query='%s' | Domain=%s", query, domain)
        bm25_results = _bm25_query(query, top_k=self.top_k * 3)
        faiss_results = _faiss_query(query, top_k=self.top_k * 3)
        approved_core_results = _approved_core_query(query, top_k=self.top_k * 3)
        fused = _rrf_fuse(bm25_results, faiss_results, k=RRF_K)
        fused = _merge_ranked_results(fused, approved_core_results, rank_field="approved_core_rank", k=RRF_K)
        rescored = _apply_post_rank(fused, query=query, requested_domain=domain)
        filtered = [
            doc
            for doc in rescored
            if not (
                str(doc.get("source_type") or "") == "approved_core"
                and str(doc.get("version_state") or "").upper() in {"SUPERSEDED", "DEPRECATED", "WITHDRAWN"}
            )
        ]
        return [_decorate_doc(doc) for doc in filtered[: self.top_k]]

    def build_context_bundle(self, query: str, *, top_k: int = 4) -> dict[str, Any]:
        results = self.retrieve(query)[:top_k]
        summary = _summarize_results(results)
        return {
            "context": _render_context(results, summary=summary),
            "summary": summary,
            "results": results,
        }

    def build_context(self, query: str, *, top_k: int = 4) -> str:
        return str(self.build_context_bundle(query, top_k=top_k).get("context") or "")


def _rrf_fuse(list_a: list[dict[str, Any]], list_b: list[dict[str, Any]], k: int = RRF_K) -> list[dict[str, Any]]:
    scores: dict[str, dict[str, Any]] = {}

    for rank, doc in enumerate(list_a, start=1):
        did = str(doc["doc_id"])
        if did not in scores:
            scores[did] = {"doc": doc, "rrf": 0.0, "bm25_rank": None, "faiss_rank": None}
        scores[did]["rrf"] += 1.0 / (k + rank)
        scores[did]["bm25_rank"] = rank

    for rank, doc in enumerate(list_b, start=1):
        did = str(doc["doc_id"])
        if did not in scores:
            scores[did] = {"doc": doc, "rrf": 0.0, "bm25_rank": None, "faiss_rank": None}
        scores[did]["rrf"] += 1.0 / (k + rank)
        scores[did]["faiss_rank"] = rank

    ordered = sorted(scores.values(), key=lambda item: item["rrf"], reverse=True)
    results = []
    for rank, entry in enumerate(ordered, start=1):
        doc = dict(entry["doc"])
        doc["rrf_score"] = round(entry["rrf"], 6)
        doc["bm25_rank"] = entry["bm25_rank"]
        doc["faiss_rank"] = entry["faiss_rank"]
        doc["rank"] = rank
        results.append(doc)
    return results


def _merge_doc_fields(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    preferred_keys = {
        "knowledge_class",
        "authority",
        "citations",
        "citation_labels",
        "claim_ids",
        "passage_ids",
        "source_ids",
        "rule_ids",
        "conflict_ids",
        "conflict_details",
        "version",
        "version_state",
        "high_stakes",
        "provenance",
        "reliability_note",
        "summary",
        "text",
    }
    for key, value in extra.items():
        if key in preferred_keys and value not in (None, "", [], {}):
            merged[key] = value
            continue
        if key not in merged or merged[key] in (None, "", [], {}):
            merged[key] = value
    return merged


def _merge_ranked_results(
    current_results: list[dict[str, Any]],
    extra_results: list[dict[str, Any]],
    *,
    rank_field: str,
    k: int = RRF_K,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {str(item.get("doc_id") or ""): dict(item) for item in current_results}
    for rank, doc in enumerate(extra_results, start=1):
        doc_id = str(doc.get("doc_id") or "")
        if not doc_id:
            continue
        bonus = 1.0 / (k + rank)
        if doc_id in merged:
            current = dict(merged[doc_id])
            current = _merge_doc_fields(current, doc)
            current["rrf_score"] = round(float(current.get("rrf_score") or 0.0) + bonus, 6)
            current[rank_field] = rank
            merged[doc_id] = current
        else:
            seeded = dict(doc)
            seeded.setdefault("bm25_rank", None)
            seeded.setdefault("faiss_rank", None)
            seeded["rrf_score"] = round(bonus, 6)
            seeded[rank_field] = rank
            merged[doc_id] = seeded
    ordered = sorted(merged.values(), key=lambda item: float(item.get("rrf_score") or 0.0), reverse=True)
    for rank, doc in enumerate(ordered, start=1):
        doc["rank"] = rank
    return ordered


def _apply_post_rank(results: list[dict[str, Any]], *, query: str, requested_domain: str) -> list[dict[str, Any]]:
    q = (query or "").lower()
    wants_memory = any(term in q for term in _FILE_MEMORY_TERMS)
    wants_repo = any(term in q for term in _REPO_TERMS)
    wants_freshness = any(term in q for term in _FRESHNESS_TERMS)

    rescored = []
    for doc in results:
        score = float(doc.get("rrf_score") or 0.0)
        domain = str(doc.get("domain") or "")
        source_type = str(doc.get("source_type") or "")
        knowledge_class = str(doc.get("knowledge_class") or "")
        if requested_domain != "ALL" and domain == requested_domain:
            score += 0.010
        if wants_memory and source_type in {"user_reviewed", "attachment_chunk"}:
            score += 0.012
        if wants_repo and source_type == "mit_repo_capability":
            score += 0.012
        if wants_freshness and source_type == "platform_intelligence":
            score += 0.008
        if wants_freshness and str(doc.get("effective_date") or "").strip():
            score += 0.004
        if knowledge_class == "APPROVED_CORE":
            score += 0.018
        if source_type == "approved_core":
            score += min(float((doc.get("authority") or {}).get("domain_confidence") or 0.0), 1.0) * 0.012
        if source_type == "approved_core" and str(doc.get("version_state") or "").upper() != "CURRENT":
            score -= 0.25
        enriched = dict(doc)
        enriched["combined_score"] = round(score, 6)
        rescored.append(enriched)

    rescored.sort(
        key=lambda item: (
            float(item.get("combined_score") or 0.0),
            str(item.get("effective_date") or item.get("saved_at") or ""),
            str(item.get("doc_id") or ""),
        ),
        reverse=True,
    )
    for rank, doc in enumerate(rescored, start=1):
        doc["rank"] = rank
    return rescored


def _detect_domain(query: str) -> str:
    q = (query or "").lower()
    scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in q:
                scores[domain] += 1
    best = max(scores, key=lambda name: scores[name])
    return best if scores[best] > 0 else "ALL"


def _source_label(source_type: Any) -> str:
    mapping = {
        "approved_core": "approved core knowledge",
        "platform_intelligence": "platform intelligence",
        "user_reviewed": "approved memory",
        "attachment_chunk": "attachment memory",
        "mit_repo_capability": "MIT capability note",
    }
    return mapping.get(str(source_type or ""), str(source_type or "knowledge"))


def _fallback_evidence_kind(source_type: str) -> str:
    mapping = {
        "approved_core": "approved_core_knowledge",
        "platform_intelligence": "platform_signal_snapshot",
        "user_reviewed": "approved_memory",
        "attachment_chunk": "attachment_memory",
        "mit_repo_capability": "mit_repo_capability",
    }
    return mapping.get(source_type, "descriptive_knowledge")


def _fallback_reliability_note(evidence_kind: str) -> str | None:
    mapping = {
        "approved_core_knowledge": (
            "Approved core knowledge is governed Veda knowledge promoted after explicit Admin approval. "
            "It remains separate from temporary external research and from deterministic production rule activation."
        ),
        "predictive_ml_signal": (
            "Treat this as predictive scored evidence, not guaranteed fact. Confirm it with fresh "
            "flows, price action, and other current intelligence."
        ),
        "platform_signal_snapshot": (
            "This is a local platform snapshot for the stated date. Use it as descriptive intelligence, "
            "not as a guaranteed forecast."
        ),
        "approved_memory": (
            "Approved memory is durable context saved by the user, but it may be older than the latest market state."
        ),
        "attachment_memory": (
            "Attachment memory comes from approved file extraction and may reflect OCR or parsing limits."
        ),
        "mit_repo_capability": "MIT capability notes are reusable ideas, not live market facts.",
    }
    return mapping.get(evidence_kind)


def _evidence_label(evidence_kind: Any) -> str:
    mapping = {
        "approved_core_knowledge": "approved core knowledge",
        "predictive_ml_signal": "predictive ML signal",
        "platform_signal_snapshot": "platform signal snapshot",
        "approved_memory": "approved memory",
        "attachment_memory": "attachment memory",
        "mit_repo_capability": "MIT capability note",
        "descriptive_knowledge": "descriptive knowledge",
    }
    return mapping.get(str(evidence_kind or ""), str(evidence_kind or "knowledge"))


def _decorate_doc(doc: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(doc)
    source_type = str(enriched.get("source_type") or "")
    evidence_kind = str(enriched.get("evidence_kind") or _fallback_evidence_kind(source_type))
    enriched["evidence_kind"] = evidence_kind
    if not str(enriched.get("knowledge_class") or "").strip():
        if source_type == "approved_core":
            enriched["knowledge_class"] = "APPROVED_CORE"
        elif evidence_kind == "predictive_ml_signal":
            enriched["knowledge_class"] = "ML_PREDICTION"
        elif source_type in {"user_reviewed", "attachment_chunk", "mit_repo_capability"}:
            enriched["knowledge_class"] = "REVIEWED_INTERNAL"
        else:
            enriched["knowledge_class"] = "LOCAL_PLATFORM_EVIDENCE"
    if not str(enriched.get("reliability_note") or "").strip():
        fallback_note = _fallback_reliability_note(evidence_kind)
        if fallback_note:
            enriched["reliability_note"] = fallback_note
    if evidence_kind == "predictive_ml_signal" and not str(enriched.get("score_meaning") or "").strip():
        enriched["score_meaning"] = (
            "Higher local model scores indicate a stronger bullish continuation signal inside the platform pipeline."
        )
    return enriched


def _result_date(doc: dict[str, Any]) -> str:
    return str(doc.get("effective_date") or doc.get("saved_at") or "").strip()


def _normalize_date_label(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return raw[:10] if len(raw) >= 10 else raw


def _confidence_value(doc: dict[str, Any]) -> float | None:
    value = doc.get("confidence")
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return None


def _source_title(doc: dict[str, Any]) -> str:
    provenance = doc.get("provenance", {}) or {}
    attachment_name = str(provenance.get("attachment_name") or "").strip()
    repo_label = str(provenance.get("repo_label") or "").strip()
    source_title = str(provenance.get("source_title") or "").strip()
    if attachment_name:
        return attachment_name
    if repo_label:
        return repo_label
    if source_title:
        return source_title
    return str(doc.get("entity") or "Knowledge source").strip() or "Knowledge source"


def _clip_summary(text: Any, limit: int = 220) -> str:
    value = " ".join(str(text or "").strip().split())
    if len(value) <= limit:
        return value
    if limit <= 3:
        return value[:limit]
    return value[: limit - 3].rstrip() + "..."


def _source_reference(doc: dict[str, Any]) -> dict[str, Any]:
    provenance = doc.get("provenance", {}) or {}
    citation_labels = list(doc.get("citation_labels") or [])
    if not citation_labels:
        citation_labels = [
            str(item.get("citation_label") or "").strip()
            for item in (doc.get("citations") or [])
            if str(item.get("citation_label") or "").strip()
        ]
    return {
        "source_id": str(doc.get("doc_id") or ""),
        "source_type": str(doc.get("source_type") or ""),
        "source_label": _source_label(doc.get("source_type")),
        "evidence_kind": str(doc.get("evidence_kind") or "descriptive_knowledge"),
        "evidence_label": _evidence_label(doc.get("evidence_kind")),
        "knowledge_class": str(doc.get("knowledge_class") or "").strip() or None,
        "domain": str(doc.get("domain") or "UNKNOWN"),
        "title": _source_title(doc),
        "entity": str(doc.get("entity") or "").strip() or None,
        "date": _normalize_date_label(_result_date(doc)),
        "freshness_class": str(doc.get("freshness_class") or "").strip() or None,
        "confidence": _confidence_value(doc),
        "summary": _clip_summary(doc.get("summary") or doc.get("text") or "", 220) or None,
        "attachment_name": str(provenance.get("attachment_name") or "").strip() or None,
        "repo_label": str(provenance.get("repo_label") or "").strip() or None,
        "license_name": str(doc.get("license_name") or provenance.get("license_name") or "").strip() or None,
        "model_name": str(doc.get("model_name") or "").strip() or None,
        "model_version": str(doc.get("model_version") or "").strip() or None,
        "score_meaning": _clip_summary(doc.get("score_meaning") or "", 180) or None,
        "reliability_note": _clip_summary(doc.get("reliability_note") or "", 180) or None,
        "claim_ids": list(doc.get("claim_ids") or []),
        "passage_ids": list(doc.get("passage_ids") or []),
        "source_ids": list(doc.get("source_ids") or []),
        "rule_ids": list(doc.get("rule_ids") or []),
        "conflict_ids": list(doc.get("conflict_ids") or []),
        "version": str(doc.get("version") or "").strip() or None,
        "version_state": str(doc.get("version_state") or "").strip() or None,
        "high_stakes": bool(doc.get("high_stakes")),
        "authority": dict(doc.get("authority") or {}),
        "citations": list(doc.get("citations") or []),
        "citation_labels": citation_labels,
        "conflict_details": list(doc.get("conflict_details") or []),
        "rank": int(doc.get("rank") or 0),
    }


def _entity_group_key(doc: dict[str, Any]) -> str:
    entity_keys = doc.get("entity_keys", {}) or {}
    for key_name in ("symbol", "sector", "topic", "repo_label", "attachment_name"):
        value = str(entity_keys.get(key_name) or "").strip()
        if value:
            return value.upper()
    entity = str(doc.get("entity") or "").strip()
    return entity.upper() if entity else str(doc.get("doc_id") or "").upper()


def _polarity(doc: dict[str, Any]) -> str:
    haystack = " ".join(
        part
        for part in [
            str(doc.get("entity") or ""),
            str(doc.get("summary") or ""),
            str(doc.get("text") or "")[:320],
            str(doc.get("score_meaning") or ""),
            str(doc.get("reliability_note") or ""),
        ]
        if part
    ).lower()
    positive = any(term in haystack for term in _POSITIVE_TERMS)
    negative = any(term in haystack for term in _NEGATIVE_TERMS)
    if positive and negative:
        return "mixed"
    if positive:
        return "positive"
    if negative:
        return "negative"
    return "unknown"


def _conflict_note(results: list[dict[str, Any]]) -> str | None:
    groups: dict[str, dict[str, Any]] = {}
    for raw_doc in results:
        doc = _decorate_doc(raw_doc)
        key = _entity_group_key(doc)
        entry = groups.setdefault(
            key,
            {
                "title": _source_title(doc),
                "polarities": set(),
                "source_labels": set(),
            },
        )
        polarity = _polarity(doc)
        if polarity in {"positive", "negative"}:
            entry["polarities"].add(polarity)
            entry["source_labels"].add(_source_label(doc.get("source_type")))
    for entry in groups.values():
        if {"positive", "negative"}.issubset(entry["polarities"]):
            labels = sorted(entry["source_labels"])
            label_text = ", ".join(labels[:3]) if labels else "local sources"
            return (
                f"Local sources disagree on {entry['title']}. Some evidence looks supportive while other "
                f"evidence is cautious or negative. Check the dates and source labels before treating it as settled. "
                f"Main source types involved: {label_text}."
            )
    return None


def _freshness_note(results: list[dict[str, Any]]) -> str | None:
    normalized_dates = [
        date_label
        for date_label in (_normalize_date_label(_result_date(_decorate_doc(doc))) for doc in results)
        if date_label
    ]
    unique_dates = list(dict.fromkeys(normalized_dates))
    has_memory = any(
        str(_decorate_doc(doc).get("source_type") or "") in {"user_reviewed", "attachment_chunk"}
        for doc in results
    )
    has_platform = any(
        str(_decorate_doc(doc).get("source_type") or "") == "platform_intelligence"
        for doc in results
    )
    if len(unique_dates) > 1:
        newest = max(unique_dates)
        return (
            f"These local sources are not from one single date. The newest dated item here is {newest}, "
            "so use that first for current-state questions."
        )
    if has_memory and has_platform and unique_dates:
        return (
            "This answer mixes current local platform signals with saved memory. Treat saved memory as background "
            "context, and use the dated platform signal for the latest market state."
        )
    return None


def _render_context(results: list[dict[str, Any]], *, summary: dict[str, Any] | None = None) -> str:
    if not results:
        return ""

    summary = summary or _summarize_results(results)
    lines = [
        "Unified evidence below blends local platform intelligence, approved core knowledge, approved memory, attachment memory, and approved MIT capability notes while keeping each trust class separate.",
        "Treat approved core knowledge as governed Veda knowledge. Treat predictive ML signals as forward-looking scored evidence, not confirmed fact. Treat approved memory and attachment memory as descriptive saved knowledge.",
    ]
    if summary.get("conflict_note"):
        lines.append(f"Conflict note: {summary['conflict_note']}")
    if summary.get("freshness_note"):
        lines.append(f"Freshness note: {summary['freshness_note']}")

    sections = [
        ("APPROVED CORE KNOWLEDGE", [item for item in results if str(_decorate_doc(item).get("knowledge_class") or "") == "APPROVED_CORE"]),
        ("KNOWN CONFLICTS", []),
        ("LOCAL PLATFORM EVIDENCE", [item for item in results if str(_decorate_doc(item).get("source_type") or "") == "platform_intelligence" and str(_decorate_doc(item).get("evidence_kind") or "") != "predictive_ml_signal"]),
        ("ML / PREDICTIVE SIGNALS", [item for item in results if str(_decorate_doc(item).get("evidence_kind") or "") == "predictive_ml_signal"]),
        ("REVIEWED INTERNAL MEMORY", [item for item in results if str(_decorate_doc(item).get("knowledge_class") or "") == "REVIEWED_INTERNAL"]),
        ("LEGACY UNSOURCED KNOWLEDGE", [item for item in results if str(_decorate_doc(item).get("knowledge_class") or "") == "LEGACY_UNSOURCED"]),
    ]

    if summary.get("known_conflicts"):
        lines.append("")
        lines.append("KNOWN CONFLICTS:")
        for conflict in list(summary.get("known_conflicts") or []):
            topic = str(conflict.get("topic") or "Approved-core conflict").strip()
            conflict_type = str(conflict.get("conflict_type") or "UNRESOLVED").strip()
            resolution = str(conflict.get("resolution_status") or "UNRESOLVED").strip()
            analysis = str(conflict.get("analysis") or "").strip()
            lines.append(f"- {topic} | type={conflict_type} | status={resolution}")
            if analysis:
                lines.append(f"  {analysis[:300]}")

    for section_label, section_docs in sections:
        if not section_docs:
            continue
        lines.append("")
        lines.append(f"{section_label}:")
        for index, raw_doc in enumerate(section_docs, start=1):
            doc = _decorate_doc(raw_doc)
            source_label = _source_label(doc.get("source_type"))
            evidence_label = _evidence_label(doc.get("evidence_kind"))
            domain = str(doc.get("domain") or "UNKNOWN")
            freshness = str(doc.get("freshness_class") or "unknown")
            date_label = _result_date(doc)
            date_text = f" | date={date_label}" if date_label else ""
            model_name = str(doc.get("model_name") or "").strip()
            model_version = str(doc.get("model_version") or "").strip()
            model_bits = [part for part in [model_name, model_version] if part]
            model_text = f" | model={'@'.join(model_bits)}" if model_bits else ""
            confidence = doc.get("confidence")
            confidence_text = f" | confidence={confidence:.2f}" if isinstance(confidence, (int, float)) else ""
            version_text = (
                f" | version={str(doc.get('version') or '').strip()}:{str(doc.get('version_state') or '').strip()}"
                if str(doc.get("version") or "").strip() or str(doc.get("version_state") or "").strip()
                else ""
            )
            authority = doc.get("authority") or {}
            authority_text = (
                f" | authority={float(authority.get('domain_confidence') or 0.0):.2f}"
                if authority
                else ""
            )
            lines.append(
                f"- [{index}] {evidence_label} | source={source_label} | domain={domain} | freshness={freshness}{date_text}{model_text}{confidence_text}{version_text}{authority_text}"
            )
            citation_labels = list(doc.get("citation_labels") or [])
            if not citation_labels:
                citation_labels = [
                    str(item.get("citation_label") or "").strip()
                    for item in (doc.get("citations") or [])
                    if str(item.get("citation_label") or "").strip()
                ]
            if citation_labels:
                lines.append(f"  citations: {', '.join(citation_labels[:3])}")
            score_meaning = str(doc.get("score_meaning") or "").strip()
            if score_meaning:
                lines.append(f"  meaning: {score_meaning[:260]}")
            reliability_note = str(doc.get("reliability_note") or "").strip()
            if reliability_note:
                lines.append(f"  reliability: {reliability_note[:260]}")
            if doc.get("high_stakes"):
                lines.append("  safety: high-stakes safeguards still apply to this knowledge.")
            lines.append(f"  {str(doc.get('text', '')).strip()[:420]}")
    return "\n".join(lines)


def _summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "used": bool(results),
        "source_count": len(results),
        "evidence_kinds": [],
        "knowledge_classes": [],
        "approved_core_count": 0,
        "reviewed_internal_count": 0,
        "local_platform_count": 0,
        "legacy_unsourced_count": 0,
        "predictive_ml_count": 0,
        "platform_snapshot_count": 0,
        "approved_memory_count": 0,
        "attachment_memory_count": 0,
        "repo_count": 0,
        "conflict_count": 0,
        "citation_count": 0,
        "high_stakes_count": 0,
        "top_date": None,
        "sources": [],
        "conflict_note": None,
        "freshness_note": None,
        "known_conflicts": [],
    }
    kinds: list[str] = []
    knowledge_classes: list[str] = []
    known_conflicts: list[dict[str, Any]] = []
    for raw_doc in results:
        doc = _decorate_doc(raw_doc)
        evidence_kind = str(doc.get("evidence_kind") or "descriptive_knowledge")
        if evidence_kind not in kinds:
            kinds.append(evidence_kind)
        knowledge_class = str(doc.get("knowledge_class") or "").strip()
        if knowledge_class and knowledge_class not in knowledge_classes:
            knowledge_classes.append(knowledge_class)
        if knowledge_class == "APPROVED_CORE":
            summary["approved_core_count"] += 1
        elif knowledge_class == "REVIEWED_INTERNAL":
            summary["reviewed_internal_count"] += 1
        elif knowledge_class == "LOCAL_PLATFORM_EVIDENCE":
            summary["local_platform_count"] += 1
        elif knowledge_class == "LEGACY_UNSOURCED":
            summary["legacy_unsourced_count"] += 1
        if evidence_kind == "predictive_ml_signal":
            summary["predictive_ml_count"] += 1
        elif evidence_kind == "platform_signal_snapshot":
            summary["platform_snapshot_count"] += 1
        elif evidence_kind == "approved_memory":
            summary["approved_memory_count"] += 1
        elif evidence_kind == "attachment_memory":
            summary["attachment_memory_count"] += 1
        elif evidence_kind == "mit_repo_capability":
            summary["repo_count"] += 1
        summary["citation_count"] += len(list(doc.get("citations") or []))
        summary["conflict_count"] += len(list(doc.get("conflict_ids") or []))
        if bool(doc.get("high_stakes")):
            summary["high_stakes_count"] += 1
        if summary["top_date"] is None:
            date_label = _result_date(doc)
            if date_label:
                summary["top_date"] = _normalize_date_label(date_label)
        for conflict in list(doc.get("conflict_details") or []):
            if isinstance(conflict, dict):
                conflict_id = str(conflict.get("conflict_id") or "").strip()
                if conflict_id and all(str(item.get("conflict_id") or "") != conflict_id for item in known_conflicts):
                    known_conflicts.append(conflict)
        summary["sources"].append(_source_reference(doc))
    summary["evidence_kinds"] = kinds
    summary["knowledge_classes"] = knowledge_classes
    summary["conflict_note"] = _conflict_note(results)
    summary["freshness_note"] = _freshness_note(results)
    summary["known_conflicts"] = known_conflicts
    return summary


def _bm25_query(query: str, top_k: int) -> list[dict[str, Any]]:
    try:
        from engines.ai.knowledge.unified_bm25_indexer import UnifiedBM25Indexer

        return UnifiedBM25Indexer.query(query, top_k=top_k)
    except Exception as exc:
        logger.warning("[UnifiedRetriever] Unified BM25 query failed: %s", exc)
        return []


def _faiss_query(query: str, top_k: int) -> list[dict[str, Any]]:
    try:
        from engines.ai.knowledge.unified_faiss_indexer import UnifiedFAISSIndexer

        return UnifiedFAISSIndexer.query(query, domain="ALL", top_k=top_k)
    except Exception as exc:
        logger.warning("[UnifiedRetriever] Unified FAISS query failed: %s", exc)
        return []


def _approved_core_query(query: str, top_k: int) -> list[dict[str, Any]]:
    try:
        from engines.ai.knowledge.approved_core_rag import retrieve_approved_core

        return retrieve_approved_core(query, top_k=top_k)
    except Exception as exc:
        logger.warning("[UnifiedRetriever] Approved-core query failed: %s", exc)
        return []
