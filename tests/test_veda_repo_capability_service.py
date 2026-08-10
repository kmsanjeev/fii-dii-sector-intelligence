from __future__ import annotations

import json

import pytest

from engines.ai.capabilities.service import RepoCapabilityService
from engines.common import config as cfg


def _make_service(tmp_dir):
    return RepoCapabilityService(
        draft_dir=tmp_dir / "drafts",
        approved_dir=tmp_dir / "approved",
        approved_docs_path=tmp_dir / "approved_docs.jsonl",
    )


def _make_service_with_sync(tmp_dir, *, unified_sync_callback=None):
    return RepoCapabilityService(
        draft_dir=tmp_dir / "drafts",
        approved_dir=tmp_dir / "approved",
        approved_docs_path=tmp_dir / "approved_docs.jsonl",
        unified_sync_callback=unified_sync_callback,
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
        "# Research Agent\n\nThis repo documents reusable prompt and workflow patterns for research mode.\n",
        encoding="utf-8",
    )
    (repo_dir / "skills").mkdir(exist_ok=True)
    (repo_dir / "skills" / "research_workflow.md").write_text(
        "# Research Workflow\n\nUse source-aware prompts and explicit citation rules.\n",
        encoding="utf-8",
    )
    (repo_dir / "utils").mkdir(exist_ok=True)
    (repo_dir / "utils" / "retry.py").write_text(
        "def retry_request():\n    return 'ok'\n\nclass SearchTool:\n    pass\n",
        encoding="utf-8",
    )


def test_repo_capability_draft_extracts_license_and_candidate_files(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_MAX_CANDIDATE_FILES", 6)
    repo_dir = tmp_dir / "agent-lab"
    _write_mit_repo(repo_dir)
    service = _make_service(tmp_dir)

    draft = service.create_draft(
        repo_path=str(repo_dir),
        repo_label="Agent Lab",
        focus="research prompts",
    )

    assert draft.repo_label == "Agent Lab"
    assert draft.license_name == "MIT"
    assert draft.license_path == "LICENSE"
    assert "mit_repo" in draft.tags
    assert any(path.endswith("skills/research_workflow.md") for path in draft.candidate_files)
    assert any(path.endswith("utils/retry.py") for path in draft.candidate_files)
    assert draft.sources[0].kind == "repo_license"
    assert any(source.kind == "tool" for source in draft.sources[1:])
    assert (tmp_dir / "drafts" / f"{draft.draft_id}.json").exists()


def test_repo_capability_requires_mit_license(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_MAX_CANDIDATE_FILES", 6)
    repo_dir = tmp_dir / "not-mit"
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "LICENSE").write_text("Apache License Version 2.0", encoding="utf-8")
    (repo_dir / "README.md").write_text("# Another Repo\n\nPrompt ideas live here.\n", encoding="utf-8")
    service = _make_service(tmp_dir)

    with pytest.raises(ValueError, match="MIT license"):
        service.create_draft(repo_path=str(repo_dir))


def test_repo_capability_approval_writes_docs_and_builds_context(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_MAX_CANDIDATE_FILES", 6)
    repo_dir = tmp_dir / "memory-kit"
    _write_mit_repo(repo_dir)
    service = _make_service(tmp_dir)
    draft = service.create_draft(
        repo_path=str(repo_dir),
        repo_label="Memory Kit",
        focus="memory workflows",
    )

    saved_first = service.approve(
        draft.draft_id,
        title=draft.title,
        summary=draft.summary,
        facts=draft.facts,
        tags=draft.tags,
        review_note="Useful for approved Veda capability upgrades.",
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
    assert approved_doc["domain"] == "MIT_REPO_CAPABILITY"
    assert approved_doc["meta"]["license_name"] == "MIT"

    context = service.build_context("Show approved memory workflow ideas from MIT repos", top_k=1)

    assert "MIT repo capability notes below came from MIT-licensed repositories" in context
    assert "memory kit" in context.lower()
    assert "license=MIT" in context


def test_repo_capability_approval_triggers_unified_sync_once_per_real_save(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_FACTS", 6)
    monkeypatch.setattr(cfg, "VEDA_KNOWLEDGE_MAX_TAGS", 8)
    monkeypatch.setattr(cfg, "VEDA_MIT_REPO_MAX_CANDIDATE_FILES", 6)
    sync_calls: list[dict] = []

    repo_dir = tmp_dir / "memory-kit"
    _write_mit_repo(repo_dir)
    service = _make_service_with_sync(
        tmp_dir,
        unified_sync_callback=lambda **kwargs: sync_calls.append(kwargs) or {"ok": True},
    )
    draft = service.create_draft(
        repo_path=str(repo_dir),
        repo_label="Memory Kit",
        focus="memory workflows",
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
    assert sync_calls[0]["reason"] == "capability_approved"
    assert sync_calls[0]["source_doc_id"] == saved_first["doc_id"]
