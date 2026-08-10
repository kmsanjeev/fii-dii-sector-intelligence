from __future__ import annotations

import json

from engines.ai.attachments.service import AttachmentService
from engines.ai.knowledge.review_service import KnowledgeReviewService
from engines.common import config as cfg


def _make_service(tmp_dir, *, attachment_service: AttachmentService | None = None):
    return KnowledgeReviewService(
        draft_dir=tmp_dir / "drafts",
        approved_dir=tmp_dir / "approved",
        approved_docs_path=tmp_dir / "approved_docs.jsonl",
        attachment_service=attachment_service,
    )


def _make_service_with_sync(
    tmp_dir,
    *,
    attachment_service: AttachmentService | None = None,
    unified_sync_callback=None,
):
    return KnowledgeReviewService(
        draft_dir=tmp_dir / "drafts",
        approved_dir=tmp_dir / "approved",
        approved_docs_path=tmp_dir / "approved_docs.jsonl",
        attachment_service=attachment_service,
        unified_sync_callback=unified_sync_callback,
    )


def _enable_attachment_settings(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENTS_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_FILE_BYTES", 2 * 1024 * 1024)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_TEXT_CHARS", 6000)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_EXCERPT_CHARS", 180)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_ATTACHMENT_CHUNK_CHARS", 120)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_ATTACHMENT_CHUNK_OVERLAP_CHARS", 20)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_ATTACHMENT_MAX_CHUNKS_PER_FILE", 4)


def test_knowledge_review_creates_traceable_draft(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_service(tmp_dir)

    draft = service.create_draft(
        question="What is the latest view on HDFC Bank?",
        answer=(
            "HDFC Bank remains in a strong position. "
            "FII support improved in the latest market read. "
            "Dividend visibility is stable for the near term."
        ),
        intent="STOCK",
        session_id="abcd1234",
        research={
            "used": True,
            "sources": [
                {
                    "title": "HDFC Bank update",
                    "url": "https://example.com/hdfc",
                    "published_at": "2026-08-04",
                    "snippet": "Net profit improved in the latest quarter.",
                }
            ],
        },
        attachments=[
            {
                "name": "bank-note.pdf",
                "excerpt": "Management commentary on margins.",
                "storage_key": "bank-note.pdf",
                "kind": "pdf",
            }
        ],
    )

    assert draft.intent == "STOCK"
    assert draft.session_id == "abcd1234"
    assert draft.sources[0].kind == "research"
    assert draft.sources[0].url == "https://example.com/hdfc"
    assert draft.sources[1].kind == "attachment"
    assert draft.sources[1].storage_key == "bank-note.pdf"
    assert "stock" in draft.tags
    assert (tmp_dir / "drafts" / f"{draft.draft_id}.json").exists()


def test_knowledge_review_approval_writes_docs_and_deduplicates(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_service(tmp_dir)
    draft = service.create_draft(
        question="Summarize the banking sector setup.",
        answer="Banking is leading. FII flows are positive. Valuation support remains healthy.",
        intent="SECTOR",
    )

    saved_first = service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
        review_note="Useful institutional context.",
    )
    saved_second = service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
    )

    approved_path = tmp_dir / "approved" / f"{saved_first['doc_id']}.json"
    assert approved_path.exists()
    assert saved_first["duplicate"] is False
    assert saved_second["duplicate"] is True

    approved_doc_lines = (tmp_dir / "approved_docs.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(approved_doc_lines) == 1
    approved_doc = json.loads(approved_doc_lines[0])
    assert approved_doc["doc_id"] == saved_first["doc_id"]
    assert approved_doc["domain"] == "USER_KNOWLEDGE"


def test_knowledge_review_approval_triggers_unified_sync_once_per_real_save(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    sync_calls: list[dict] = []

    service = _make_service_with_sync(
        tmp_dir,
        unified_sync_callback=lambda **kwargs: sync_calls.append(kwargs) or {"ok": True},
    )
    draft = service.create_draft(
        question="Summarize the banking sector setup.",
        answer="Banking is leading. FII flows are positive. Valuation support remains healthy.",
        intent="SECTOR",
    )

    saved_first = service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
    )
    service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
    )

    assert len(sync_calls) == 1
    assert sync_calls[0]["reason"] == "knowledge_approved"
    assert sync_calls[0]["source_doc_id"] == saved_first["doc_id"]


