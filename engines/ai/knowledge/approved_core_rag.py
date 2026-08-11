from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from engines.ai.research.platform.contracts import CoreVersionState, ResearchCoreKnowledgeRecord
from engines.ai.research.platform.service import get_research_platform_service
from engines.common import config as cfg

ASTROLOGY_QUERY_TERMS = {
    "astrology",
    "astrofinance",
    "ayanamsha",
    "bhava",
    "chart",
    "conjunction",
    "dasha",
    "debilitation",
    "dosha",
    "drishti",
    "gochara",
    "graha",
    "guru",
    "house",
    "jupiter",
    "jyotisha",
    "karaka",
    "ketu",
    "lagna",
    "lordship",
    "mahadasha",
    "manglik",
    "mars",
    "moon",
    "nakshatra",
    "navamsha",
    "pada",
    "parashara",
    "planet",
    "rahu",
    "rashi",
    "saturn",
    "shani",
    "shukra",
    "sun",
    "transit",
    "upaya",
    "varga",
    "vedic",
    "venus",
    "vimshottari",
    "yoga",
}


def _normalize_text(value: Any) -> str:
    lowered = str(value or "").lower().replace("’", "'").replace("`", "'")
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokenize(value: Any) -> list[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return []
    return normalized.split()


def _clip(value: Any, limit: int = 240) -> str:
    compact = " ".join(str(value or "").strip().split())
    if len(compact) <= limit:
        return compact
    if limit <= 3:
        return compact[:limit]
    return compact[: limit - 3].rstrip() + "..."


def _topic_domain(topic_key: str | None) -> str:
    raw = str(topic_key or "").strip()
    if "::" in raw:
        return raw.split("::", 1)[0] or "ASTROLOGY"
    return raw or "ASTROLOGY"


def _unique(values: list[str]) -> list[str]:
    ordered: list[str] = []
    for item in values:
        cleaned = str(item or "").strip()
        if cleaned and cleaned not in ordered:
            ordered.append(cleaned)
    return ordered


@lru_cache(maxsize=8)
def _load_json_files(root_str: str) -> dict[str, dict[str, Any]]:
    root = Path(root_str)
    if not root.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        key = (
            payload.get("source_id")
            or payload.get("passage_id")
            or payload.get("claim_id")
            or payload.get("conflict_id")
            or payload.get("rule_id")
        )
        if key:
            records[str(key)] = payload
    return records


@lru_cache(maxsize=4)
def _load_approved_rules(root_str: str) -> dict[str, dict[str, Any]]:
    root = Path(root_str)
    if not root.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        rule_id = str(payload.get("rule_id") or "").strip()
        if rule_id:
            records[rule_id] = payload
    return records


@lru_cache(maxsize=4)
def _load_ontology_aliases(root_str: str) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]]]:
    root = Path(root_str)
    entity_index: dict[str, dict[str, Any]] = {}
    aliases: dict[str, str] = {}
    if not root.exists():
        return entity_index, []

    for path in sorted(root.rglob("*.json")):
        if "relations" in path.parts:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, list):
            continue
        for item in payload:
            entity_id = str(item.get("entity_id") or "").strip()
            if not entity_id:
                continue
            entity_index[entity_id] = item
            names = [
                item.get("canonical_name"),
                item.get("sanskrit_name"),
                item.get("transliteration"),
                *(item.get("aliases") or []),
                *(item.get("deprecated_aliases") or []),
            ]
            for name in names:
                normalized = _normalize_text(name)
                if normalized:
                    aliases[normalized] = entity_id
    alias_rows = sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True)
    return entity_index, alias_rows


@lru_cache(maxsize=4)
def _build_claim_to_conflicts(conflict_root_str: str) -> dict[str, list[str]]:
    conflicts = _load_json_files(conflict_root_str)
    mapping: dict[str, list[str]] = {}
    for conflict_id, payload in conflicts.items():
        for claim_field in ("claim_a", "claim_b"):
            claim_id = str(payload.get(claim_field) or "").strip()
            if not claim_id:
                continue
            mapping.setdefault(claim_id, []).append(conflict_id)
    return mapping


