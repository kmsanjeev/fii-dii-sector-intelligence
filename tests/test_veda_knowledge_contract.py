from __future__ import annotations

import json

from engines.ai.attachments.service import AttachmentService
from engines.ai.capabilities.service import RepoCapabilityService
from engines.ai.knowledge.contracts import (
    CONTRACT_VERSION,
    from_attachment_chunk,
    from_approved_core,
    from_platform_doc,
    from_repo_capability,
    from_reviewed_memory,
    normalize_knowledge_record,
)
from engines.ai.knowledge.review_service import KnowledgeReviewService
from engines.common import config as cfg


def _make_review_service(tmp_dir, *, attachment_service: AttachmentService | None = None):
    return KnowledgeReviewService(
        draft_dir=tmp_dir / "drafts",
        approved_dir=tmp_dir / "approved",
        approved_docs_path=tmp_dir / "approved_docs.jsonl",
        attachment_service=attachment_service,
    )


def _make_repo_service(tmp_dir):
    return RepoCapabilityService(
        draft_dir=tmp_dir / "repo_drafts",
        approved_dir=tmp_dir / "repo_approved",
        approved_docs_path=tmp_dir / "repo_docs.jsonl",
    )


def _enable_attachment_settings(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENTS_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_FILE_BYTES", 2 * 1024 * 1024)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_MAX_TEXT_CHARS", 6000)
    monkeypatch.setattr(cfg, "VEDA_ATTACHMENT_EXCERPT_CHARS", 180)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_ATTACHMENT_CHUNK_CHARS", 120)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_ATTACHMENT_CHUNK_OVERLAP_CHARS", 20)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_ATTACHMENT_MAX_CHUNKS_PER_FILE", 4)


def _write_mit_repo(repo_dir):
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "LICENSE").write_text(
        (
            "MIT License\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files.\n\n"
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.\n'
        ),
        encoding="utf-8",
    )
    (repo_dir / "README.md").write_text(
        "# Research Agent\n\nThis repo documents reusable prompt and workflow patterns for research mode.\n",
        encoding="utf-8",
    )
    (repo_dir / "skills").mkdir(exist_ok=True)
    (repo_dir / "skills" / "research_workflow.md").write_text(
        "# Research Workflow\n\nUse source-aware prompts and explicit citation rules.\n",
        encoding="utf-8",
    )


def test_contract_normalizes_platform_rag_doc():
    doc = {
        "doc_id": "market_regime",
        "domain": "MARKET",
        "entity": "MARKET_REGIME",
        "text": "Market regime is ACCUMULATION with positive FII flows.",
        "meta": {
            "date": "2026-08-04",
            "regime": "ACCUMULATION",
        },
    }

    record = from_platform_doc(doc)
    payload = record.to_dict()

    assert payload["contract_version"] == CONTRACT_VERSION
    assert record.source_type == "platform_intelligence"
    assert record.domain == "MARKET"
    assert record.entity_keys.regime == "ACCUMULATION"
    assert payload["effective_date"] == "2026-08-04"
    assert payload["freshness_class"] == "dated_snapshot"
    assert payload["approval_state"] == "system_generated"
    assert payload["evidence_kind"] == "platform_signal_snapshot"
    assert "local platform snapshot" in (payload["reliability_note"] or "").lower()


def test_contract_marks_stock_ml_doc_as_predictive_signal():
    doc = {
        "doc_id": "stock_ethosltd",
        "domain": "STOCK",
        "entity": "ETHOSLTD",
        "text": (
            "Stock Analysis: ETHOSLTD. ML bull run score is 80.78 and accumulation score is 99.70. "
            "Bull run score remains strong."
        ),
        "meta": {
            "symbol": "ETHOSLTD",
            "sector": "FMCG",
            "label": "BULL_RUN",
            "ml_bull_run_score": 80.78,
            "accumulation_score": 99.70,
            "feature_date": "2026-08-04",
        },
    }

    record = from_platform_doc(doc)
    payload = record.to_dict()

    assert payload["evidence_kind"] == "predictive_ml_signal"
    assert payload["model_name"] == cfg.VEDA_PLATFORM_ML_MODEL_NAME
    assert payload["model_version"] == cfg.VEDA_PLATFORM_ML_MODEL_VERSION
    assert payload["effective_date"] == "2026-08-04"
    assert "bullish continuation signal" in (payload["score_meaning"] or "").lower()
    assert "not guaranteed fact" in (payload["reliability_note"] or "").lower()


