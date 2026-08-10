from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engines.common import config as cfg

CONTRACT_VERSION = getattr(cfg, "VEDA_KNOWLEDGE_CONTRACT_VERSION", "2026-08-04")

_PLATFORM_DOMAINS = {"MARKET", "SECTOR", "STOCK", "DEAL", "CORPORATE", "ASTRO"}


def _compact_text(value: Any, limit: int) -> str:
    compact = " ".join(str(value or "").strip().split())
    return compact[:limit].strip()


def _slug(value: Any) -> str:
    raw = "".join(ch.lower() if str(ch).isalnum() else "_" for ch in str(value or ""))
    while "__" in raw:
        raw = raw.replace("__", "_")
    return raw.strip("_")


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _unique_tags(*values: Any) -> list[str]:
    tags: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            for item in value:
                cleaned = _slug(item)
                if cleaned and cleaned not in tags:
                    tags.append(cleaned)
            continue
        cleaned = _slug(value)
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
    return tags


def _coerce_meta(doc: dict[str, Any]) -> dict[str, Any]:
    meta = doc.get("meta")
    if isinstance(meta, dict):
        return dict(meta)
    metadata = doc.get("metadata")
    if isinstance(metadata, dict):
        return dict(metadata)
    return {}


@dataclass(slots=True)
class KnowledgeEntityKeys:
    symbol: str | None = None
    sector: str | None = None
    theme: str | None = None
    topic: str | None = None
    regime: str | None = None
    intent: str | None = None
    repo_label: str | None = None
    attachment_name: str | None = None
    parent_doc_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "sector": self.sector,
            "theme": self.theme,
            "topic": self.topic,
            "regime": self.regime,
            "intent": self.intent,
            "repo_label": self.repo_label,
            "attachment_name": self.attachment_name,
            "parent_doc_id": self.parent_doc_id,
        }


@dataclass(slots=True)
class KnowledgeFreshness:
    classification: str = "unknown"
    effective_date: str | None = None
    saved_at: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "effective_date": self.effective_date,
            "saved_at": self.saved_at,
            "note": self.note,
        }


@dataclass(slots=True)
class KnowledgeProvenance:
    source_kind: str
    source_label: str | None = None
    storage_key: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    source_date: str | None = None
    repo_label: str | None = None
    license_name: str | None = None
    attachment_name: str | None = None
    attachment_storage_key: str | None = None
    attachment_hash: str | None = None
    parent_doc_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "source_label": self.source_label,
            "storage_key": self.storage_key,
            "source_title": self.source_title,
            "source_url": self.source_url,
            "source_date": self.source_date,
            "repo_label": self.repo_label,
            "license_name": self.license_name,
            "attachment_name": self.attachment_name,
            "attachment_storage_key": self.attachment_storage_key,
            "attachment_hash": self.attachment_hash,
            "parent_doc_id": self.parent_doc_id,
            "details": self.details,
        }


@dataclass(slots=True)
class KnowledgeEvidenceRecord:
    doc_id: str
    source_type: str
    domain: str
    entity: str
    text: str
    summary: str
    entity_keys: KnowledgeEntityKeys = field(default_factory=KnowledgeEntityKeys)
    tags: list[str] = field(default_factory=list)
    confidence: float | None = None
    approval_state: str = "unknown"
    evidence_kind: str = "descriptive_knowledge"
    provenance: KnowledgeProvenance = field(
        default_factory=lambda: KnowledgeProvenance(source_kind="unknown")
    )
    freshness: KnowledgeFreshness = field(default_factory=KnowledgeFreshness)
    license_name: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    score_meaning: str | None = None
    reliability_note: str | None = None
    contract_version: str = CONTRACT_VERSION

    @property
    def saved_at(self) -> str | None:
        return self.freshness.saved_at

    @property
    def effective_date(self) -> str | None:
        return self.freshness.effective_date

    @property
    def freshness_class(self) -> str:
        return self.freshness.classification

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "doc_id": self.doc_id,
            "source_type": self.source_type,
            "domain": self.domain,
            "entity": self.entity,
            "entity_keys": self.entity_keys.to_dict(),
            "text": self.text,
            "summary": self.summary,
            "tags": list(self.tags),
            "saved_at": self.saved_at,
            "effective_date": self.effective_date,
            "freshness_class": self.freshness_class,
            "freshness": self.freshness.to_dict(),
            "confidence": self.confidence,
            "evidence_kind": self.evidence_kind,
            "provenance": self.provenance.to_dict(),
            "approval_state": self.approval_state,
            "license_name": self.license_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "score_meaning": self.score_meaning,
            "reliability_note": self.reliability_note,
        }