def _source_map() -> dict[str, dict[str, Any]]:
    return _load_json_files(str(cfg.VEDA_ASTROLOGY_SOURCE_DIR))


def _passage_map() -> dict[str, dict[str, Any]]:
    return _load_json_files(str(cfg.VEDA_ASTROLOGY_PASSAGE_DIR))


def _claim_map() -> dict[str, dict[str, Any]]:
    return _load_json_files(str(cfg.VEDA_ASTROLOGY_CLAIM_DIR))


def _conflict_map() -> dict[str, dict[str, Any]]:
    return _load_json_files(str(cfg.VEDA_ASTROLOGY_CONFLICT_DIR))


def _rule_map() -> dict[str, dict[str, Any]]:
    return _load_approved_rules(str(cfg.VEDA_ASTROLOGY_RULE_APPROVED_DIR))


def _claim_to_conflicts() -> dict[str, list[str]]:
    return _build_claim_to_conflicts(str(cfg.VEDA_ASTROLOGY_CONFLICT_DIR))


def _query_ontology(query: str) -> dict[str, Any]:
    entity_index, alias_rows = _load_ontology_aliases(str(cfg.VEDA_ASTROLOGY_ONTOLOGY_DIR))
    normalized_query = _normalize_text(query)
    matched_aliases: list[dict[str, Any]] = []
    matched_entity_ids: list[str] = []
    expanded_tokens = set(_tokenize(query))

    for alias, entity_id in alias_rows:
        if not alias:
            continue
        if f" {alias} " not in f" {normalized_query} ":
            continue
        if entity_id in matched_entity_ids:
            continue
        entity = entity_index.get(entity_id, {})
        matched_entity_ids.append(entity_id)
        matched_aliases.append(
            {
                "entity_id": entity_id,
                "alias": alias,
                "canonical_name": entity.get("canonical_name"),
                "entity_type": entity.get("entity_type"),
            }
        )
        for candidate in [
            entity.get("canonical_name"),
            entity.get("sanskrit_name"),
            entity.get("transliteration"),
            *(entity.get("aliases") or []),
        ]:
            expanded_tokens.update(_tokenize(candidate))

    return {
        "query": query,
        "normalized_query": normalized_query,
        "query_tokens": sorted(set(_tokenize(query))),
        "expanded_tokens": sorted(expanded_tokens),
        "ontology_matches": matched_aliases,
    }


def _is_astrology_query(query: str, ontology: dict[str, Any]) -> bool:
    if ontology.get("ontology_matches"):
        return True
    query_tokens = set(ontology.get("query_tokens") or _tokenize(query))
    return bool(query_tokens & ASTROLOGY_QUERY_TERMS)


def _citation_type(source_payload: dict[str, Any]) -> str:
    source_class = str(source_payload.get("source_class") or "").upper()
    if source_class == "CLASSICAL_PRIMARY":
        return "PRIMARY_TEXT_CITATION"
    if source_class == "CLASSICAL_COMMENTARY":
        return "COMMENTARY_CITATION"
    if source_class:
        return "SECONDARY_CITATION"
    return "INTERNAL_APPROVED_CLAIM"


def _source_authority(source_payload: dict[str, Any]) -> dict[str, Any]:
    authority_profile = dict(source_payload.get("authority_profile") or {})
    authority_score = authority_profile.get("authority_score")
    if authority_score is None:
        authority_score = source_payload.get("authority_score")
    try:
        score_value = float(authority_score) if authority_score is not None else None
    except (TypeError, ValueError):
        score_value = None
    if score_value is not None and score_value > 1.0:
        score_value = round(score_value / 100.0, 4)
    elif score_value is not None:
        score_value = round(score_value, 4)
    return {
        "source_class": source_payload.get("source_class"),
        "authority_tier": authority_profile.get("authority_tier"),
        "authority_score": score_value,
        "quality_grade": source_payload.get("quality_grade"),
        "verification_status": source_payload.get("verification_status"),
    }


def _format_verse(passage_payload: dict[str, Any]) -> str | None:
    start = passage_payload.get("verse_start")
    end = passage_payload.get("verse_end")
    if start and end and start != end:
        return f"{start}-{end}"
    return str(start or end or "").strip() or None