def test_contract_normalizes_reviewed_memory_doc(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_review_service(tmp_dir)
    draft = service.create_draft(
        question="What is the banking setup now?",
        answer="Banking remains strong. FII buying is supportive and private banks still lead.",
        intent="SECTOR",
        research={
            "used": True,
            "provider": "ddgs",
            "temporary": True,
            "save_requires_review": True,
            "governance_note": "Outside research stays temporary unless you explicitly save it through review.",
            "sources": [
                {
                    "title": "Banking sector update",
                    "url": "https://example.com/banking",
                    "published_at": "2026-08-04",
                    "snippet": "Private banks still lead the sector move.",
                }
            ],
        },
    )
    service.approve(
        draft.draft_id,
        title="Banking setup",
        summary="Banking remains strong with supportive FII buying.",
        facts=[
            "Banking remains strong.",
            "FII buying is supportive.",
        ],
        tags=["banking", "fii"],
    )

    doc = json.loads((tmp_dir / "approved_docs.jsonl").read_text(encoding="utf-8").splitlines()[0])
    record = from_reviewed_memory(doc)
    payload = record.to_dict()

    assert record.source_type == "user_reviewed"
    assert record.domain == "SECTOR"
    assert record.entity_keys.intent == "SECTOR"
    assert payload["approval_state"] == "user_approved"
    assert payload["saved_at"]
    assert payload["provenance"]["source_kind"] == "approved_reviewed_memory"
    assert payload["provenance"]["source_date"] == "2026-08-04"
    assert payload["provenance"]["details"]["research_used"] is True
    assert payload["provenance"]["details"]["research_source_count"] == 1
    assert payload["provenance"]["details"]["research_sources"][0]["title"] == "Banking sector update"


def test_contract_normalizes_attachment_chunk_doc(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    _enable_attachment_settings(monkeypatch)
    attachment_service = AttachmentService(upload_dir=tmp_dir / "uploads")
    service = _make_review_service(tmp_dir, attachment_service=attachment_service)

    uploaded = attachment_service.save_upload(
        filename="astro-book.txt",
        content_type="text/plain",
        content=(
            b"Jupiter transit rules help time expansion cycles. "
            b"Saturn themes slow momentum and delay results."
        ),
    )
    draft = service.create_draft(
        question="Study this book and remember it.",
        answer="I extracted the main timing rules from the uploaded book.",
        intent="RESEARCH",
        attachments=[uploaded.to_chat_stub()],
    )
    service.approve(
        draft.draft_id,
        title="Astro timing notes",
        summary="Key timing notes from the uploaded astrology book.",
        facts=[
            "Jupiter transit rules help time expansion cycles.",
            "Saturn themes slow momentum and delay results.",
        ],
        tags=["astrology", "timing", "book"],
    )

    approved_docs = [
        json.loads(line)
        for line in (tmp_dir / "approved_docs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    attachment_doc = next(doc for doc in approved_docs if doc["domain"] == "USER_ATTACHMENT_KNOWLEDGE")
    record = from_attachment_chunk(attachment_doc)
    payload = record.to_dict()

    assert record.source_type == "attachment_chunk"
    assert record.domain == "RESEARCH"
    assert record.entity_keys.attachment_name == "astro-book.txt"
    assert payload["provenance"]["attachment_hash"]
    assert payload["freshness_class"] == "durable_memory"


def test_contract_normalizes_repo_capability_doc(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_MAX_CANDIDATE_FILES", 6)
    repo_dir = tmp_dir / "agent-lab"
    _write_mit_repo(repo_dir)
    service = _make_repo_service(tmp_dir)
    draft = service.create_draft(
        repo_path=str(repo_dir),
        repo_label="Agent Lab",
        focus="research prompts",
    )
    service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
    )

    doc = json.loads((tmp_dir / "repo_docs.jsonl").read_text(encoding="utf-8").splitlines()[0])
    record = from_repo_capability(doc)
    payload = record.to_dict()

    assert record.source_type == "mit_repo_capability"
    assert record.domain == "MIT_REPO_CAPABILITY"
    assert record.license_name == "MIT"
    assert payload["provenance"]["repo_label"] == "Agent Lab"
    assert payload["approval_state"] == "user_approved"


def test_contract_auto_routes_current_doc_shapes(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    service = _make_review_service(tmp_dir)
    draft = service.create_draft(
        question="Summarize the market setup.",
        answer="Market regime remains constructive with positive FII support.",
        intent="MARKET",
    )
    service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
    )

    doc = json.loads((tmp_dir / "approved_docs.jsonl").read_text(encoding="utf-8").splitlines()[0])
    record = normalize_knowledge_record(doc)

    assert record.source_type == "user_reviewed"
    assert record.domain == "MARKET"


def test_contract_normalizes_approved_core_doc():
    doc = {
        "doc_id": "veda_core_claim_1",
        "domain": "VEDA",
        "entity": "VIMSHOTTARI_DASHA",
        "text": "Approved core claim for Vimshottari dasha foundation.",
        "meta": {
            "memory_type": "approved_core",
            "governance_zone": "APPROVED_CORE",
            "core_id": "VEDA-RCORE-000123",
            "promotion_id": "VEDA-RPRM-000123",
            "claim_ids": ["VEDA-CLM-000123"],
            "passage_ids": ["VEDA-PSG-000123"],
            "source_ids": ["VEDA-SRC-000123"],
            "rule_ids": ["VEDA-RUL-DASHA-000123"],
            "high_stakes": False,
            "created_at": "2026-08-11T05:00:00Z",
        },
    }

    routed = normalize_knowledge_record(doc)
    direct = from_approved_core(doc)

    assert routed.source_type == "approved_core"
    assert routed.approval_state == "admin_promoted_core"
    assert routed.provenance.source_kind == "approved_core_knowledge"
    assert routed.provenance.details["promotion_id"] == "VEDA-RPRM-000123"
    assert routed.provenance.details["claim_ids"] == ["VEDA-CLM-000123"]
    assert routed.freshness.classification == "governed_core"
    assert direct.entity == "VIMSHOTTARI_DASHA"
