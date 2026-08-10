from __future__ import annotations

from typing import Any

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)


def refresh_unified_retrieval_assets(*, reason: str, source_doc_id: str | None = None) -> dict[str, Any]:
    """
    Rebuild unified retrieval assets after approved memory or capability changes.

    This keeps Veda's primary unified retrieval path in sync with newly approved
    durable knowledge without waiting for the next full scheduled index rebuild.
    """
    if not cfg.VEDA_UNIFIED_RETRIEVAL_SYNC_ON_SAVE:
        return {
            "ok": False,
            "skipped": True,
            "reason": "sync_disabled",
            "source_doc_id": source_doc_id,
        }

    try:
        from engines.ai.knowledge.unified_corpus_builder import UnifiedCorpusBuilder
        from engines.ai.knowledge.unified_bm25_indexer import UnifiedBM25Indexer
        from engines.ai.knowledge.unified_faiss_indexer import UnifiedFAISSIndexer

        summary = UnifiedCorpusBuilder().run()
        bm25_ready = bool(UnifiedBM25Indexer().run())
        faiss_ready = False
        faiss_skipped = not cfg.VEDA_UNIFIED_FAISS_SYNC_ON_SAVE
        faiss_error: str | None = None
        if not faiss_skipped:
            try:
                faiss_ready = bool(
                    UnifiedFAISSIndexer(local_files_only=cfg.VEDA_UNIFIED_FAISS_LOCAL_ONLY_ON_SAVE).run()
                )
            except Exception as exc:
                faiss_error = str(exc)
                logger.warning(
                    "[UnifiedRuntimeSync] Unified FAISS refresh skipped (reason=%s, source_doc_id=%s): %s",
                    reason,
                    source_doc_id,
                    exc,
                )
        result = {
            "ok": bool(bm25_ready),
            "skipped": False,
            "reason": reason,
            "source_doc_id": source_doc_id,
            "total_records": int(summary.get("total_records", 0)),
            "bm25_ready": bm25_ready,
            "faiss_ready": faiss_ready,
            "faiss_skipped": faiss_skipped,
            "mode": "full" if faiss_ready else "bm25_only",
        }
        if faiss_error:
            result["faiss_error"] = faiss_error
        logger.info(
            "[UnifiedRuntimeSync] reason=%s source_doc_id=%s total_records=%s bm25=%s faiss=%s mode=%s",
            reason,
            source_doc_id,
            result["total_records"],
            bm25_ready,
            faiss_ready,
            result["mode"],
        )
        return result
    except Exception as exc:
        logger.warning(
            "[UnifiedRuntimeSync] Failed to refresh unified retrieval assets (reason=%s, source_doc_id=%s): %s",
            reason,
            source_doc_id,
            exc,
        )
        return {
            "ok": False,
            "skipped": False,
            "reason": reason,
            "source_doc_id": source_doc_id,
            "error": str(exc),
        }