def _format_page(passage_payload: dict[str, Any]) -> str | None:
    start = passage_payload.get("page_start")
    end = passage_payload.get("page_end")
    if start and end and start != end:
        return f"{start}-{end}"
    return str(start or end or "").strip() or None


def _build_citations(
    *,
    claim_ids: list[str],
    rule_ids: list[str],
    source_ids: list[str],
    passage_ids: list[str],
) -> list[dict[str, Any]]:
    sources = _source_map()
    passages = _passage_map()
    citations: list[dict[str, Any]] = []

    for passage_id in passage_ids:
        passage = passages.get(passage_id)
        if passage is None:
            continue
        source = sources.get(str(passage.get("source_id") or "").strip(), {})
        citations.append(
            {
                "citation_id": f"CIT-{passage_id}",
                "citation_type": _citation_type(source),
                "source_id": source.get("source_id"),
                "passage_id": passage_id,
                "claim_id": claim_ids[0] if claim_ids else None,
                "rule_id": rule_ids[0] if rule_ids else None,
                "work": source.get("title_normalized"),
                "author": source.get("author"),
                "chapter": passage.get("chapter"),
                "section": passage.get("section"),
                "verse": _format_verse(passage),
                "page": _format_page(passage),
                "edition": source.get("edition"),
                "translator": source.get("translator"),
                "publisher": source.get("publisher"),
                "source_uri": source.get("digital_source"),
                "verification_status": passage.get("verification_status") or source.get("verification_status"),
                "retrieved_at": source.get("updated_at") or source.get("created_at"),
                "citation_label": passage.get("citation_label"),
                "excerpt": _clip(
                    passage.get("translation")
                    or passage.get("original_text")
                    or passage.get("context_after")
                    or passage.get("context_before"),
                    280,
                ),
                "support_type": "PASSAGE",
                "authority": _source_authority(source),
            }
        )

    if citations:
        return citations

    for source_id in source_ids:
        source = sources.get(source_id)
        if source is None:
            continue
        citations.append(
            {
                "citation_id": f"CIT-{source_id}",
                "citation_type": _citation_type(source),
                "source_id": source_id,
                "passage_id": None,
                "claim_id": claim_ids[0] if claim_ids else None,
                "rule_id": rule_ids[0] if rule_ids else None,
                "work": source.get("title_normalized"),
                "author": source.get("author"),
                "chapter": None,
                "section": None,
                "verse": None,
                "page": None,
                "edition": source.get("edition"),
                "translator": source.get("translator"),
                "publisher": source.get("publisher"),
                "source_uri": source.get("digital_source"),
                "verification_status": source.get("verification_status"),
                "retrieved_at": source.get("updated_at") or source.get("created_at"),
                "citation_label": source.get("title_normalized"),
                "excerpt": None,
                "support_type": "SOURCE",
                "authority": _source_authority(source),
            }
        )
    return citations