def _is_predictive_ml_platform_doc(domain: str, meta: dict[str, Any], text: str) -> bool:
    if domain != "STOCK":
        return False
    if str(meta.get("model_name") or "").strip() or str(meta.get("model_version") or "").strip():
        return True
    if any(_as_float(meta.get(field_name)) is not None for field_name in ("ml_bull_run_score", "accumulation_score", "bull_run_score")):
        return True
    lowered = (text or "").lower()
    return "ml bull run score" in lowered or "accumulation score" in lowered


def _platform_evidence_kind(domain: str, meta: dict[str, Any], text: str) -> str:
    return "predictive_ml_signal" if _is_predictive_ml_platform_doc(domain, meta, text) else "platform_signal_snapshot"


def _platform_model_name(meta: dict[str, Any], *, predictive: bool) -> str | None:
    explicit = str(meta.get("model_name") or "").strip() or None
    if explicit:
        return explicit
    if predictive:
        return cfg.VEDA_PLATFORM_ML_MODEL_NAME
    return None


def _platform_model_version(meta: dict[str, Any], *, predictive: bool) -> str | None:
    explicit = str(meta.get("model_version") or "").strip() or None
    if explicit:
        return explicit
    if predictive:
        return cfg.VEDA_PLATFORM_ML_MODEL_VERSION
    return None


