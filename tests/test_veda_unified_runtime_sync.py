from __future__ import annotations

from engines.ai.knowledge import unified_bm25_indexer
from engines.ai.knowledge import unified_corpus_builder
from engines.ai.knowledge import unified_faiss_indexer
from engines.ai.knowledge.unified_runtime_sync import refresh_unified_retrieval_assets


def test_unified_runtime_sync_skips_when_disabled(monkeypatch):
    from engines.ai.knowledge import unified_runtime_sync

    monkeypatch.setattr(unified_runtime_sync.cfg, "VEDA_UNIFIED_RETRIEVAL_SYNC_ON_SAVE", False)

    result = refresh_unified_retrieval_assets(reason="knowledge_approved", source_doc_id="doc-1")

    assert result == {
        "ok": False,
        "skipped": True,
        "reason": "sync_disabled",
        "source_doc_id": "doc-1",
    }


def test_unified_runtime_sync_reports_bm25_only_when_faiss_refresh_fails(monkeypatch):
    from engines.ai.knowledge import unified_runtime_sync

    calls: dict[str, object] = {}

    class FakeCorpusBuilder:
        def run(self):
            calls["corpus"] = True
            return {"total_records": 7}

    class FakeBM25Indexer:
        def run(self):
            calls["bm25"] = True
            return True

    class FakeFAISSIndexer:
        def __init__(self, *, local_files_only: bool = False):
            calls["local_files_only"] = local_files_only

        def run(self):
            raise RuntimeError("local embedding model not cached")

    monkeypatch.setattr(unified_runtime_sync.cfg, "VEDA_UNIFIED_RETRIEVAL_SYNC_ON_SAVE", True)
    monkeypatch.setattr(unified_runtime_sync.cfg, "VEDA_UNIFIED_FAISS_SYNC_ON_SAVE", True)
    monkeypatch.setattr(unified_runtime_sync.cfg, "VEDA_UNIFIED_FAISS_LOCAL_ONLY_ON_SAVE", True)
    monkeypatch.setattr(unified_corpus_builder, "UnifiedCorpusBuilder", FakeCorpusBuilder)
    monkeypatch.setattr(unified_bm25_indexer, "UnifiedBM25Indexer", FakeBM25Indexer)
    monkeypatch.setattr(unified_faiss_indexer, "UnifiedFAISSIndexer", FakeFAISSIndexer)

    result = refresh_unified_retrieval_assets(reason="knowledge_approved", source_doc_id="doc-2")

    assert calls == {
        "corpus": True,
        "bm25": True,
        "local_files_only": True,
    }
    assert result["ok"] is True
    assert result["mode"] == "bm25_only"
    assert result["bm25_ready"] is True
    assert result["faiss_ready"] is False
    assert result["faiss_skipped"] is False
    assert result["faiss_error"] == "local embedding model not cached"
    assert result["total_records"] == 7


def test_unified_runtime_sync_skips_faiss_on_save_by_default(monkeypatch):
    from engines.ai.knowledge import unified_runtime_sync

    calls: dict[str, object] = {}

    class FakeCorpusBuilder:
        def run(self):
            calls["corpus"] = True
            return {"total_records": 3}

    class FakeBM25Indexer:
        def run(self):
            calls["bm25"] = True
            return True

    class FakeFAISSIndexer:
        def __init__(self, *, local_files_only: bool = False):
            calls["faiss_init"] = local_files_only

        def run(self):
            calls["faiss_run"] = True
            return True

    monkeypatch.setattr(unified_runtime_sync.cfg, "VEDA_UNIFIED_RETRIEVAL_SYNC_ON_SAVE", True)
    monkeypatch.setattr(unified_runtime_sync.cfg, "VEDA_UNIFIED_FAISS_SYNC_ON_SAVE", False)
    monkeypatch.setattr(unified_corpus_builder, "UnifiedCorpusBuilder", FakeCorpusBuilder)
    monkeypatch.setattr(unified_bm25_indexer, "UnifiedBM25Indexer", FakeBM25Indexer)
    monkeypatch.setattr(unified_faiss_indexer, "UnifiedFAISSIndexer", FakeFAISSIndexer)

    result = refresh_unified_retrieval_assets(reason="knowledge_approved", source_doc_id="doc-3")

    assert calls == {
        "corpus": True,
        "bm25": True,
    }
    assert result["ok"] is True
    assert result["mode"] == "bm25_only"
    assert result["bm25_ready"] is True
    assert result["faiss_ready"] is False
    assert result["faiss_skipped"] is True
    assert result["total_records"] == 3