def _derive_lineage(record: ResearchCoreKnowledgeRecord) -> dict[str, Any]:
    claims = _claim_map()
    rules = _rule_map()
    passages = _passage_map()
    claim_ids = list(record.claim_ids)
    rule_ids = list(record.rule_ids)

    if record.domain_id == "VEDA-DOMAIN-VEDIC-ASTROLOGY":
        topic_key = str(record.topic_key or "").upper()
        normalized_claim = _normalize_text(record.claim)
        normalized_title = _normalize_text(record.title)
        for claim_id, payload in claims.items():
            claim_topic = f"{str(payload.get('domain') or '').upper()}::{str(payload.get('subdomain') or '').upper()}"
            if claim_topic == topic_key or _normalize_text(payload.get("claim_text")) == normalized_claim:
                if claim_id not in claim_ids:
                    claim_ids.append(claim_id)
        for rule_id, payload in rules.items():
            rule_topic = f"{str(payload.get('domain') or '').upper()}::{str(payload.get('subdomain') or '').upper()}"
            if rule_topic == topic_key or _normalize_text(payload.get("title")) == normalized_title:
                if rule_id not in rule_ids:
                    rule_ids.append(rule_id)

    source_ids = list(record.source_ids)
    passage_ids = list(record.passage_ids)
    conflict_ids = list(record.conflict_ids)

    for claim_id in claim_ids:
        claim = claims.get(claim_id)
        if claim is None:
            continue
        passage_ids.extend(list(claim.get("source_passages") or []))
        for conflict_id in _claim_to_conflicts().get(claim_id, []):
            conflict_ids.append(conflict_id)
        for conflicting_claim_id in claim.get("conflicting_claims") or []:
            for linked_conflict_id in _claim_to_conflicts().get(str(conflicting_claim_id), []):
                conflict_ids.append(linked_conflict_id)

    for rule_id in rule_ids:
        rule = rules.get(rule_id)
        if rule is None:
            continue
        provenance = dict(rule.get("provenance") or {})
        source_ids.extend(list(provenance.get("source_ids") or []))
        passage_ids.extend(list(provenance.get("passage_ids") or []))
        claim_ids.extend(list(provenance.get("claim_ids") or []))
        conflict_ids.extend(list(provenance.get("conflict_ids") or []))

    for passage_id in passage_ids:
        passage = passages.get(passage_id)
        if passage is None:
            continue
        source_ids.append(str(passage.get("source_id") or "").strip())

    claim_ids = _unique(claim_ids)
    rule_ids = _unique(rule_ids)
    passage_ids = _unique(passage_ids)
    source_ids = _unique(source_ids)
    conflict_ids = _unique(conflict_ids)

    return {
        "claim_ids": claim_ids,
        "rule_ids": rule_ids,
        "passage_ids": passage_ids,
        "source_ids": source_ids,
        "conflict_ids": conflict_ids,
    }


def _build_conflict_details(conflict_ids: list[str]) -> list[dict[str, Any]]:
    conflicts = _conflict_map()
    details: list[dict[str, Any]] = []
    for conflict_id in conflict_ids:
        payload = conflicts.get(conflict_id)
        if payload is None:
            continue
        details.append(
            {
                "conflict_id": conflict_id,
                "topic": payload.get("topic"),
                "conflict_type": payload.get("conflict_type"),
                "resolution_status": payload.get("resolution_status"),
                "approved_resolution": payload.get("approved_resolution"),
                "analysis": _clip(payload.get("analysis"), 260),
            }
        )
    return details


def _source_class_diversity(source_ids: list[str]) -> dict[str, int]:
    sources = _source_map()
    counts: dict[str, int] = {}
    for source_id in source_ids:
        payload = sources.get(source_id)
        source_class = str((payload or {}).get("source_class") or "UNKNOWN")
        counts[source_class] = counts.get(source_class, 0) + 1
    return counts


def _build_search_text(
    record: ResearchCoreKnowledgeRecord,
    *,
    citations: list[dict[str, Any]],
    conflict_details: list[dict[str, Any]],
) -> str:
    parts = [
        record.title,
        record.claim,
        record.normalized_claim,
        record.topic_key,
        _topic_domain(record.topic_key),
        " ".join(record.source_ids),
        " ".join(record.claim_ids),
        " ".join(record.rule_ids),
        " ".join(record.passage_ids),
        " ".join(record.conflict_ids),
    ]
    for citation in citations:
        parts.extend(
            [
                citation.get("work"),
                citation.get("author"),
                citation.get("chapter"),
                citation.get("section"),
                citation.get("verse"),
                citation.get("page"),
                citation.get("citation_label"),
                citation.get("excerpt"),
            ]
        )
    for conflict in conflict_details:
        parts.extend([conflict.get("topic"), conflict.get("analysis"), conflict.get("approved_resolution")])
    return _normalize_text(" ".join(str(part or "") for part in parts if str(part or "").strip()))


