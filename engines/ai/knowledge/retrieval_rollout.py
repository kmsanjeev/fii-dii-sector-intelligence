from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


_SOURCE_LABELS = {
    "approved_core": "approved core knowledge",
    "platform_intelligence": "platform intelligence",
    "user_reviewed": "approved memory",
    "attachment_chunk": "attachment memory",
    "mit_repo_capability": "MIT capability note",
}
_EVIDENCE_KIND_BY_SOURCE = {
    "approved_core": "approved_core_knowledge",
    "platform_intelligence": "platform_signal_snapshot",
    "user_reviewed": "approved_memory",
    "attachment_chunk": "attachment_memory",
    "mit_repo_capability": "mit_repo_capability",
}
_EVIDENCE_LABELS = {
    "approved_core_knowledge": "approved core knowledge",
    "predictive_ml_signal": "predictive ML signal",
    "platform_signal_snapshot": "platform signal snapshot",
    "approved_memory": "approved memory",
    "attachment_memory": "attachment memory",
    "mit_repo_capability": "MIT capability note",
    "descriptive_knowledge": "descriptive knowledge",
}
_POSITIVE_TERMS = {
    "accumulation",
    "bullish",
    "buy",
    "breakout",
    "emerging",
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


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return raw[:10] if len(raw) >= 10 else raw


def _clip_summary(text: Any, limit: int = 220) -> str | None:
    value = " ".join(str(text or "").strip().split())
    if not value:
        return None
    if len(value) <= limit:
        return value
    if limit <= 3:
        return value[:limit]
    return value[: limit - 3].rstrip() + "..."


def _source_label(source_type: str) -> str:
    return _SOURCE_LABELS.get(source_type, source_type or "knowledge")


def _evidence_kind(doc: dict[str, Any]) -> str:
    raw = str(doc.get("evidence_kind") or "").strip()
    if raw:
        return raw
    source_type = str(doc.get("source_type") or "").strip()
    return _EVIDENCE_KIND_BY_SOURCE.get(source_type, "descriptive_knowledge")


def _evidence_label(evidence_kind: str) -> str:
    return _EVIDENCE_LABELS.get(evidence_kind, evidence_kind or "knowledge")


def _source_title(doc: dict[str, Any]) -> str:
    meta = doc.get("meta", {}) or {}
    provenance = doc.get("provenance", {}) or meta.get("provenance", {}) or {}
    attachment_name = str(provenance.get("attachment_name") or meta.get("attachment_name") or "").strip()
    repo_label = str(provenance.get("repo_label") or meta.get("repo_label") or "").strip()
    source_title = str(provenance.get("source_title") or meta.get("source_title") or "").strip()
    entity = str(doc.get("entity") or "").strip()
    if attachment_name:
        return attachment_name
    if repo_label:
        return repo_label
    if source_title:
        return source_title
    if entity:
        return entity
    return str(doc.get("doc_id") or "Knowledge source").strip() or "Knowledge source"


def build_source_reference(doc: dict[str, Any]) -> dict[str, Any]:
    meta = doc.get("meta", {}) or {}
    provenance = doc.get("provenance", {}) or meta.get("provenance", {}) or {}
    source_type = str(doc.get("source_type") or meta.get("source_type") or "").strip()
    evidence_kind = _evidence_kind(doc)
    result_date = (
        doc.get("effective_date")
        or meta.get("effective_date")
        or doc.get("saved_at")
        or meta.get("saved_at")
    )
    return {
        "source_id": str(doc.get("doc_id") or "").strip(),
        "source_type": source_type,
        "source_label": _source_label(source_type),
        "evidence_kind": evidence_kind,
        "evidence_label": _evidence_label(evidence_kind),
        "knowledge_class": str(doc.get("knowledge_class") or meta.get("knowledge_class") or "").strip() or None,
        "domain": str(doc.get("domain") or meta.get("domain") or "UNKNOWN").strip() or "UNKNOWN",
        "title": _source_title(doc),
        "entity": str(doc.get("entity") or "").strip() or None,
        "date": _normalize_date(result_date),
        "freshness_class": str(doc.get("freshness_class") or meta.get("freshness_class") or "").strip() or None,
        "confidence": doc.get("confidence"),
        "summary": _clip_summary(doc.get("summary") or meta.get("summary") or doc.get("text") or "", 220),
        "attachment_name": str(provenance.get("attachment_name") or meta.get("attachment_name") or "").strip() or None,
        "repo_label": str(provenance.get("repo_label") or meta.get("repo_label") or "").strip() or None,
        "license_name": str(doc.get("license_name") or meta.get("license_name") or provenance.get("license_name") or "").strip() or None,
        "model_name": str(doc.get("model_name") or meta.get("model_name") or "").strip() or None,
        "model_version": str(doc.get("model_version") or meta.get("model_version") or "").strip() or None,
        "score_meaning": _clip_summary(doc.get("score_meaning") or meta.get("score_meaning") or "", 180),
        "reliability_note": _clip_summary(doc.get("reliability_note") or meta.get("reliability_note") or "", 180),
        "claim_ids": list(doc.get("claim_ids") or meta.get("claim_ids") or []),
        "passage_ids": list(doc.get("passage_ids") or meta.get("passage_ids") or []),
        "source_ids": list(doc.get("source_ids") or meta.get("source_ids") or []),
        "rule_ids": list(doc.get("rule_ids") or meta.get("rule_ids") or []),
        "conflict_ids": list(doc.get("conflict_ids") or meta.get("conflict_ids") or []),
        "version": str(doc.get("version") or meta.get("version") or "").strip() or None,
        "version_state": str(doc.get("version_state") or meta.get("version_state") or "").strip() or None,
        "high_stakes": bool(doc.get("high_stakes") or meta.get("high_stakes")),
        "authority": dict(doc.get("authority") or meta.get("authority") or {}),
        "citations": list(doc.get("citations") or meta.get("citations") or []),
        "citation_labels": list(doc.get("citation_labels") or meta.get("citation_labels") or []),
        "conflict_details": list(doc.get("conflict_details") or meta.get("conflict_details") or []),
        "rank": int(doc.get("rank") or 0),
    }


def summarize_sources(sources: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "used": bool(sources),
        "source_count": len(sources),
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
        "sources": sources,
        "conflict_note": None,
        "freshness_note": None,
        "known_conflicts": [],
    }
    seen_kinds: list[str] = []
    seen_classes: list[str] = []
    known_conflicts: list[dict[str, Any]] = []
    for source in sources:
        evidence_kind = str(source.get("evidence_kind") or "descriptive_knowledge")
        if evidence_kind not in seen_kinds:
            seen_kinds.append(evidence_kind)
        knowledge_class = str(source.get("knowledge_class") or "").strip()
        if knowledge_class and knowledge_class not in seen_classes:
            seen_classes.append(knowledge_class)
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
        summary["citation_count"] += len(list(source.get("citations") or []))
        summary["conflict_count"] += len(list(source.get("conflict_ids") or []))
        if bool(source.get("high_stakes")):
            summary["high_stakes_count"] += 1
        for conflict in list(source.get("conflict_details") or []):
            if not isinstance(conflict, dict):
                continue
            conflict_id = str(conflict.get("conflict_id") or "").strip()
            if conflict_id and all(str(item.get("conflict_id") or "") != conflict_id for item in known_conflicts):
                known_conflicts.append(conflict)
        if summary["top_date"] is None and source.get("date"):
            summary["top_date"] = source.get("date")
    summary["evidence_kinds"] = seen_kinds
    summary["knowledge_classes"] = seen_classes
    summary["conflict_note"] = _conflict_note(sources)
    summary["freshness_note"] = _freshness_note(sources)
    summary["known_conflicts"] = known_conflicts
    return summary


def _polarity(source: dict[str, Any]) -> str:
    haystack = " ".join(
        str(part or "")
        for part in [
            source.get("title"),
            source.get("summary"),
            source.get("score_meaning"),
            source.get("reliability_note"),
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


def _conflict_note(sources: list[dict[str, Any]]) -> str | None:
    groups: dict[str, dict[str, Any]] = {}
    for source in sources:
        key = str(source.get("entity") or source.get("title") or source.get("source_id") or "").strip().upper()
        if not key:
            continue
        entry = groups.setdefault(
            key,
            {
                "title": str(source.get("title") or source.get("entity") or "this topic"),
                "polarities": set(),
                "source_labels": set(),
            },
        )
        polarity = _polarity(source)
        if polarity in {"positive", "negative"}:
            entry["polarities"].add(polarity)
            entry["source_labels"].add(str(source.get("source_label") or "knowledge"))
    for entry in groups.values():
        if {"positive", "negative"}.issubset(entry["polarities"]):
            label_text = ", ".join(sorted(entry["source_labels"])[:3]) or "local sources"
            return (
                f"Local sources disagree on {entry['title']}. Some evidence looks supportive while other "
                f"evidence is cautious or negative. Check dates and source labels before treating it as settled. "
                f"Main source types involved: {label_text}."
            )
    return None


def _freshness_note(sources: list[dict[str, Any]]) -> str | None:
    unique_dates = list(dict.fromkeys(str(source.get("date") or "").strip() for source in sources if source.get("date")))
    has_memory = any(str(source.get("source_type") or "") in {"user_reviewed", "attachment_chunk"} for source in sources)
    has_platform = any(str(source.get("source_type") or "") == "platform_intelligence" for source in sources)
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


def build_legacy_bundle(
    *,
    reviewed_results: list[dict[str, Any]],
    repo_results: list[dict[str, Any]],
    legacy_results: list[dict[str, Any]],
    reviewed_context: str,
    repo_context: str,
) -> dict[str, Any]:
    normalized_results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    def _append_many(raw_results: list[dict[str, Any]], *, default_source_type: str | None = None) -> None:
        for rank, raw_doc in enumerate(raw_results, start=1):
            doc = dict(raw_doc)
            if default_source_type and not str(doc.get("source_type") or "").strip():
                doc["source_type"] = default_source_type
            doc_id = str(doc.get("doc_id") or "").strip()
            if doc_id and doc_id in seen_ids:
                continue
            if doc_id:
                seen_ids.add(doc_id)
            doc["rank"] = len(normalized_results) + 1
            if not doc.get("summary"):
                doc["summary"] = str(doc.get("text") or "").strip()[:220]
            normalized_results.append(doc)

    _append_many(reviewed_results)
    _append_many(repo_results)
    _append_many(legacy_results, default_source_type="platform_intelligence")

    rag_context = ""
    if legacy_results:
        rag_context = "\n".join(f"- {str(result.get('text') or '').strip()[:300]}" for result in legacy_results)
        if rag_context:
            rag_context = f"Relevant intelligence context:\n{rag_context}"

    blocks = [part for part in [reviewed_context, repo_context, rag_context] if part]
    references = [build_source_reference(doc) for doc in normalized_results]
    return {
        "context": "\n\n".join(blocks),
        "summary": summarize_sources(references),
        "results": normalized_results,
    }


def attribution_quality_score(sources: list[dict[str, Any]]) -> float:
    if not sources:
        return 0.0
    total = 0.0
    for source in sources:
        present = 0
        for key in ("source_id", "source_type", "title", "domain", "summary", "date"):
            if str(source.get(key) or "").strip():
                present += 1
        total += present / 6.0
    return round(total / len(sources), 3)


def duplicate_noise_score(sources: list[dict[str, Any]]) -> float:
    if not sources:
        return 0.0
    unique_ids = {str(source.get("source_id") or "").strip() for source in sources if str(source.get("source_id") or "").strip()}
    duplicates = max(len(sources) - len(unique_ids), 0)
    return round(duplicates / len(sources), 3)


def build_retrieval_audit(
    *,
    configured_primary_mode: str,
    resolved_primary_mode: str,
    primary_bundle: dict[str, Any] | None,
    shadow_mode: str | None,
    shadow_bundle: dict[str, Any] | None,
    primary_error: str | None = None,
    shadow_error: str | None = None,
) -> dict[str, Any]:
    primary_sources = list(((primary_bundle or {}).get("summary") or {}).get("sources") or [])
    shadow_sources = list(((shadow_bundle or {}).get("summary") or {}).get("sources") or [])
    primary_ids = {str(source.get("source_id") or "").strip() for source in primary_sources if str(source.get("source_id") or "").strip()}
    shadow_ids = {str(source.get("source_id") or "").strip() for source in shadow_sources if str(source.get("source_id") or "").strip()}
    shared_ids = sorted(primary_ids & shadow_ids)
    primary_only = [
        str(source.get("title") or source.get("source_id") or "").strip()
        for source in primary_sources
        if str(source.get("source_id") or "").strip() not in shadow_ids
    ][:5]
    shadow_only = [
        str(source.get("title") or source.get("source_id") or "").strip()
        for source in shadow_sources
        if str(source.get("source_id") or "").strip() not in primary_ids
    ][:5]
    overlap_denominator = max(len(primary_ids | shadow_ids), 1)
    overlap_rate = round(len(shared_ids) / overlap_denominator, 3) if (primary_ids or shadow_ids) else 0.0
    notes: list[str] = []
    if primary_error:
        notes.append(f"Primary retrieval error: {primary_error}")
    if shadow_error:
        notes.append(f"Shadow retrieval error: {shadow_error}")
    if primary_sources and shadow_sources and overlap_rate < 0.4:
        notes.append("Primary and shadow retrieval overlap is low. Review before full cutover.")
    if any(source.get("source_type") in {"user_reviewed", "attachment_chunk"} for source in primary_sources) and not any(
        source.get("source_type") in {"user_reviewed", "attachment_chunk"} for source in shadow_sources
    ):
        notes.append("Shadow retrieval missed saved memory or attachment memory that the primary path used.")
    if attribution_quality_score(shadow_sources) > attribution_quality_score(primary_sources) + 0.15:
        notes.append("Shadow retrieval kept richer source attribution than the primary path.")
    return {
        "shadow_enabled": bool(shadow_mode),
        "configured_primary_mode": configured_primary_mode,
        "resolved_primary_mode": resolved_primary_mode,
        "primary_used": bool(primary_sources),
        "primary_source_count": len(primary_sources),
        "primary_approved_core_hits": sum(1 for source in primary_sources if source.get("knowledge_class") == "APPROVED_CORE"),
        "primary_reviewed_internal_hits": sum(1 for source in primary_sources if source.get("knowledge_class") == "REVIEWED_INTERNAL"),
        "primary_local_platform_hits": sum(1 for source in primary_sources if source.get("knowledge_class") == "LOCAL_PLATFORM_EVIDENCE"),
        "primary_ml_hits": sum(1 for source in primary_sources if source.get("evidence_kind") == "predictive_ml_signal"),
        "primary_conflict_count": sum(len(list(source.get("conflict_ids") or [])) for source in primary_sources),
        "primary_citation_count": sum(len(list(source.get("citations") or [])) for source in primary_sources),
        "primary_attribution_quality": attribution_quality_score(primary_sources),
        "primary_duplicate_noise": duplicate_noise_score(primary_sources),
        "shadow_mode": shadow_mode,
        "shadow_used": bool(shadow_sources),
        "shadow_source_count": len(shadow_sources),
        "shadow_approved_core_hits": sum(1 for source in shadow_sources if source.get("knowledge_class") == "APPROVED_CORE"),
        "shadow_reviewed_internal_hits": sum(1 for source in shadow_sources if source.get("knowledge_class") == "REVIEWED_INTERNAL"),
        "shadow_local_platform_hits": sum(1 for source in shadow_sources if source.get("knowledge_class") == "LOCAL_PLATFORM_EVIDENCE"),
        "shadow_ml_hits": sum(1 for source in shadow_sources if source.get("evidence_kind") == "predictive_ml_signal"),
        "shadow_conflict_count": sum(len(list(source.get("conflict_ids") or [])) for source in shadow_sources),
        "shadow_citation_count": sum(len(list(source.get("citations") or [])) for source in shadow_sources),
        "shadow_attribution_quality": attribution_quality_score(shadow_sources),
        "shadow_duplicate_noise": duplicate_noise_score(shadow_sources),
        "overlap_count": len(shared_ids),
        "overlap_rate": overlap_rate,
        "only_in_primary": [item for item in primary_only if item],
        "only_in_shadow": [item for item in shadow_only if item],
        "notes": notes,
        "primary_error": primary_error,
        "shadow_error": shadow_error,
    }


def append_shadow_audit(path: Path, *, query: str, audit: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "created_at": _utc_now(),
        "query": str(query or "").strip()[:800],
        **audit,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