def _platform_score_meaning(meta: dict[str, Any], *, predictive: bool) -> str | None:
    explicit = _compact_text(meta.get("score_meaning") or "", cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
    if explicit:
        return explicit
    if predictive:
        return (
            "Higher bull-run, accumulation, and related local model scores indicate a stronger "
            "bullish continuation signal inside Veda's platform scoring pipeline."
        )
    return None


def _platform_reliability_note(meta: dict[str, Any], *, evidence_kind: str) -> str:
    explicit = _compact_text(meta.get("reliability_note") or "", cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
    if explicit:
        return explicit
    if evidence_kind == "predictive_ml_signal":
        return (
            "Treat this as predictive scored evidence, not guaranteed fact. Confirm it with current "
            "flows, price action, and other fresh intelligence before acting on it."
        )
    return (
        "This is a local platform snapshot built from structured data pipelines for the stated date. "
        "Use it as descriptive intelligence, not as a forward prediction by itself."
    )


def normalize_knowledge_record(doc: dict[str, Any]) -> KnowledgeEvidenceRecord:
    domain = str(doc.get("domain") or "").upper()
    meta = _coerce_meta(doc)
    memory_type = str(meta.get("memory_type") or "").lower()
    if memory_type == "attachment_chunk" or domain == "USER_ATTACHMENT_KNOWLEDGE":
        return from_attachment_chunk(doc)
    if domain == "MIT_REPO_CAPABILITY":
        return from_repo_capability(doc)
    if memory_type == "reviewed_note" or domain == "USER_KNOWLEDGE":
        return from_reviewed_memory(doc)
    return from_platform_doc(doc)


def from_platform_doc(doc: dict[str, Any]) -> KnowledgeEvidenceRecord:
    meta = _coerce_meta(doc)
    domain = str(doc.get("domain") or "UNKNOWN").upper()
    entity = str(doc.get("entity") or "Unknown")
    text = str(doc.get("text") or "").strip()
    summary = _compact_text(meta.get("summary") or text, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
    effective_date = str(meta.get("date") or meta.get("effective_date") or meta.get("feature_date") or "").strip() or None
    evidence_kind = _platform_evidence_kind(domain, meta, text)
    predictive = evidence_kind == "predictive_ml_signal"
    model_name = _platform_model_name(meta, predictive=predictive)
    model_version = _platform_model_version(meta, predictive=predictive)
    score_meaning = _platform_score_meaning(meta, predictive=predictive)
    reliability_note = _platform_reliability_note(meta, evidence_kind=evidence_kind)

    entity_keys = KnowledgeEntityKeys(
        symbol=str(meta.get("symbol") or entity).strip() if domain in {"STOCK", "DEAL", "CORPORATE"} else None,
        sector=str(meta.get("sector") or entity).strip() if domain == "SECTOR" else None,
        topic=entity if domain == "ASTRO" else None,
        regime=str(meta.get("regime") or "").strip() or None if domain == "MARKET" else None,
    )
    tags = _unique_tags(meta.get("tags"), domain, meta.get("label"), meta.get("rotation_signal"), meta.get("sector"), meta.get("symbol"))
    freshness_class = "dated_snapshot" if effective_date else "reference"
    provenance = KnowledgeProvenance(
        source_kind="platform_ml_signal" if predictive else "platform_rag_document",
        source_label=f"{'platform_ml' if predictive else 'platform'}:{domain.lower()}",
        storage_key=str(doc.get("doc_id") or ""),
        source_title=entity,
        source_date=effective_date,
        details={
            "source_domain": domain,
            "evidence_kind": evidence_kind,
            "feature_date": effective_date,
            "model_name": model_name,
            "model_version": model_version,
            "score_meaning": score_meaning,
            "reliability_note": reliability_note,
            **meta,
        },
    )
    return KnowledgeEvidenceRecord(
        doc_id=str(doc.get("doc_id") or ""),
        source_type="platform_intelligence",
        domain=domain if domain in _PLATFORM_DOMAINS else "PLATFORM_INTELLIGENCE",
        entity=entity,
        entity_keys=entity_keys,
        text=text,
        summary=summary,
        tags=tags,
        approval_state="system_generated",
        evidence_kind=evidence_kind,
        provenance=provenance,
        freshness=KnowledgeFreshness(
            classification=freshness_class,
            effective_date=effective_date,
            note=(
                "Platform predictive signals are regenerated from local models and data pipelines."
                if predictive
                else "Platform intelligence documents are regenerated from local data pipelines."
            ),
        ),
        model_name=model_name,
        model_version=model_version,
        score_meaning=score_meaning,
        reliability_note=reliability_note,
    )


def from_reviewed_memory(doc: dict[str, Any]) -> KnowledgeEvidenceRecord:
    meta = _coerce_meta(doc)
    entity = str(doc.get("entity") or "Reviewed knowledge")
    text = str(doc.get("text") or "").strip()
    summary = _compact_text(meta.get("summary") or text or entity, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
    intent = str(meta.get("intent") or "").strip().upper() or None
    saved_at = str(meta.get("saved_at") or "").strip() or None
    research_sources = []
    for source in meta.get("research_sources", []) or []:
        if not isinstance(source, dict):
            continue
        title = _compact_text(source.get("title") or "Research source", 180)
        url = str(source.get("url") or "").strip() or None
        published_at = str(source.get("published_at") or "").strip() or None
        excerpt = _compact_text(source.get("excerpt") or "", cfg.VEDA_ATTACHMENT_EXCERPT_CHARS) or None
        research_sources.append({
            "title": title,
            "url": url,
            "published_at": published_at,
            "excerpt": excerpt,
        })
    latest_research_date = str(meta.get("latest_research_date") or "").strip() or None
    domain = intent or "USER_KNOWLEDGE"
    provenance = KnowledgeProvenance(
        source_kind="approved_reviewed_memory",
        source_label="reviewed_memory",
        storage_key=str(doc.get("doc_id") or ""),
        source_title=entity,
        source_url=research_sources[0]["url"] if len(research_sources) == 1 else None,
        source_date=latest_research_date,
        parent_doc_id=str(meta.get("parent_doc_id") or "").strip() or None,
        details={
            "source_domain": str(doc.get("domain") or "USER_KNOWLEDGE"),
            "memory_type": str(meta.get("memory_type") or "reviewed_note"),
            "source_count": meta.get("source_count"),
            "research_used": bool(meta.get("research_used") or research_sources),
            "research_source_count": int(meta.get("research_source_count") or len(research_sources)),
            "research_sources": research_sources,
            "latest_research_date": latest_research_date,
            "research_conflict_note": str(meta.get("research_conflict_note") or "").strip() or None,
            "research_governance_note": str(meta.get("research_governance_note") or "").strip() or None,
        },
    )
    return KnowledgeEvidenceRecord(
        doc_id=str(doc.get("doc_id") or ""),
        source_type="user_reviewed",
        domain=domain,
        entity=entity,
        entity_keys=KnowledgeEntityKeys(
            intent=intent,
            topic=entity,
            parent_doc_id=provenance.parent_doc_id,
        ),
        text=text,
        summary=summary,
        tags=_unique_tags(meta.get("tags"), intent, "reviewed_memory"),
        approval_state="user_approved",
        evidence_kind="approved_memory",
        provenance=provenance,
        freshness=KnowledgeFreshness(
            classification="durable_memory",
            saved_at=saved_at,
            note="Reviewed memory was explicitly approved by the user before saving.",
        ),
        reliability_note=(
            "Approved memory can add durable context, but it is not model output and may be older than "
            "the latest market state."
        ),
    )


def from_attachment_chunk(doc: dict[str, Any]) -> KnowledgeEvidenceRecord:
    meta = _coerce_meta(doc)
    entity = str(doc.get("entity") or "Attachment memory")
    text = str(doc.get("text") or "").strip()
    summary = _compact_text(meta.get("summary") or entity, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
    intent = str(meta.get("intent") or "").strip().upper() or None
    saved_at = str(meta.get("saved_at") or "").strip() or None
    parent_doc_id = str(meta.get("parent_doc_id") or "").strip() or None
    attachment_name = str(meta.get("attachment_name") or "").strip() or None
    provenance = KnowledgeProvenance(
        source_kind="approved_attachment_memory",
        source_label="attachment_memory",
        storage_key=str(doc.get("doc_id") or ""),
        source_title=entity,
        attachment_name=attachment_name,
        attachment_storage_key=str(meta.get("attachment_storage_key") or "").strip() or None,
        attachment_hash=str(meta.get("attachment_hash") or "").strip() or None,
        parent_doc_id=parent_doc_id,
        details={
            "source_domain": str(doc.get("domain") or "USER_ATTACHMENT_KNOWLEDGE"),
            "attachment_kind": meta.get("attachment_kind"),
            "chunk_index": meta.get("chunk_index"),
            "chunk_count": meta.get("chunk_count"),
        },
    )
    return KnowledgeEvidenceRecord(
        doc_id=str(doc.get("doc_id") or ""),
        source_type="attachment_chunk",
        domain=intent or "USER_ATTACHMENT_KNOWLEDGE",
        entity=entity,
        entity_keys=KnowledgeEntityKeys(
            intent=intent,
            topic=entity,
            attachment_name=attachment_name,
            parent_doc_id=parent_doc_id,
        ),
        text=text,
        summary=summary,
        tags=_unique_tags(meta.get("tags"), intent, attachment_name, "attachment_memory"),
        approval_state="user_approved",
        evidence_kind="attachment_memory",
        provenance=provenance,
        freshness=KnowledgeFreshness(
            classification="durable_memory",
            saved_at=saved_at,
            note="Attachment chunks become durable memory only after the parent review is approved.",
        ),
        reliability_note=(
            "Attachment memory comes from user-approved file extraction and may reflect OCR or parsing limits."
        ),
    )


def from_repo_capability(doc: dict[str, Any]) -> KnowledgeEvidenceRecord:
    meta = _coerce_meta(doc)
    entity = str(doc.get("entity") or "MIT repo capability")
    text = str(doc.get("text") or "").strip()
    summary = _compact_text(meta.get("summary") or text or entity, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
    saved_at = str(meta.get("saved_at") or "").strip() or None
    repo_label = str(meta.get("repo_label") or "").strip() or None
    license_name = str(meta.get("license_name") or "").strip() or None
    provenance = KnowledgeProvenance(
        source_kind="approved_mit_repo_capability",
        source_label="mit_repo_capability",
        storage_key=str(doc.get("doc_id") or ""),
        source_title=entity,
        repo_label=repo_label,
        license_name=license_name,
        details={
            "source_domain": str(doc.get("domain") or "MIT_REPO_CAPABILITY"),
            "candidate_file_count": meta.get("candidate_file_count"),
        },
    )
    return KnowledgeEvidenceRecord(
        doc_id=str(doc.get("doc_id") or ""),
        source_type="mit_repo_capability",
        domain="MIT_REPO_CAPABILITY",
        entity=entity,
        entity_keys=KnowledgeEntityKeys(
            topic=entity,
            repo_label=repo_label,
        ),
        text=text,
        summary=summary,
        tags=_unique_tags(meta.get("tags"), repo_label, "mit_repo_capability"),
        approval_state="user_approved",
        evidence_kind="mit_repo_capability",
        provenance=provenance,
        freshness=KnowledgeFreshness(
            classification="reference",
            saved_at=saved_at,
            note="MIT repo capability notes are approved reusable ideas, not executable repo instructions.",
        ),
        license_name=license_name,
        reliability_note="MIT capability notes are reusable ideas, not live market facts or model output.",
    )