def _score_record(
    record: ResearchCoreKnowledgeRecord,
    *,
    query_tokens: set[str],
    expanded_tokens: set[str],
    search_text: str,
    ontology_matches: list[dict[str, Any]],
) -> float:
    if not search_text:
        return 0.0
    doc_tokens = set(search_text.split())
    base_overlap = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)
    expanded_overlap = len(expanded_tokens & doc_tokens) / max(len(expanded_tokens), 1)
    phrase_boost = 0.18 if _normalize_text(record.title) in search_text or _normalize_text(record.claim) in search_text else 0.0
    ontology_boost = 0.0
    for match in ontology_matches:
        canonical_name = _normalize_text(match.get("canonical_name"))
        alias = _normalize_text(match.get("alias"))
        if canonical_name and canonical_name in search_text:
            ontology_boost += 0.06
        elif alias and alias in search_text:
            ontology_boost += 0.04
    confidence = record.confidence
    authority_score = (
        float(confidence.authority_confidence)
        + float(confidence.cross_source_confidence)
        + float(confidence.provenance_confidence)
        + float(confidence.domain_confidence)
    ) / 4.0
    version_boost = 0.03 if record.version_state == CoreVersionState.CURRENT else -0.25
    return round(
        (base_overlap * 0.56)
        + (expanded_overlap * 0.18)
        + ontology_boost
        + (authority_score * 0.16)
        + phrase_boost
        + version_boost,
        6,
    )


def _enrich_record(record: ResearchCoreKnowledgeRecord, *, search_text: str) -> dict[str, Any]:
    lineage = _derive_lineage(record)
    citations = _build_citations(
        claim_ids=lineage["claim_ids"],
        rule_ids=lineage["rule_ids"],
        source_ids=lineage["source_ids"],
        passage_ids=lineage["passage_ids"],
    )
    conflict_details = _build_conflict_details(lineage["conflict_ids"])
    summary = _clip(record.claim, 220)
    citation_labels = [
        str(citation.get("citation_label") or citation.get("work") or citation.get("source_id") or "").strip()
        for citation in citations
        if str(citation.get("citation_label") or citation.get("work") or citation.get("source_id") or "").strip()
    ]
    source_classes = _source_class_diversity(lineage["source_ids"])
    return {
        "doc_id": f"veda_core_{record.core_id.lower().replace('-', '_')}",
        "source_type": "approved_core",
        "knowledge_class": "APPROVED_CORE",
        "domain": _topic_domain(record.topic_key),
        "entity": record.title,
        "text": record.claim,
        "summary": summary,
        "tags": ["approved_core", str(_topic_domain(record.topic_key)).lower()],
        "approval_state": "admin_promoted_core",
        "evidence_kind": "approved_core_knowledge",
        "freshness_class": "governed_core",
        "saved_at": record.updated_at,
        "effective_date": record.updated_at[:10] if record.updated_at else None,
        "version": record.version,
        "version_state": record.version_state.value,
        "high_stakes": bool(record.high_stakes),
        "confidence": round(float(record.confidence.domain_confidence), 4),
        "authority": {
            "source_confidence": round(float(record.confidence.source_confidence), 4),
            "authority_confidence": round(float(record.confidence.authority_confidence), 4),
            "cross_source_confidence": round(float(record.confidence.cross_source_confidence), 4),
            "provenance_confidence": round(float(record.confidence.provenance_confidence), 4),
            "domain_confidence": round(float(record.confidence.domain_confidence), 4),
            "source_class_diversity": source_classes,
        },
        "claim_ids": lineage["claim_ids"],
        "passage_ids": lineage["passage_ids"],
        "source_ids": lineage["source_ids"],
        "rule_ids": lineage["rule_ids"],
        "conflict_ids": lineage["conflict_ids"],
        "citations": citations,
        "citation_labels": _unique(citation_labels),
        "conflict_details": conflict_details,
        "search_text": search_text,
        "reliability_note": (
            "Approved core knowledge is governed Veda knowledge promoted after Admin approval. "
            "Treat it separately from temporary external research."
        ),
        "provenance": {
            "source_kind": "approved_core_knowledge",
            "source_label": "approved_core",
            "source_title": record.title,
            "source_date": record.updated_at[:10] if record.updated_at else None,
            "details": {
                "governance_zone": "APPROVED_CORE",
                "core_id": record.core_id,
                "candidate_id": record.candidate_id,
                "approval_id": record.approval_id,
                "promotion_id": record.promotion_id,
                "claim_ids": lineage["claim_ids"],
                "passage_ids": lineage["passage_ids"],
                "source_ids": lineage["source_ids"],
                "rule_ids": lineage["rule_ids"],
                "conflict_ids": lineage["conflict_ids"],
                "version": record.version,
                "version_state": record.version_state.value,
                "high_stakes": bool(record.high_stakes),
            },
        },
    }