def test_knowledge_review_approval_preserves_research_provenance_in_doc_meta(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_service(tmp_dir)
    draft = service.create_draft(
        question="What is the latest outside view on HDFC Bank?",
        answer="Outside research says HDFC Bank stays strong, but the user still needs to review before saving.",
        intent="STOCK",
        research={
            "used": True,
            "provider": "ddgs",
            "temporary": True,
            "save_requires_review": True,
            "conflict_note": "Outside research is more cautious than saved memory on this topic.",
            "governance_note": "Outside research stays temporary unless you explicitly save it through review.",
            "sources": [
                {
                    "title": "HDFC Bank update",
                    "url": "https://example.com/hdfc-bank",
                    "published_at": "2026-08-04",
                    "snippet": "Quarterly trends still look stable.",
                }
            ],
        },
    )

    saved = service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
    )

    approved_doc = json.loads((tmp_dir / "approved_docs.jsonl").read_text(encoding="utf-8").splitlines()[0])
    meta = approved_doc["meta"]

    assert saved["doc_id"] == approved_doc["doc_id"]
    assert meta["research_used"] is True
    assert meta["research_source_count"] == 1
    assert meta["latest_research_date"] == "2026-08-04"
    assert meta["research_sources"][0]["title"] == "HDFC Bank update"
    assert meta["research_sources"][0]["url"] == "https://example.com/hdfc-bank"
    assert meta["research_conflict_note"] == "Outside research is more cautious than saved memory on this topic."
    assert "temporary unless you explicitly save it" in (meta["research_governance_note"] or "")


