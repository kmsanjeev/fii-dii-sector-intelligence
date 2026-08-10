from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD_RE = re.compile(r"[A-Za-z0-9_]{3,}")
_STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "will",
    "your", "have", "about", "when", "what", "where", "which", "using",
    "used", "only", "been", "were", "their", "there", "they", "them",
    "after", "before", "could", "should", "would", "also", "very", "more",
}
_NOVELTY_NOISE_TERMS = {
    "again", "answer", "because", "current", "details", "different", "draft",
    "latest", "memory", "older", "purpose", "related", "review", "saved",
    "separate", "similar", "still", "today", "topic", "topics", "updated",
    "useful", "value",
}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _clean_text(value: str, limit: int) -> str:
    compact = " ".join((value or "").strip().split())
    return compact[:limit].strip()


def _slug(value: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9]+", "_", (value or "").strip().lower()).strip("_")
    return raw[:60] or "knowledge"


def _terms(value: str) -> list[str]:
    terms: list[str] = []
    for match in _WORD_RE.findall((value or "").lower()):
        if match in _STOP_WORDS:
            continue
        if match not in terms:
            terms.append(match)
    return terms


def _sequence_score(left: str, right: str) -> int:
    left_clean = _clean_text(left, 4000).lower()
    right_clean = _clean_text(right, 4000).lower()
    if not left_clean or not right_clean:
        return 0
    return int(round(SequenceMatcher(None, left_clean, right_clean).ratio() * 100))


def _attachment_fingerprint(*, kind: str, mime_type: str, text: str) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "kind": kind,
                "mime_type": mime_type,
                "text": text,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]


@dataclass(slots=True)
class KnowledgeTraceSource:
    kind: str
    title: str
    url: str | None = None
    published_at: str | None = None
    excerpt: str | None = None
    storage_key: str | None = None
    warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class KnowledgeExistingMatch:
    doc_id: str
    title: str
    summary: str
    saved_at: str | None = None
    memory_type: str = "reviewed_note"
    overlap_score: int = 0
    semantic_score: int = 0
    reason: str | None = None
    exact_duplicate: bool = False
    new_value_hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class KnowledgeReviewDraft:
    draft_id: str
    title: str
    summary: str
    facts: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    raw_question: str = ""
    raw_answer: str = ""
    intent: str | None = None
    session_id: str | None = None
    created_at: str = field(default_factory=_utc_now)
    sources: list[KnowledgeTraceSource] = field(default_factory=list)
    research: dict[str, Any] = field(default_factory=dict)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    existing_matches: list[KnowledgeExistingMatch] = field(default_factory=list)
    suggested_action: str = "save"
    suggestion_reason: str | None = None
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sources"] = [source.to_dict() for source in self.sources]
        payload["existing_matches"] = [match.to_dict() for match in self.existing_matches]
        return payload


