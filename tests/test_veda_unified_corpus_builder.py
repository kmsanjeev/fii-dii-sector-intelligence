from __future__ import annotations

import json

from engines.ai.capabilities.service import RepoCapabilityService
from engines.ai.knowledge.review_service import KnowledgeReviewService
from engines.ai.knowledge.unified_corpus_builder import UnifiedCorpusBuilder
from engines.common import config as cfg


def _make_review_service(tmp_dir):
    return KnowledgeReviewService(
        draft_dir=tmp_dir / "drafts",
        approved_dir=tmp_dir / "approved",
        approved_docs_path=tmp_dir / "reviewed_docs.jsonl",
    )


def _make_repo_service(tmp_dir):
    return RepoCapabilityService(
        draft_dir=tmp_dir / "repo_drafts",
        approved_dir=tmp_dir / "repo_approved",
        approved_docs_path=tmp_dir / "capability_docs.jsonl",
    )


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
        "# Memory Research\n\nReusable prompt and workflow ideas.\n",
        encoding="utf-8",
    )
    (repo_dir / "skills").mkdir(exist_ok=True)
    (repo_dir / "skills" / "memory.md").write_text(
        "# Memory Guide\n\nUse source-aware memory summaries.\n",
        encoding="utf-8",
    )


def _write_jsonl(path, docs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=False) + "\n")


def test_unified_corpus_builder_combines_current_durable_sources(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_MAX_CANDIDATE_FILES", 6)

    platform_docs_path = tmp_dir / "documents.jsonl"
    reviewed_docs_path = tmp_dir / "reviewed_docs.jsonl"
    capability_docs_path = tmp_dir / "capability_docs.jsonl"
    unified_docs_path = tmp_dir / "veda_unified_documents.jsonl"
    manifest_path = tmp_dir / "veda_unified_manifest.json"
    metadata_path = tmp_dir / "veda_unified_metadata.csv"

    _write_jsonl(
        platform_docs_path,
        [
            {
                "doc_id": "market_regime",
                "domain": "MARKET",
                "entity": "MARKET_REGIME",
                "text": "Market regime is ACCUMULATION with positive FII support.",
                "meta": {"date": "2026-08-04", "regime": "ACCUMULATION"},
            }
        ],
    )

    review_service = _make_review_service(tmp_dir)
    draft = review_service.create_draft(
        question="What is the current banking setup?",
        answer="Banking remains strong and FII support is still healthy.",
        intent="SECTOR",
    )
    review_service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
    )

    repo_dir = tmp_dir / "agent-lab"
    _write_mit_repo(repo_dir)
    repo_service = _make_repo_service(tmp_dir)
    repo_draft = repo_service.create_draft(
        repo_path=str(repo_dir),
        repo_label="Agent Lab",
        focus="memory workflows",
    )
    repo_service.approve(
        repo_draft.draft_id,
        title=repo_draft.title,
        summary=repo_draft.summary,
        facts=repo_draft.facts,
        tags=repo_draft.tags,
    )

    builder = UnifiedCorpusBuilder(
        platform_docs_path=platform_docs_path,
        reviewed_docs_path=reviewed_docs_path,
        capability_docs_path=capability_docs_path,
        unified_docs_path=unified_docs_path,
        manifest_path=manifest_path,
        metadata_path=metadata_path,
    )
    summary = builder.run()

    assert summary["total_records"] == 3
    assert summary["source_counts"]["platform_intelligence"] == 1
    assert summary["source_counts"]["user_reviewed"] == 1
    assert summary["source_counts"]["mit_repo_capability"] == 1
    assert summary["domain_counts"]["MARKET"] == 1
    assert summary["domain_counts"]["SECTOR"] == 1
    assert summary["domain_counts"]["MIT_REPO_CAPABILITY"] == 1
    assert summary["missing_critical_field_count"] == 0
    assert unified_docs_path.exists()
    assert manifest_path.exists()
    assert metadata_path.exists()

    docs = [json.loads(line) for line in unified_docs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(docs) == 3
    assert any(doc["source_type"] == "platform_intelligence" for doc in docs)
    assert any(doc["source_type"] == "user_reviewed" for doc in docs)
    assert any(doc["source_type"] == "mit_repo_capability" for doc in docs)


def test_unified_corpus_builder_reports_exact_duplicates(tmp_dir):
    platform_docs_path = tmp_dir / "documents.jsonl"
    duplicate_text = "Sector rotation is improving and accumulation remains strong."
    _write_jsonl(
        platform_docs_path,
        [
            {
                "doc_id": "sector_banking_a",
                "domain": "SECTOR",
                "entity": "BANKING",
                "text": duplicate_text,
                "meta": {"sector": "BANKING"},
            },
            {
                "doc_id": "sector_banking_b",
                "domain": "SECTOR",
                "entity": "BANKING",
                "text": duplicate_text,
                "meta": {"sector": "BANKING"},
            },
        ],
    )

    builder = UnifiedCorpusBuilder(
        platform_docs_path=platform_docs_path,
        reviewed_docs_path=tmp_dir / "missing_reviewed.jsonl",
        capability_docs_path=tmp_dir / "missing_capability.jsonl",
        unified_docs_path=tmp_dir / "veda_unified_documents.jsonl",
        manifest_path=tmp_dir / "veda_unified_manifest.json",
        metadata_path=tmp_dir / "veda_unified_metadata.csv",
    )
    summary = builder.run()

    assert summary["total_records"] == 2
    assert summary["duplicate_group_count"] == 1
    assert summary["duplicates"][0]["count"] == 2
    assert set(summary["duplicates"][0]["doc_ids"]) == {"sector_banking_a", "sector_banking_b"}
