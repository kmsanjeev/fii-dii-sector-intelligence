"""
FAISS Indexer -- Phase 13C
Builds dense vector index over knowledge documents for semantic retrieval.

Uses sentence-transformers to encode documents, FAISS for ANN search.
Model: all-MiniLM-L6-v2 (22MB, fast, good financial text quality)

6 domain-specific FAISS indexes for precision retrieval:
  MARKET, SECTOR, STOCK, DEAL, CORPORATE, ALL (cross-domain)

Output: data/intelligence/rag_knowledge/faiss/
        faiss_{domain}.index    -- FAISS IVF index
        faiss_{domain}_ids.json -- doc_id mapping
"""

import json
import shutil
import os
from pathlib import Path
import numpy as np

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

RAG_DIR = cfg.INTELLIGENCE_DIR / "rag_knowledge"
DOCS_PATH = RAG_DIR / "documents.jsonl"
FAISS_DIR = RAG_DIR / "faiss"

EMBED_MODEL = "all-MiniLM-L6-v2"
DOMAINS = ["MARKET", "SECTOR", "STOCK", "DEAL", "CORPORATE"]
BATCH_SIZE = 64


class FAISSIndexer:
    """
    Encodes documents with sentence-transformers and builds per-domain FAISS indexes.
    """

    def run(self) -> bool:
        import faiss
        from sentence_transformers import SentenceTransformer

        logger.info("[FAISSIndexer] Loading embedding model...")
        model = SentenceTransformer(EMBED_MODEL)
        FAISS_DIR.mkdir(parents=True, exist_ok=True)

        if not DOCS_PATH.exists():
            raise FileNotFoundError(f"Run document_builder.py first: {DOCS_PATH}")

        docs = self._load_docs()
        if not docs:
            logger.error("[FAISSIndexer] No documents to index")
            return False

        logger.info(f"[FAISSIndexer] Encoding {len(docs)} documents...")
        texts = [d["text"] for d in docs]

        # Encode in batches
        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,  # cosine similarity via dot product
        )
        embeddings = embeddings.astype(np.float32)
        dim = embeddings.shape[1]

        # Build cross-domain ALL index first
        self._build_index("ALL", docs, embeddings, list(range(len(docs))), dim, faiss)

        # Per-domain indexes
        for domain in DOMAINS:
            idx_list = [i for i, d in enumerate(docs) if d["domain"] == domain]
            if not idx_list:
                logger.info(f"[FAISSIndexer] No docs for domain {domain} -- skipping")
                continue
            domain_emb = embeddings[idx_list]
            domain_docs = [docs[i] for i in idx_list]
            self._build_index(domain, domain_docs, domain_emb, idx_list, dim, faiss)

        logger.info(f"[FAISSIndexer] All indexes built in {FAISS_DIR}")
        return True

    def _build_index(self, name: str, docs: list[dict], embeddings: np.ndarray,
                     global_idx: list[int], dim: int, faiss):
        n = len(docs)
        # Use flat index for small collections, IVF only when sufficiently large
        # IVF needs at least nlist*39 training points to avoid FAISS warnings
        nlist = max(4, min(32, n // 40))
        use_ivf = n >= nlist * 40
        if not use_ivf:
            index = faiss.IndexFlatIP(dim)
        else:
            quantizer = faiss.IndexFlatIP(dim)
            index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
            index.train(embeddings)

        index.add(embeddings)

        index_path = FAISS_DIR / f"faiss_{name}.index"
        ids_path   = FAISS_DIR / f"faiss_{name}_ids.json"

        tmp_idx = index_path.with_suffix(".tmp.index")
        faiss.write_index(index, str(tmp_idx))
        shutil.move(str(tmp_idx), str(index_path))

        id_map = {i: {"doc_id": d["doc_id"], "domain": d["domain"], "text": d["text"]}
                  for i, d in enumerate(docs)}
        tmp_ids = ids_path.with_suffix(".tmp.json")
        with open(tmp_ids, "w", encoding="utf-8") as f:
            json.dump(id_map, f, ensure_ascii=False)
        shutil.move(str(tmp_ids), str(ids_path))

        logger.info(f"[FAISSIndexer] {name}: {n} vectors, dim={dim} -> {index_path.name}")

    def _load_docs(self) -> list[dict]:
        docs = []
        with open(DOCS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))
        return docs

    @staticmethod
    def query(query_text: str, domain: str = "ALL", top_k: int = 10) -> list[dict]:
        """
        Run a semantic FAISS query against the saved index.
        Returns list of {doc_id, domain, text, faiss_score, rank}.
        """
        import faiss
        from sentence_transformers import SentenceTransformer

        index_path = FAISS_DIR / f"faiss_{domain}.index"
        ids_path   = FAISS_DIR / f"faiss_{domain}_ids.json"

        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not built for domain {domain}: {index_path}")

        model = SentenceTransformer(EMBED_MODEL)
        q_emb = model.encode([query_text], normalize_embeddings=True).astype(np.float32)

        index = faiss.read_index(str(index_path))
        scores, indices = index.search(q_emb, top_k)

        with open(ids_path, encoding="utf-8") as f:
            id_map = json.load(f)

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < 0:
                continue
            entry = id_map.get(str(idx), {})
            results.append({
                "doc_id": entry.get("doc_id", f"idx_{idx}"),
                "domain": entry.get("domain", domain),
                "text": entry.get("text", ""),
                "faiss_score": float(score),
                "rank": rank + 1,
            })
        return results


if __name__ == "__main__":
    indexer = FAISSIndexer()
    indexer.run()

    print("\nFAISS query: 'which sectors are seeing FII accumulation'")
    results = FAISSIndexer.query("which sectors are seeing FII accumulation", domain="SECTOR", top_k=5)
    for r in results:
        print(f"  [{r['rank']}] {r['doc_id']} (score={r['faiss_score']:.3f}): {r['text'][:120]}...")

    print("\nFAISS query: 'top emerging stocks with high bull run score'")
    results = FAISSIndexer.query("top emerging stocks with high bull run score", domain="STOCK", top_k=5)
    for r in results:
        print(f"  [{r['rank']}] {r['doc_id']} (score={r['faiss_score']:.3f}): {r['text'][:120]}...")