class KnowledgeReviewService:
    def __init__(
        self,
        *,
        draft_dir: Path | None = None,
        approved_dir: Path | None = None,
        approved_docs_path: Path | None = None,
        attachment_service: Any | None = None,
        unified_sync_callback: Callable[..., dict[str, Any]] | None = None,
    ):
        self._draft_dir = Path(draft_dir or cfg.VEDA_KNOWLEDGE_DRAFT_DIR)
        self._approved_dir = Path(approved_dir or cfg.VEDA_KNOWLEDGE_APPROVED_DIR)
        self._approved_docs_path = Path(approved_docs_path or cfg.VEDA_APPROVED_KNOWLEDGE_DOCS)
        self._attachment_service = attachment_service
        self._unified_sync_callback = unified_sync_callback
        self._draft_dir.mkdir(parents=True, exist_ok=True)
        self._approved_dir.mkdir(parents=True, exist_ok=True)
        self._approved_docs_path.parent.mkdir(parents=True, exist_ok=True)

    def create_draft(
        self,
        *,
        question: str,
        answer: str,
        intent: str | None = None,
        session_id: str | None = None,
        research: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> KnowledgeReviewDraft:
        question_clean = _clean_text(question, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
        answer_clean = _clean_text(answer, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS * 2)
        if not question_clean:
            raise ValueError("Question is required to create a review draft.")
        if not answer_clean:
            raise ValueError("Answer is required to create a review draft.")

        research_payload = research or {}
        attachment_payload = attachments or []
        existing_matches, suggested_action, suggestion_reason = self._analyze_existing_memory(
            question=question_clean,
            answer=answer_clean,
            intent=(intent or "").strip() or None,
            attachments=attachment_payload,
        )
        draft = KnowledgeReviewDraft(
            draft_id=uuid.uuid4().hex,
            title=self._derive_title(question_clean, answer_clean, intent),
            summary=self._derive_summary(answer_clean),
            facts=self._derive_facts(answer_clean),
            tags=self._derive_tags(question_clean, answer_clean, intent, research_payload, attachment_payload),
            raw_question=question_clean,
            raw_answer=answer_clean,
            intent=(intent or "").strip() or None,
            session_id=(session_id or "").strip() or None,
            sources=self._derive_sources(research_payload, attachment_payload),
            research=research_payload,
            attachments=attachment_payload,
            existing_matches=existing_matches,
            suggested_action=suggested_action,
            suggestion_reason=suggestion_reason,
        )
        self._write_json(self._draft_path(draft.draft_id), draft.to_dict())
        return draft

    def approve(
        self,
        draft_id: str,
        *,
        title: str,
        summary: str,
        facts: list[str],
        tags: list[str],
        review_note: str | None = None,
        decision: str | None = None,
    ) -> dict[str, Any]:
        draft = self.load_draft(draft_id)
        approved_title = _clean_text(title or draft.title, cfg.VEDA_KNOWLEDGE_MAX_TITLE_CHARS)
        approved_summary = _clean_text(summary or draft.summary, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
        approved_facts = self._normalize_facts(facts or draft.facts)
        approved_tags = self._normalize_tags(tags or draft.tags)
        note = _clean_text(review_note or "", cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
        saved_at = _utc_now()
        requested_decision = (decision or "save").strip().lower() or "save"
        if requested_decision not in {"save", "merge"}:
            raise ValueError("Knowledge approval decision must be either 'save' or 'merge'.")

        if requested_decision == "merge":
            merged = self._approve_by_merge(
                draft=draft,
                approved_title=approved_title,
                approved_summary=approved_summary,
                approved_facts=approved_facts,
                approved_tags=approved_tags,
                review_note=note,
                saved_at=saved_at,
            )
            if merged is not None:
                return merged

        fingerprint_payload = {
            "title": approved_title,
            "summary": approved_summary,
            "facts": approved_facts,
            "tags": approved_tags,
            "question": draft.raw_question,
            "sources": [source.to_dict() for source in draft.sources],
        }
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        doc_id = f"veda_review_{fingerprint}"
        approved_path = self._approved_dir / f"{doc_id}.json"
        duplicate = approved_path.exists()

        if duplicate:
            record = json.loads(approved_path.read_text(encoding="utf-8"))
            saved_at = str(record.get("saved_at") or saved_at)
            approved_title = str(record.get("title") or approved_title)
        else:
            attachment_docs = self._build_attachment_docs(
                draft=draft,
                approved_title=approved_title,
                approved_tags=approved_tags,
                saved_at=saved_at,
                parent_doc_id=doc_id,
            )
            record = {
                "draft_id": draft.draft_id,
                "doc_id": doc_id,
                "status": "approved",
                "saved_at": saved_at,
                "title": approved_title,
                "summary": approved_summary,
                "facts": approved_facts,
                "tags": approved_tags,
                "review_note": note or None,
                "raw_question": draft.raw_question,
                "raw_answer": draft.raw_answer,
                "intent": draft.intent,
                "session_id": draft.session_id,
                "created_at": draft.created_at,
                "sources": [source.to_dict() for source in draft.sources],
                "research": draft.research,
                "attachments": draft.attachments,
                "attachment_doc_count": len({doc["meta"].get("attachment_storage_key") for doc in attachment_docs}),
                "attachment_chunk_count": len(attachment_docs),
            }
            self._write_json(approved_path, record)
            self._upsert_approved_docs([self._approved_record_to_doc(record), *attachment_docs])
            self._refresh_unified_retrieval_assets(reason="knowledge_approved", source_doc_id=doc_id)

        return {
            "draft_id": draft.draft_id,
            "doc_id": doc_id,
            "saved_at": saved_at,
            "title": approved_title,
            "status": "approved",
            "duplicate": duplicate,
            "attachment_doc_count": int(record.get("attachment_doc_count") or 0),
            "attachment_chunk_count": int(record.get("attachment_chunk_count") or 0),
            "decision": "save",
            "merged_into_doc_id": None,
        }

    def load_draft(self, draft_id: str) -> KnowledgeReviewDraft:
        path = self._draft_path(draft_id)
        if not path.exists():
            raise FileNotFoundError(draft_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources = [KnowledgeTraceSource(**source) for source in payload.get("sources", [])]
        matches = [KnowledgeExistingMatch(**match) for match in payload.get("existing_matches", [])]
        payload["sources"] = sources
        payload["existing_matches"] = matches
        return KnowledgeReviewDraft(**payload)

    def discard(self, draft_id: str) -> dict[str, Any]:
        path = self._draft_path(draft_id)
        if not path.exists():
            raise FileNotFoundError(draft_id)
        path.unlink()
        return {
            "draft_id": draft_id,
            "status": "discarded",
        }

    def search(self, query: str, *, top_k: int = 3) -> list[dict[str, Any]]:
        docs = self._load_approved_docs()
        if not docs:
            return []
        terms = _terms(query)
        if not terms:
            return []

        ranked: list[dict[str, Any]] = []
        for doc in docs:
            meta = doc.get("meta", {}) or {}
            haystack = " ".join([
                str(doc.get("entity", "")),
                str(doc.get("text", "")),
                " ".join(str(tag) for tag in meta.get("tags", []) or []),
                str(meta.get("summary", "")),
            ]).lower()
            score = 0
            for term in terms:
                if term in haystack:
                    score += haystack.count(term)
            if score <= 0:
                continue
            ranked.append({
                **doc,
                "review_score": score,
            })

        ranked.sort(
            key=lambda item: (item.get("review_score", 0), item.get("meta", {}).get("saved_at", "")),
            reverse=True,
        )
        return ranked[:top_k]

    def build_context(self, query: str, *, top_k: int = 2) -> str:
        results = self.search(query, top_k=top_k)
        if not results:
            return ""
        lines = [
            "Reviewed knowledge below was explicitly approved by the user before saving.",
            "Treat it as platform memory and still stay honest about freshness or gaps.",
        ]
        for index, doc in enumerate(results, start=1):
            meta = doc.get("meta", {}) or {}
            memory_type = str(meta.get("memory_type") or "reviewed_note")
            source_label = "attachment memory" if memory_type == "attachment_chunk" else "reviewed note"
            lines.append(
                f"- [{index}] {doc.get('entity', 'Reviewed note')} | saved={meta.get('saved_at', 'unknown')} | {source_label}\n"
                f"  {str(doc.get('text', '')).strip()[:420]}"
            )
        return "\n".join(lines)

    def _derive_title(self, question: str, answer: str, intent: str | None) -> str:
        first_answer_line = answer.splitlines()[0].strip() if answer else ""
        first_sentence = _SENTENCE_SPLIT_RE.split(first_answer_line)[0].strip() if first_answer_line else ""
        title = first_sentence or question
        if intent and intent.strip():
            title = f"{intent.strip().title()}: {title}"
        return _clean_text(title, cfg.VEDA_KNOWLEDGE_MAX_TITLE_CHARS)

    def _derive_summary(self, answer: str) -> str:
        return _clean_text(answer, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)

    def _derive_facts(self, answer: str) -> list[str]:
        raw_parts = _SENTENCE_SPLIT_RE.split(answer or "")
        facts: list[str] = []
        for part in raw_parts:
            cleaned = _clean_text(part, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
            if len(cleaned) < 20:
                continue
            if cleaned in facts:
                continue
            facts.append(cleaned)
            if len(facts) >= cfg.VEDA_KNOWLEDGE_MAX_FACTS:
                break
        return facts or [self._derive_summary(answer)]

    def _derive_tags(
        self,
        question: str,
        answer: str,
        intent: str | None,
        research: dict[str, Any],
        attachments: list[dict[str, Any]],
    ) -> list[str]:
        tags: list[str] = []
        if intent and intent.strip():
            tags.append(intent.strip().lower())
        if research.get("used"):
            tags.append("research")
        if attachments:
            tags.append("attachment")
            for attachment in attachments:
                kind = str(attachment.get("kind") or "").strip().lower()
                if kind and kind not in tags:
                    tags.append(kind)
        for term in _terms(f"{question} {answer}"):
            if len(tags) >= cfg.VEDA_KNOWLEDGE_MAX_TAGS:
                break
            if term not in tags:
                tags.append(term)
        return tags[: cfg.VEDA_KNOWLEDGE_MAX_TAGS]

    def _derive_sources(
        self,
        research: dict[str, Any],
        attachments: list[dict[str, Any]],
    ) -> list[KnowledgeTraceSource]:
        sources: list[KnowledgeTraceSource] = []
        for source in research.get("sources", []) or []:
            title = _clean_text(str(source.get("title") or source.get("source") or "Research source"), 180)
            sources.append(KnowledgeTraceSource(
                kind="research",
                title=title,
                url=str(source.get("url") or "").strip() or None,
                published_at=str(source.get("published_at") or "").strip() or None,
                excerpt=_clean_text(str(source.get("snippet") or ""), cfg.VEDA_ATTACHMENT_EXCERPT_CHARS) or None,
            ))
        for attachment in attachments:
            title = _clean_text(str(attachment.get("name") or "Attachment"), 180)
            sources.append(KnowledgeTraceSource(
                kind="attachment",
                title=title,
                excerpt=_clean_text(str(attachment.get("excerpt") or ""), cfg.VEDA_ATTACHMENT_EXCERPT_CHARS) or None,
                storage_key=str(attachment.get("storage_key") or "").strip() or None,
                warning=str(attachment.get("warning") or "").strip() or None,
            ))
        return sources

    def _normalize_facts(self, facts: list[str]) -> list[str]:
        cleaned: list[str] = []
        for fact in facts:
            value = _clean_text(fact, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
            if len(value) < 8 or value in cleaned:
                continue
            cleaned.append(value)
            if len(cleaned) >= cfg.VEDA_KNOWLEDGE_MAX_FACTS:
                break
        if not cleaned:
            raise ValueError("At least one reviewed fact is required.")
        return cleaned

    def _normalize_tags(self, tags: list[str]) -> list[str]:
        cleaned: list[str] = []
        for tag in tags:
            value = _slug(tag)
            if not value or value in cleaned:
                continue
            cleaned.append(value)
            if len(cleaned) >= cfg.VEDA_KNOWLEDGE_MAX_TAGS:
                break
        return cleaned

    def _approved_record_to_doc(self, record: dict[str, Any]) -> dict[str, Any]:
        title = str(record.get("title") or "Reviewed knowledge")
        summary = str(record.get("summary") or "")
        facts = [str(fact) for fact in record.get("facts", []) if str(fact).strip()]
        text_parts = [summary] + facts
        text = " ".join(part.strip() for part in text_parts if part.strip()).strip()
        if not text:
            text = summary or title
        research_sources = self._research_sources_for_meta(record.get("sources", []))
        research_payload = record.get("research", {}) if isinstance(record.get("research"), dict) else {}
        return {
            "doc_id": record["doc_id"],
            "domain": "USER_KNOWLEDGE",
            "entity": title,
            "text": text,
            "meta": {
                "tags": record.get("tags", []),
                "saved_at": record.get("saved_at"),
                "updated_at": record.get("updated_at"),
                "intent": record.get("intent"),
                "source_count": len(record.get("sources", [])),
                "summary": summary,
                "memory_type": "reviewed_note",
                "merge_count": int(record.get("merge_count") or 0),
                "research_used": bool(research_sources),
                "research_source_count": len(research_sources),
                "research_sources": research_sources,
                "latest_research_date": self._latest_research_date(research_sources),
                "research_conflict_note": str(research_payload.get("conflict_note") or "").strip() or None,
                "research_governance_note": str(research_payload.get("governance_note") or "").strip() or None,
            },
        }

    def _analyze_existing_memory(
        self,
        *,
        question: str,
        answer: str,
        intent: str | None,
        attachments: list[dict[str, Any]],
    ) -> tuple[list[KnowledgeExistingMatch], str, str | None]:
        docs = self._load_approved_docs()
        if not docs:
            return [], "save", None

        attachment_candidates = self._load_attachment_candidates(attachments)
        query_parts = [question, answer]
        query_parts.extend(str(attachment.get("excerpt") or "") for attachment in attachments)
        query_parts.extend(str(candidate.get("text") or "") for candidate in attachment_candidates)
        query_text = " ".join(part for part in query_parts if part)
        query_terms = _terms(" ".join(query_parts))
        content_terms = _terms(" ".join([
            answer,
            *[str(candidate.get("text") or "") for candidate in attachment_candidates],
        ]))
        if not content_terms:
            content_terms = query_terms

        if not query_terms and not attachment_candidates:
            return [], "save", None

        exact_duplicate_hashes = {candidate["attachment_hash"] for candidate in attachment_candidates}
        grouped: dict[str, dict[str, Any]] = {}
        for doc in docs:
            meta = doc.get("meta", {}) or {}
            doc_id = str(doc.get("doc_id") or "").strip()
            if not doc_id:
                continue
            root_id = str(meta.get("parent_doc_id") or doc_id).strip() or doc_id
            haystack = " ".join([
                str(doc.get("entity", "")),
                str(doc.get("text", "")),
                " ".join(str(tag) for tag in meta.get("tags", []) or []),
                str(meta.get("summary", "")),
            ]).lower()
            score = 0
            for term in query_terms:
                if term in haystack:
                    score += haystack.count(term)

            attachment_hash = str(meta.get("attachment_hash") or "").strip()
            exact_duplicate = bool(attachment_hash and attachment_hash in exact_duplicate_hashes)
            if score <= 0 and not exact_duplicate:
                continue

            group = grouped.setdefault(root_id, {
                "doc_id": root_id,
                "title": str(doc.get("entity") or "Saved memory"),
                "summary": str(meta.get("summary") or ""),
                "saved_at": str(meta.get("saved_at") or "") or None,
                "memory_type": str(meta.get("memory_type") or "reviewed_note"),
                "overlap_score": 0,
                "exact_duplicate": False,
                "has_reviewed_note": False,
                "has_attachment_memory": False,
                "text_parts": [],
                "terms": set(),
            })
            group["overlap_score"] += score
            group["exact_duplicate"] = group["exact_duplicate"] or exact_duplicate
            group["text_parts"].append(haystack)
            group["terms"].update(_terms(haystack))
            memory_type = str(meta.get("memory_type") or "reviewed_note")
            if memory_type == "reviewed_note":
                group["has_reviewed_note"] = True
                group["memory_type"] = "reviewed_note"
                group["title"] = str(doc.get("entity") or group["title"])
                group["summary"] = str(meta.get("summary") or group["summary"])
                group["saved_at"] = str(meta.get("saved_at") or group["saved_at"]) or group["saved_at"]
            elif not group["has_reviewed_note"]:
                group["has_attachment_memory"] = True
                group["memory_type"] = "attachment_chunk"
                if not group["summary"]:
                    group["summary"] = str(meta.get("summary") or "")

        matches: list[KnowledgeExistingMatch] = []
        for item in grouped.values():
            overlap_score = int(item["overlap_score"])
            group_text = " ".join(str(part) for part in item.get("text_parts", []) if str(part).strip())
            group_terms = set(item.get("terms", set()))
            semantic_score = _sequence_score(query_text, group_text)
            same_topic = overlap_score >= 6 or semantic_score >= 55
            novel_terms = [
                term
                for term in content_terms
                if len(term) >= 6 and term not in group_terms and term not in _NOVELTY_NOISE_TERMS
            ]
            new_value_hint = None
            if same_topic and novel_terms:
                preview = ", ".join(novel_terms[:4])
                if preview:
                    new_value_hint = f"Possible new value: {preview}."
            if item["exact_duplicate"]:
                reason = "This readable file already exists in saved memory."
            elif same_topic and new_value_hint:
                reason = "This saved memory covers the same topic, but the new draft appears to add something useful."
            elif same_topic:
                reason = "This saved memory already covers almost the same topic."
            else:
                reason = "This saved memory is related, but not close enough to treat as the same note."
            matches.append(KnowledgeExistingMatch(
                doc_id=str(item["doc_id"]),
                title=_clean_text(str(item["title"] or "Saved memory"), 140),
                summary=_clean_text(str(item["summary"] or ""), cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS),
                saved_at=item["saved_at"],
                memory_type=str(item["memory_type"]),
                overlap_score=overlap_score,
                semantic_score=semantic_score,
                exact_duplicate=bool(item["exact_duplicate"]),
                reason=reason,
                new_value_hint=new_value_hint,
            ))
        matches.sort(
            key=lambda item: (
                item.exact_duplicate,
                item.semantic_score,
                item.overlap_score,
                item.saved_at or "",
            ),
            reverse=True,
        )
        matches = matches[:3]

        if not matches:
            return [], "save", None

        top_match = matches[0]
        if top_match.exact_duplicate:
            return (
                matches,
                "discard",
                "Veda already has the same readable file memory saved from an earlier approval. Discard is recommended unless you intentionally want another copy.",
            )
        if (
            top_match.overlap_score >= 12
            and not attachment_candidates
            and not top_match.new_value_hint
        ):
            return (
                matches,
                "discard",
                "Veda found an older saved memory that already covers nearly the same topic. Discard is recommended unless you want to keep a separate note on purpose.",
            )
        if (
            (top_match.overlap_score >= 6 or top_match.semantic_score >= 55)
            and top_match.new_value_hint
        ):
            return (
                matches,
                "merge",
                "Veda found saved memory on the same topic, but this draft appears to add new value. Merge is recommended so the older memory stays updated without creating a duplicate note.",
            )
        return (
            matches,
            "save",
            "Some saved memory is related, but this draft still looks different enough to save separately after your review.",
        )

    def _approve_by_merge(
        self,
        *,
        draft: KnowledgeReviewDraft,
        approved_title: str,
        approved_summary: str,
        approved_facts: list[str],
        approved_tags: list[str],
        review_note: str,
        saved_at: str,
    ) -> dict[str, Any] | None:
        target_doc_id = next((match.doc_id for match in draft.existing_matches if match.doc_id), "")
        if not target_doc_id:
            return None

        approved_path = self._approved_dir / f"{target_doc_id}.json"
        if not approved_path.exists():
            return None

        existing_record = json.loads(approved_path.read_text(encoding="utf-8"))
        merged_title = self._merge_title(
            str(existing_record.get("title") or ""),
            approved_title,
        )
        merged_summary = self._merge_summary(
            str(existing_record.get("summary") or ""),
            approved_summary,
        )
        merged_facts = self._merge_facts(
            existing_record.get("facts", []),
            approved_facts,
        )
        merged_tags = self._merge_tags(
            existing_record.get("tags", []),
            approved_tags,
        )
        merged_sources = self._merge_source_like_rows(
            existing_record.get("sources", []),
            [source.to_dict() for source in draft.sources],
        )
        merged_attachments = self._merge_source_like_rows(
            existing_record.get("attachments", []),
            draft.attachments,
        )
        merged_review_note = self._merge_summary(
            str(existing_record.get("review_note") or ""),
            review_note,
        ) or None
        attachment_docs = self._build_attachment_docs(
            draft=draft,
            approved_title=merged_title,
            approved_tags=merged_tags,
            saved_at=saved_at,
            parent_doc_id=target_doc_id,
        )
        attachment_doc_count, attachment_chunk_count = self._attachment_doc_stats(
            target_doc_id,
            pending_docs=attachment_docs,
        )
        merged_draft_ids = [
            draft_id_value
            for draft_id_value in [*existing_record.get("merged_draft_ids", []), draft.draft_id]
            if str(draft_id_value).strip()
        ]
        merged_draft_ids = list(dict.fromkeys(merged_draft_ids))[-10:]

        merged_record = {
            **existing_record,
            "doc_id": target_doc_id,
            "draft_id": draft.draft_id,
            "root_draft_id": str(existing_record.get("root_draft_id") or existing_record.get("draft_id") or draft.draft_id),
            "last_draft_id": draft.draft_id,
            "status": "approved",
            "saved_at": saved_at,
            "updated_at": saved_at,
            "title": merged_title,
            "summary": merged_summary,
            "facts": merged_facts,
            "tags": merged_tags,
            "review_note": merged_review_note,
            "raw_question": draft.raw_question,
            "raw_answer": draft.raw_answer,
            "intent": draft.intent or existing_record.get("intent"),
            "session_id": draft.session_id or existing_record.get("session_id"),
            "created_at": existing_record.get("created_at") or draft.created_at,
            "sources": merged_sources,
            "research": draft.research or existing_record.get("research", {}),
            "attachments": merged_attachments,
            "attachment_doc_count": attachment_doc_count,
            "attachment_chunk_count": attachment_chunk_count,
            "merge_count": int(existing_record.get("merge_count") or 0) + 1,
            "merged_draft_ids": merged_draft_ids,
        }
        self._write_json(approved_path, merged_record)
        self._upsert_approved_docs([self._approved_record_to_doc(merged_record), *attachment_docs])
        self._refresh_unified_retrieval_assets(reason="knowledge_merged", source_doc_id=target_doc_id)
        return {
            "draft_id": draft.draft_id,
            "doc_id": target_doc_id,
            "saved_at": saved_at,
            "title": merged_title,
            "status": "approved",
            "duplicate": False,
            "attachment_doc_count": attachment_doc_count,
            "attachment_chunk_count": attachment_chunk_count,
            "decision": "merge",
            "merged_into_doc_id": target_doc_id,
        }

    def _build_attachment_docs(
        self,
        *,
        draft: KnowledgeReviewDraft,
        approved_title: str,
        approved_tags: list[str],
        saved_at: str,
        parent_doc_id: str,
    ) -> list[dict[str, Any]]:
        attachment_service = self._get_attachment_service()
        if attachment_service is None:
            return []

        docs: list[dict[str, Any]] = []
        for attachment in draft.attachments:
            storage_key = str(attachment.get("storage_key") or "").strip()
            if not storage_key:
                continue
            try:
                prepared = attachment_service.load(storage_key)
            except FileNotFoundError:
                logger.debug("[KnowledgeReview] Attachment upload missing for storage key %s", storage_key)
                continue
            except Exception as exc:
                logger.warning("[KnowledgeReview] Could not load attachment %s: %s", storage_key, exc)
                continue

            extracted_text = self._clean_attachment_text(getattr(prepared, "extracted_text", ""))
            if not extracted_text:
                continue

            chunks = self._chunk_attachment_text(extracted_text)
            if not chunks:
                continue

            attachment_name = str(getattr(prepared, "name", "") or attachment.get("name") or "Attachment")
            attachment_kind = str(getattr(prepared, "kind", "") or attachment.get("kind") or "attachment")
            attachment_hash = _attachment_fingerprint(
                kind=attachment_kind,
                mime_type=str(getattr(prepared, "mime_type", "") or attachment.get("mime_type") or ""),
                text=extracted_text,
            )
            total_chunks = len(chunks)
            base_tags = self._attachment_tags(approved_tags, attachment_kind)
            summary = _clean_text(str(getattr(prepared, "excerpt", "") or ""), cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS) or attachment_name

            for chunk_index, chunk in enumerate(chunks, start=1):
                chunk_label = f" chunk {chunk_index}/{total_chunks}" if total_chunks > 1 else ""
                docs.append({
                    "doc_id": f"veda_attachment_{attachment_hash}_{chunk_index:02d}",
                    "domain": "USER_ATTACHMENT_KNOWLEDGE",
                    "entity": _clean_text(f"{approved_title} | file: {attachment_name}{chunk_label}", cfg.VEDA_KNOWLEDGE_MAX_TITLE_CHARS),
                    "text": chunk,
                    "meta": {
                        "tags": base_tags,
                        "saved_at": saved_at,
                        "intent": draft.intent,
                        "source_count": 1,
                        "summary": summary,
                        "memory_type": "attachment_chunk",
                        "parent_doc_id": parent_doc_id,
                        "attachment_name": attachment_name,
                        "attachment_kind": attachment_kind,
                        "attachment_storage_key": storage_key,
                        "attachment_hash": attachment_hash,
                        "chunk_index": chunk_index,
                        "chunk_count": total_chunks,
                    },
                })
        return docs

    def _load_attachment_candidates(self, attachments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        attachment_service = self._get_attachment_service()
        if attachment_service is None:
            return []

        candidates: list[dict[str, Any]] = []
        for attachment in attachments:
            storage_key = str(attachment.get("storage_key") or "").strip()
            if not storage_key:
                continue
            try:
                prepared = attachment_service.load(storage_key)
            except Exception:
                continue
            extracted_text = self._clean_attachment_text(getattr(prepared, "extracted_text", ""))
            if not extracted_text:
                continue
            attachment_name = str(getattr(prepared, "name", "") or attachment.get("name") or "Attachment")
            attachment_kind = str(getattr(prepared, "kind", "") or attachment.get("kind") or "attachment")
            mime_type = str(getattr(prepared, "mime_type", "") or attachment.get("mime_type") or "")
            candidates.append({
                "storage_key": storage_key,
                "attachment_hash": _attachment_fingerprint(
                    kind=attachment_kind,
                    mime_type=mime_type,
                    text=extracted_text,
                ),
                "text": extracted_text,
            })
        return candidates

    def _attachment_tags(self, approved_tags: list[str], attachment_kind: str) -> list[str]:
        tags = list(approved_tags)
        for tag in ["attachment", _slug(attachment_kind)]:
            if tag and tag not in tags:
                tags.append(tag)
        return tags[: cfg.VEDA_KNOWLEDGE_MAX_TAGS]

    def _clean_attachment_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"\n{3,}", "\n\n", text.replace("\r", "\n")).strip()
        return cleaned[: cfg.VEDA_ATTACHMENT_MAX_TEXT_CHARS]

    def _chunk_attachment_text(self, text: str) -> list[str]:
        cleaned = self._clean_attachment_text(text)
        if not cleaned:
            return []

        chunk_size = max(int(cfg.VEDA_KNOWLEDGE_ATTACHMENT_CHUNK_CHARS), 400)
        overlap = max(0, min(int(cfg.VEDA_KNOWLEDGE_ATTACHMENT_CHUNK_OVERLAP_CHARS), chunk_size // 3))
        max_chunks = max(int(cfg.VEDA_KNOWLEDGE_ATTACHMENT_MAX_CHUNKS_PER_FILE), 1)
        min_cut = max(chunk_size // 2, 200)

        chunks: list[str] = []
        start = 0
        text_len = len(cleaned)
        while start < text_len and len(chunks) < max_chunks:
            end = min(start + chunk_size, text_len)
            if end < text_len:
                for separator in ("\n\n", ". ", "? ", "! ", " "):
                    cut = cleaned.rfind(separator, start + min_cut, end)
                    if cut > start:
                        end = cut + len(separator.strip())
                        break
            chunk = cleaned[start:end].strip()
            if chunk and (not chunks or chunk != chunks[-1]):
                chunks.append(chunk)
            if end >= text_len:
                break
            start = max(end - overlap, start + 1)
            while start < text_len and cleaned[start].isspace():
                start += 1
        return chunks

    def _load_approved_docs(self) -> list[dict[str, Any]]:
        if not self._approved_docs_path.exists():
            return []
        docs: list[dict[str, Any]] = []
        for line in self._approved_docs_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("[KnowledgeReview] Skipping invalid approved doc line")
        return docs

    def _upsert_approved_doc(self, doc: dict[str, Any]) -> None:
        self._upsert_approved_docs([doc])

    def _upsert_approved_docs(self, docs_to_write: list[dict[str, Any]]) -> None:
        docs = {existing.get("doc_id"): existing for existing in self._load_approved_docs() if existing.get("doc_id")}
        for doc in docs_to_write:
            docs[doc["doc_id"]] = doc
        ordered = sorted(docs.values(), key=lambda item: item.get("meta", {}).get("saved_at", ""))
        tmp = self._approved_docs_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            for item in ordered:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        tmp.replace(self._approved_docs_path)

    def _refresh_unified_retrieval_assets(self, *, reason: str, source_doc_id: str | None) -> None:
        callback = self._unified_sync_callback
        if callback is None:
            try:
                from engines.ai.knowledge.unified_runtime_sync import refresh_unified_retrieval_assets

                callback = refresh_unified_retrieval_assets
            except Exception as exc:
                logger.debug("[KnowledgeReview] Unified runtime sync unavailable: %s", exc)
                return
        try:
            callback(reason=reason, source_doc_id=source_doc_id)
        except Exception as exc:
            logger.warning(
                "[KnowledgeReview] Unified runtime sync callback failed (reason=%s, source_doc_id=%s): %s",
                reason,
                source_doc_id,
                exc,
            )

    def _merge_title(self, existing_title: str, new_title: str) -> str:
        existing_clean = _clean_text(existing_title, cfg.VEDA_KNOWLEDGE_MAX_TITLE_CHARS)
        new_clean = _clean_text(new_title, cfg.VEDA_KNOWLEDGE_MAX_TITLE_CHARS)
        if not existing_clean:
            return new_clean
        if not new_clean:
            return existing_clean
        return new_clean if len(new_clean) > len(existing_clean) else existing_clean

    def _merge_summary(self, existing_summary: str, new_summary: str) -> str:
        parts: list[str] = []
        for raw_value in [existing_summary, new_summary]:
            for piece in _SENTENCE_SPLIT_RE.split(raw_value or ""):
                cleaned = _clean_text(piece, cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)
                if not cleaned or cleaned in parts:
                    continue
                parts.append(cleaned)
        return _clean_text(" ".join(parts), cfg.VEDA_KNOWLEDGE_MAX_SUMMARY_CHARS)

    def _merge_facts(self, existing_facts: list[Any], new_facts: list[str]) -> list[str]:
        return self._normalize_facts([
            *[str(fact) for fact in existing_facts if str(fact).strip()],
            *new_facts,
        ])

    def _merge_tags(self, existing_tags: list[Any], new_tags: list[str]) -> list[str]:
        return self._normalize_tags([
            *[str(tag) for tag in existing_tags if str(tag).strip()],
            *new_tags,
        ])

    def _research_sources_for_meta(self, rows: list[Any]) -> list[dict[str, Any]]:
        research_sources: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("kind") or "").strip().lower() != "research":
                continue
            title = _clean_text(str(row.get("title") or "Research source"), 180)
            url = str(row.get("url") or "").strip() or None
            published_at = str(row.get("published_at") or "").strip() or None
            excerpt = _clean_text(str(row.get("excerpt") or ""), cfg.VEDA_ATTACHMENT_EXCERPT_CHARS) or None
            research_sources.append({
                "title": title,
                "url": url,
                "published_at": published_at,
                "excerpt": excerpt,
            })
        return research_sources

    def _latest_research_date(self, research_sources: list[dict[str, Any]]) -> str | None:
        dates = [
            str(source.get("published_at") or "").strip()
            for source in research_sources
            if str(source.get("published_at") or "").strip()
        ]
        return max(dates) if dates else None

    def _merge_source_like_rows(
        self,
        existing_rows: list[Any],
        new_rows: list[Any],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[tuple[str, ...]] = set()
        for row in [*existing_rows, *new_rows]:
            if not isinstance(row, dict):
                continue
            normalized = {
                key: value
                for key, value in row.items()
                if value not in (None, "", [], {})
            }
            if not normalized:
                continue
            dedupe_key = tuple(
                str(normalized.get(field_name) or "")
                for field_name in ("kind", "title", "url", "storage_key", "name")
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged.append(normalized)
        return merged

    def _attachment_doc_stats(
        self,
        parent_doc_id: str,
        *,
        pending_docs: list[dict[str, Any]] | None = None,
    ) -> tuple[int, int]:
        docs_by_id: dict[str, dict[str, Any]] = {}
        for doc in self._load_approved_docs():
            meta = doc.get("meta", {}) or {}
            if str(meta.get("parent_doc_id") or "") == parent_doc_id:
                docs_by_id[str(doc.get("doc_id") or "")] = doc
        for doc in pending_docs or []:
            docs_by_id[str(doc.get("doc_id") or "")] = doc
        attachment_keys = {
            str((doc.get("meta", {}) or {}).get("attachment_storage_key") or "").strip()
            for doc in docs_by_id.values()
            if str((doc.get("meta", {}) or {}).get("attachment_storage_key") or "").strip()
        }
        return len(attachment_keys), len(docs_by_id)

    def _get_attachment_service(self):
        if self._attachment_service is not None:
            return self._attachment_service
        try:
            from engines.ai.attachments import get_attachment_service
            self._attachment_service = get_attachment_service()
        except Exception as exc:
            logger.debug("[KnowledgeReview] Attachment service unavailable: %s", exc)
            self._attachment_service = None
        return self._attachment_service

    def _draft_path(self, draft_id: str) -> Path:
        safe = _slug(draft_id) or draft_id
        return self._draft_dir / f"{safe}.json"

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)


_SERVICE: KnowledgeReviewService | None = None


def get_knowledge_review_service() -> KnowledgeReviewService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = KnowledgeReviewService()
    return _SERVICE
