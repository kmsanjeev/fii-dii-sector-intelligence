"""
BM25 Indexer -- Phase 13B
Builds keyword-based BM25 index over knowledge documents for sparse retrieval.

BM25 excels at exact-keyword queries: "ADANIENSOL", "EARLY_ROTATION", "FII buying".
Used in hybrid retrieval via Reciprocal Rank Fusion (RRF) with dense FAISS index.

Output: data/intelligence/rag_knowledge/bm25_index.pkl
"""

import pickle
import shutil
from pathlib import Path
import json
import re

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

RAG_DIR = cfg.INTELLIGENCE_DIR / "rag_knowledge"
DOCS_PATH = RAG_DIR / "documents.jsonl"
INDEX_OUT = RAG_DIR / "bm25_index.pkl"


class BM25Indexer:
    """
    Builds and saves a BM25Okapi index from documents.jsonl.
    Each document's text is tokenized and indexed.
    """

    def run(self) -> bool:
        from rank_bm25 import BM25Okapi

        logger.info("[BM25Indexer] Building BM25 index")

        if not DOCS_PATH.exists():
            raise FileNotFoundError(f"Run document_builder.py first: {DOCS_PATH}")

        docs = self._load_docs()
        if not docs:
            logger.error("[BM25Indexer] No documents to index")
            return False

        corpus = [_tokenize(d["text"]) for d in docs]
        doc_ids = [d["doc_id"] for d in docs]
        domains = [d["domain"] for d in docs]

        bm25 = BM25Okapi(corpus)

        payload = {
            "bm25": bm25,
            "doc_ids": doc_ids,
            "domains": domains,
            "texts": [d["text"] for d in docs],
            "n_docs": len(docs),
        }

        tmp = INDEX_OUT.with_suffix(".tmp.pkl")
        with open(tmp, "wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
        shutil.move(str(tmp), str(INDEX_OUT))

        logger.info(f"[BM25Indexer] Indexed {len(docs)} documents -> {INDEX_OUT}")
        return True

    def _load_docs(self) -> list[dict]:
        docs = []
        with open(DOCS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))
        return docs

    @staticmethod
    def query(query_text: str, top_k: int = 10) -> list[dict]:
        """
        Run a BM25 query against the saved index.
        Returns list of {doc_id, domain, text, bm25_score, rank}.
        """
        if not INDEX_OUT.exists():
            raise FileNotFoundError(f"BM25 index not built: {INDEX_OUT}")

        with open(INDEX_OUT, "rb") as f:
            payload = pickle.load(f)

        bm25 = payload["bm25"]
        tokens = _tokenize(query_text)
        scores = bm25.get_scores(tokens)

        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for rank, idx in enumerate(top_idx):
            results.append({
                "doc_id": payload["doc_ids"][idx],
                "domain": payload["domains"][idx],
                "text": payload["texts"][idx],
                "bm25_score": float(scores[idx]),
                "rank": rank + 1,
            })
        return results


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    # Split on non-alphanumeric but keep underscores within tokens (e.g. EARLY_ROTATION)
    tokens = re.findall(r"[a-z0-9_]+", text)
    return tokens


if __name__ == "__main__":
    indexer = BM25Indexer()
    indexer.run()

    # Quick test
    results = BM25Indexer.query("FII buying EARLY_ROTATION sector", top_k=5)
    print("BM25 query: 'FII buying EARLY_ROTATION sector'")
    for r in results:
        print(f"  [{r['rank']}] {r['doc_id']} (score={r['bm25_score']:.3f}): {r['text'][:100]}...")