class ApprovedCoreKnowledgeRetriever:
    def __init__(self, *, domain_id: str | None = "VEDA-DOMAIN-VEDIC-ASTROLOGY"):
        self.domain_id = domain_id

    def query(self, query: str, *, top_k: int = 6) -> list[dict[str, Any]]:
        diagnostics = self.diagnostics(query, top_k=top_k)
        return list(diagnostics["results"])

    def diagnostics(self, query: str, *, top_k: int = 6) -> dict[str, Any]:
        service = get_research_platform_service()
        ontology = _query_ontology(query)
        if not _is_astrology_query(query, ontology):
            return {
                "query": query,
                "results": [],
                "ontology_matches": ontology["ontology_matches"],
                "ontology_gaps": [],
                "source_class_diversity": {},
                "reason": "non_astrology_query",
            }
        query_tokens = set(ontology["query_tokens"])
        expanded_tokens = set(ontology["expanded_tokens"])
        results: list[dict[str, Any]] = []

        core_records = service.store.list_all_core_knowledge()
        for record in core_records:
            if self.domain_id and record.domain_id != self.domain_id:
                continue
            if record.version_state != CoreVersionState.CURRENT:
                continue
            search_text = _build_search_text(
                record,
                citations=_build_citations(
                    claim_ids=_derive_lineage(record)["claim_ids"],
                    rule_ids=_derive_lineage(record)["rule_ids"],
                    source_ids=_derive_lineage(record)["source_ids"],
                    passage_ids=_derive_lineage(record)["passage_ids"],
                ),
                conflict_details=_build_conflict_details(_derive_lineage(record)["conflict_ids"]),
            )
            score = _score_record(
                record,
                query_tokens=query_tokens,
                expanded_tokens=expanded_tokens,
                search_text=search_text,
                ontology_matches=ontology["ontology_matches"],
            )
            if score <= 0:
                continue
            enriched = _enrich_record(record, search_text=search_text)
            enriched["retrieval_method"] = "approved_core_store"
            enriched["retrieval_score"] = score
            enriched["normalized_score"] = score
            enriched["fusion_reason"] = "approved_core_direct_match"
            results.append(enriched)

        results.sort(
            key=lambda item: (
                float(item.get("retrieval_score") or 0.0),
                float((item.get("authority") or {}).get("domain_confidence") or 0.0),
                str(item.get("saved_at") or ""),
                str(item.get("doc_id") or ""),
            ),
            reverse=True,
        )
        for rank, item in enumerate(results[: max(int(top_k), 1)], start=1):
            item["approved_core_rank"] = rank
            item["rank"] = rank

        source_class_diversity: dict[str, int] = {}
        for item in results[: max(int(top_k), 1)]:
            for source_class, count in (item.get("authority") or {}).get("source_class_diversity", {}).items():
                source_class_diversity[source_class] = source_class_diversity.get(source_class, 0) + int(count)

        return {
            "query": query,
            "results": results[: max(int(top_k), 1)],
            "ontology_matches": ontology["ontology_matches"],
            "ontology_gaps": [],
            "source_class_diversity": source_class_diversity,
        }


def retrieve_approved_core(query: str, *, top_k: int = 6, domain_id: str | None = "VEDA-DOMAIN-VEDIC-ASTROLOGY") -> list[dict[str, Any]]:
    return ApprovedCoreKnowledgeRetriever(domain_id=domain_id).query(query, top_k=top_k)


def diagnose_approved_core_query(query: str, *, top_k: int = 6, domain_id: str | None = "VEDA-DOMAIN-VEDIC-ASTROLOGY") -> dict[str, Any]:
    return ApprovedCoreKnowledgeRetriever(domain_id=domain_id).diagnostics(query, top_k=top_k)
