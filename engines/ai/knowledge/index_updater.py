"""
Index Updater -- Phase 13E
Daily incremental RAG index rebuild.

Runs after market close (post 16:30 IST) once intelligence CSVs are refreshed.
Rebuilds documents.jsonl -> BM25 index -> FAISS indexes in sequence.

Usage:
    py -3.11 -m engines.ai.knowledge.index_updater
    (or scheduled via alerts/alert_scheduler.py)
"""

from pathlib import Path
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

RAG_DIR = cfg.INTELLIGENCE_DIR / "rag_knowledge"


def run_index_update(force: bool = False) -> bool:
    """
    Full RAG index rebuild pipeline:
      1. DocumentBuilder  -> documents.jsonl
      2. BM25Indexer      -> bm25_index.pkl
      3. FAISSIndexer     -> faiss/*.index
    """
    logger.info("[IndexUpdater] Starting RAG index rebuild")

    # Step 1: Documents
    from engines.ai.knowledge.document_builder import DocumentBuilder
    n_docs = DocumentBuilder().run()
    if n_docs == 0:
        logger.error("[IndexUpdater] Document builder produced 0 docs -- aborting")
        return False
    logger.info(f"[IndexUpdater] Documents: {n_docs}")

    # Step 2: BM25
    from engines.ai.knowledge.bm25_indexer import BM25Indexer
    if not BM25Indexer().run():
        logger.error("[IndexUpdater] BM25 indexing failed")
        return False
    logger.info("[IndexUpdater] BM25 index ready")

    # Step 3: FAISS
    from engines.ai.knowledge.faiss_indexer import FAISSIndexer
    if not FAISSIndexer().run():
        logger.error("[IndexUpdater] FAISS indexing failed")
        return False
    logger.info("[IndexUpdater] FAISS indexes ready")

    logger.info("[IndexUpdater] RAG index rebuild complete")
    return True


if __name__ == "__main__":
    success = run_index_update()
    if success:
        print("RAG index update complete")
        # Quick smoke test
        from engines.ai.knowledge.retriever import HybridRetriever
        r = HybridRetriever(top_k=3)
        results = r.retrieve("What is the market regime today?")
        print(f"Retrieval smoke test: {len(results)} results")
        for res in results:
            print(f"  [{res['rank']}] {res['doc_id']}: {res['text'][:100]}...")
    else:
        import sys
        sys.exit(1)
