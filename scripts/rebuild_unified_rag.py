"""Rebuild deterministic unified corpus snapshots and the derived BM25 cache."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.ai.knowledge.unified_bm25_indexer import UnifiedBM25Indexer
from engines.ai.knowledge.unified_corpus_builder import UnifiedCorpusBuilder


def main() -> int:
    summary = UnifiedCorpusBuilder().run()
    if not UnifiedBM25Indexer().run():
        return 1
    print(
        "Unified RAG rebuild complete: "
        f"records={summary['document_count']} "
        f"corpus_hash={summary['corpus_content_hash']} "
        f"written={summary['written']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