def test_knowledge_review_build_context_returns_saved_memory(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_service(tmp_dir)
    draft = service.create_draft(
        question="What is the current setup in banking?",
        answer=(
            "Banking sector rotation remains strong. "
            "FII buying is supportive and private banks are still leading."
        ),
        intent="SECTOR",
    )
    service.approve(
        draft.draft_id,
        title="Banking rotation setup",
        summary="Banking remains strong with supportive FII buying.",
        facts=[
            "Banking sector rotation remains strong.",
            "FII buying is supportive.",
        ],
        tags=["banking", "rotation", "fii"],
    )

    context = service.build_context("Which banking sector setup still looks strong?", top_k=1)

    assert "Reviewed knowledge below was explicitly approved" in context
    assert "banking rotation setup" in context.lower()
    assert "supportive fii buying" in context.lower()


def test_knowledge_review_approval_saves_attachment_document_memory(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    _enable_attachment_settings(monkeypatch)
    attachment_service = AttachmentService(upload_dir=tmp_dir / "uploads")
    service = _make_service(tmp_dir, attachment_service=attachment_service)

    uploaded = attachment_service.save_upload(
        filename="astro-book.txt",
        content_type="text/plain",
        content=(
            b"Jupiter transit rules help time expansion cycles in long-range analysis. "
            b"Mercury periods often change communication and trading behavior. "
            b"Saturn themes can slow momentum and force delayed results."
        ),
    )
    draft = service.create_draft(
        question="Study this astrology book and remember the key ideas.",
        answer="I studied the uploaded book and extracted the main rules for later review.",
        intent="RESEARCH",
        attachments=[uploaded.to_chat_stub()],
    )

    saved = service.approve(
        draft.draft_id,
        title="Astrology timing notes",
        summary="Key timing notes from the uploaded astrology book.",
        facts=[
            "Jupiter transit rules help time expansion cycles in long-range analysis.",
            "Saturn themes can slow momentum and force delayed results.",
        ],
        tags=["astrology", "timing", "book"],
    )

    approved_doc_lines = (tmp_dir / "approved_docs.jsonl").read_text(encoding="utf-8").splitlines()
    approved_docs = [json.loads(line) for line in approved_doc_lines]
    attachment_docs = [doc for doc in approved_docs if doc["domain"] == "USER_ATTACHMENT_KNOWLEDGE"]

    assert saved["attachment_doc_count"] == 1
    assert saved["attachment_chunk_count"] == len(attachment_docs)
    assert attachment_docs
    assert any("Jupiter transit rules" in doc["text"] for doc in attachment_docs)
    assert all(doc["meta"]["parent_doc_id"] == saved["doc_id"] for doc in attachment_docs)

    context = service.build_context("What did the saved book say about Jupiter transit?", top_k=2)

    assert "attachment memory" in context
    assert "jupiter transit rules" in context.lower()


def test_knowledge_review_flags_exact_duplicate_attachment_for_discard(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    _enable_attachment_settings(monkeypatch)
    attachment_service = AttachmentService(upload_dir=tmp_dir / "uploads")
    service = _make_service(tmp_dir, attachment_service=attachment_service)

    uploaded = attachment_service.save_upload(
        filename="astro-duplicate.txt",
        content_type="text/plain",
        content=(
            b"Jupiter periods support growth and expansion. "
            b"Saturn periods slow momentum and test discipline."
        ),
    )
    first_draft = service.create_draft(
        question="Study this book and remember it.",
        answer="I extracted the timing rules from the uploaded book.",
        intent="RESEARCH",
        attachments=[uploaded.to_chat_stub()],
    )
    service.approve(
        first_draft.draft_id,
        title="Astro timing rules",
        summary="Timing rules extracted from the uploaded book.",
        facts=[
            "Jupiter periods support growth and expansion.",
            "Saturn periods slow momentum and test discipline.",
        ],
        tags=["astrology", "timing", "book"],
    )

    uploaded_renamed = attachment_service.save_upload(
        filename="astro-duplicate-renamed.txt",
        content_type="text/plain",
        content=(
            b"Jupiter periods support growth and expansion. "
            b"Saturn periods slow momentum and test discipline."
        ),
    )
    second_draft = service.create_draft(
        question="Study this book and remember it again.",
        answer="I extracted the timing rules from the uploaded book again.",
        intent="RESEARCH",
        attachments=[uploaded_renamed.to_chat_stub()],
    )

    assert second_draft.suggested_action == "discard"
    assert "already has the same readable file memory" in (second_draft.suggestion_reason or "")
    assert second_draft.existing_matches
    assert second_draft.existing_matches[0].exact_duplicate is True


def test_knowledge_review_flags_strong_same_topic_overlap_without_new_attachment(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_service(tmp_dir)

    baseline = service.create_draft(
        question="Explain banking sector rotation and FII support.",
        answer=(
            "Banking sector rotation remains strong. "
            "FII support keeps private bank leadership intact. "
            "Banking sector rotation and FII support remain the main theme."
        ),
        intent="SECTOR",
    )
    service.approve(
        baseline.draft_id,
        title="Banking rotation and FII support",
        summary="Banking sector rotation remains strong with FII support and private bank leadership.",
        facts=[
            "Banking sector rotation remains strong.",
            "FII support keeps private bank leadership intact.",
            "Banking sector rotation and FII support remain the main theme.",
        ],
        tags=["banking", "rotation", "fii", "sector"],
    )

    follow_up = service.create_draft(
        question="Explain banking sector rotation and FII support in private banking leadership today.",
        answer=(
            "Banking sector rotation stays strong because FII support keeps private banking leadership intact. "
            "Banking sector rotation plus FII support remains the main banking theme today."
        ),
        intent="SECTOR",
    )

    assert follow_up.existing_matches
    assert follow_up.suggested_action == "discard"
    assert "already covers nearly the same topic" in (follow_up.suggestion_reason or "")
    assert follow_up.existing_matches[0].overlap_score >= 12


def test_knowledge_review_warns_but_allows_save_for_new_attachment_on_same_topic(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    _enable_attachment_settings(monkeypatch)
    attachment_service = AttachmentService(upload_dir=tmp_dir / "uploads")
    service = _make_service(tmp_dir, attachment_service=attachment_service)

    first_upload = attachment_service.save_upload(
        filename="astro-book-one.txt",
        content_type="text/plain",
        content=(
            b"Jupiter periods support growth and expansion. "
            b"Saturn periods slow momentum and test discipline."
        ),
    )
    first_draft = service.create_draft(
        question="Study this first astrology book.",
        answer="I extracted the main timing rules from the first uploaded book.",
        intent="RESEARCH",
        attachments=[first_upload.to_chat_stub()],
    )
    first_saved = service.approve(
        first_draft.draft_id,
        title="Astro timing rules",
        summary="Timing rules from the first astrology book.",
        facts=[
            "Jupiter periods support growth and expansion.",
            "Saturn periods slow momentum and test discipline.",
        ],
        tags=["astrology", "timing", "book"],
    )

    second_upload = attachment_service.save_upload(
        filename="astro-book-two.txt",
        content_type="text/plain",
        content=(
            b"Jupiter periods support growth and expansion. "
            b"Mercury periods change communication and trading behavior."
        ),
    )
    second_draft = service.create_draft(
        question="Study this second astrology book on the same topic.",
        answer="I found a similar topic, but this uploaded book adds Mercury timing details.",
        intent="RESEARCH",
        attachments=[second_upload.to_chat_stub()],
    )

    assert second_draft.existing_matches
    assert second_draft.suggested_action == "merge"
    assert "Merge is recommended" in (second_draft.suggestion_reason or "")
    assert second_draft.existing_matches[0].exact_duplicate is False
    assert "Possible new value" in (second_draft.existing_matches[0].new_value_hint or "")

    merged = service.approve(
        second_draft.draft_id,
        title=second_draft.title,
        summary=second_draft.summary,
        facts=second_draft.facts,
        tags=second_draft.tags,
        decision="merge",
    )

    assert merged["decision"] == "merge"
    assert merged["doc_id"] == first_saved["doc_id"]
    merged_record = json.loads((tmp_dir / "approved" / f"{first_saved['doc_id']}.json").read_text(encoding="utf-8"))
    assert merged_record["merge_count"] == 1
    assert merged_record["attachment_doc_count"] == 2
    approved_docs = [
        json.loads(line)
        for line in (tmp_dir / "approved_docs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    root_docs = [doc for doc in approved_docs if doc["domain"] == "USER_KNOWLEDGE"]
    assert len(root_docs) == 1
    context = service.build_context("What do the saved astrology books say about Mercury periods?", top_k=3)
    assert "mercury periods change communication and trading behavior" in context.lower()


def test_knowledge_review_merge_triggers_unified_sync(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    _enable_attachment_settings(monkeypatch)
    sync_calls: list[dict] = []
    attachment_service = AttachmentService(upload_dir=tmp_dir / "uploads")
    service = _make_service_with_sync(
        tmp_dir,
        attachment_service=attachment_service,
        unified_sync_callback=lambda **kwargs: sync_calls.append(kwargs) or {"ok": True},
    )

    first_upload = attachment_service.save_upload(
        filename="astro-book-one.txt",
        content_type="text/plain",
        content=(
            b"Jupiter periods support growth and expansion. "
            b"Saturn periods slow momentum and test discipline."
        ),
    )
    first_draft = service.create_draft(
        question="Study this first astrology book.",
        answer="I extracted the main timing rules from the first uploaded book.",
        intent="RESEARCH",
        attachments=[first_upload.to_chat_stub()],
    )
    first_saved = service.approve(
        first_draft.draft_id,
        title="Astro timing rules",
        summary="Timing rules from the first astrology book.",
        facts=[
            "Jupiter periods support growth and expansion.",
            "Saturn periods slow momentum and test discipline.",
        ],
        tags=["astrology", "timing", "book"],
    )
    sync_calls.clear()

    second_upload = attachment_service.save_upload(
        filename="astro-book-two.txt",
        content_type="text/plain",
        content=(
            b"Jupiter periods support growth and expansion. "
            b"Mercury periods change communication and trading behavior."
        ),
    )
    second_draft = service.create_draft(
        question="Study this second astrology book on the same topic.",
        answer="I found a similar topic, but this uploaded book adds Mercury timing details.",
        intent="RESEARCH",
        attachments=[second_upload.to_chat_stub()],
    )

    result = service.approve(
        second_draft.draft_id,
        title=second_draft.title,
        summary=second_draft.summary,
        facts=second_draft.facts,
        tags=second_draft.tags,
        decision="merge",
    )

    assert result["decision"] == "merge"
    assert result["doc_id"] == first_saved["doc_id"]
    assert len(sync_calls) == 1
    assert sync_calls[0]["reason"] == "knowledge_merged"
    assert sync_calls[0]["source_doc_id"] == first_saved["doc_id"]


def test_knowledge_review_discard_removes_saved_draft(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_service(tmp_dir)

    draft = service.create_draft(
        question="Keep this only if I approve it.",
        answer="This draft should be removed when I discard it.",
        intent="RESEARCH",
    )

    result = service.discard(draft.draft_id)

    assert result == {
        "draft_id": draft.draft_id,
        "status": "discarded",
    }
    assert not (tmp_dir / "drafts" / f"{draft.draft_id}.json").exists()
