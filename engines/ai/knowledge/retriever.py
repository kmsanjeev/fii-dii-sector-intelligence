"""
Hybrid Retriever -- Phase 13D
Combines BM25 (sparse) + FAISS (dense) results via Reciprocal Rank Fusion (RRF).

RRF score = sum(1 / (k + rank_i)) for each retrieval system.
Default k=60 from the original RRF paper (Cormack et al., 2009).

Domain routing:
  - "sector" queries -> SECTOR index
  - "stock"/"symbol" queries -> STOCK index
  - "deal"/"trade"/"bulk" queries -> DEAL index
  - "corporate"/"buyback"/"dividend" queries -> CORPORATE index
  - "market"/"regime"/"fii"/"dii" queries -> MARKET index
  - fallback -> ALL index
"""

from __future__ import annotations
import re
from typing import Optional

from engines.common.logger import get_logger

logger = get_logger(__name__)

RRF_K = 60
DEFAULT_TOP_K = 10

DOMAIN_KEYWORDS = {
    "SECTOR": ["sector", "rotation", "industry", "leading", "lagging", "early_rotation"],
    "STOCK": ["stock", "symbol", "share", "equity", "scrip", "emerging", "watchlist", "candidate"],
    "DEAL": ["deal", "bulk", "block", "trade", "transaction", "acquisition", "institutional deal"],
    "CORPORATE": ["corporate", "buyback", "dividend", "bonus", "split", "confidence", "promoter"],
    "MARKET": ["market", "regime", "fii", "dii", "accumulation", "distribution", "participant"],
}


class HybridRetriever:
    """
    Retrieve documents using BM25 + FAISS hybrid with RRF re-ranking.
    """

    def __init__(self, top_k: int = DEFAULT_TOP_K):
        self.top_k = top_k

    def retrieve(self, query: str, domain: Optional[str] = None) -> list[dict]:
        """
        Main retrieval method.
        Returns list of {doc_id, domain, text, rrf_score, rank, bm25_rank, faiss_rank}.
        """
        if domain is None:
            domain = _detect_domain(query)

        logger.debug(f"[Retriever] Query: '{query}' | Domain: {domain}")

        # Fetch from both systems
        bm25_results = _bm25_query(query, top_k=self.top_k * 2)
        faiss_results = _faiss_query(query, domain=domain, top_k=self.top_k * 2)

        # RRF fusion
        fused = _rrf_fuse(bm25_results, faiss_results, k=RRF_K)
        return fused[:self.top_k]

    def retrieve_by_domain(self, query: str, domain: str, top_k: int = 5) -> list[dict]:
        """Force a specific domain, useful for structured agent queries."""
        faiss_results = _faiss_query(query, domain=domain, top_k=top_k * 2)
        bm25_results = _bm25_query(query, top_k=top_k * 2)

        # Filter BM25 to same domain
        bm25_results = [r for r in bm25_results if r.get("domain") == domain]

        fused = _rrf_fuse(bm25_results, faiss_results, k=RRF_K)
        return fused[:top_k]


# ------------------------------------------------------------------
# RRF
# ------------------------------------------------------------------

def _rrf_fuse(list_a: list[dict], list_b: list[dict], k: int = RRF_K) -> list[dict]:
    """
    Reciprocal Rank Fusion of two ranked lists.
    Uses doc_id as the merge key.
    """
    scores: dict[str, dict] = {}

    for rank, doc in enumerate(list_a, start=1):
        did = doc["doc_id"]
        if did not in scores:
            scores[did] = {"doc": doc, "rrf": 0.0, "bm25_rank": None, "faiss_rank": None}
        scores[did]["rrf"] += 1.0 / (k + rank)
        scores[did]["bm25_rank"] = rank

    for rank, doc in enumerate(list_b, start=1):
        did = doc["doc_id"]
        if did not in scores:
            scores[did] = {"doc": doc, "rrf": 0.0, "bm25_rank": None, "faiss_rank": None}
        scores[did]["rrf"] += 1.0 / (k + rank)
        scores[did]["faiss_rank"] = rank

    ordered = sorted(scores.values(), key=lambda x: x["rrf"], reverse=True)

    results = []
    for rank, entry in enumerate(ordered, start=1):
        doc = entry["doc"].copy()
        doc["rrf_score"] = round(entry["rrf"], 6)
        doc["bm25_rank"] = entry["bm25_rank"]
        doc["faiss_rank"] = entry["faiss_rank"]
        doc["rank"] = rank
        results.append(doc)

    return results


# ------------------------------------------------------------------
# Domain detection
# ------------------------------------------------------------------

def _detect_domain(query: str) -> str:
    q = query.lower()
    scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                scores[domain] += 1
    best = max(scores, key=lambda d: scores[d])
    return best if scores[best] > 0 else "ALL"


# ------------------------------------------------------------------
# Internal query wrappers (lazy-import to keep startup fast)
# ------------------------------------------------------------------

def _bm25_query(query: str, top_k: int) -> list[dict]:
    try:
        from engines.ai.knowledge.bm25_indexer import BM25Indexer
        return BM25Indexer.query(query, top_k=top_k)
    except Exception as e:
        logger.warning(f"[Retriever] BM25 query failed: {e}")
        return []


def _faiss_query(query: str, domain: str, top_k: int) -> list[dict]:
    try:
        from engines.ai.knowledge.faiss_indexer import FAISSIndexer
        return FAISSIndexer.query(query, domain=domain, top_k=top_k)
    except Exception as e:
        logger.warning(f"[Retriever] FAISS query failed (domain={domain}): {e}")
        return []


if __name__ == "__main__":
    retriever = HybridRetriever(top_k=5)

    queries = [
        "Which sectors are seeing FII accumulation today?",
        "Show me STRONG_CANDIDATE stocks with high bull run score",
        "What is the current market regime?",
        "Large institutional block deals today",
        "Corporate buybacks with high confidence",
    ]

    for q in queries:
        print(f"\nQuery: {q}")
        results = retriever.retrieve(q)
        for r in results[:3]:
            print(f"  [{r['rank']}] {r['doc_id']} (rrf={r['rrf_score']:.5f}, "
                  f"bm25={r['bm25_rank']}, faiss={r['faiss_rank']}): "
                  f"{r['text'][:100]}...")
