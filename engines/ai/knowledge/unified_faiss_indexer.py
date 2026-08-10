"""
Unified FAISS Indexer -- Phase 2B
Builds semantic indexes over the unified durable Veda corpus.

Input:  data/intelligence/rag_knowledge/veda_unified_documents.jsonl
Output: data/intelligence/rag_knowledge/veda_unified_faiss/
"""

from __future__ import annotations

import json
import shutil
from typing import Any

import numpy as np

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

DOCS_PATH = cfg.VEDA_UNIFIED_KNOWLEDGE_DOCS
FAISS_DIR = cfg.VEDA_UNIFIED_FAISS_DIR
EMBED_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


class UnifiedFAISSIndexer:
    def __init__(self, *, local_files_only: bool = False):
        self.local_files_only = bool(local_files_only)

    def run(self) -> bool:
        import faiss

        logger.info("[UnifiedFAISS] Loading embedding model...")
        model = _load_model(local_files_only=self.local_files_only)
        FAISS_DIR.mkdir(parents=True, exist_ok=True)

        if not DOCS_PATH.exists():
            raise FileNotFoundError(f"Run unified_corpus_builder.py first: {DOCS_PATH}")

        docs = self._load_docs()
        if not docs:
            logger.error("[UnifiedFAISS] No unified documents to index")
            return False

        logger.info("[UnifiedFAISS] Encoding %s unified documents...", len(docs))
        texts = [_embed_text(doc) for doc in docs]
        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).astype(np.float32)
        dim = embeddings.shape[1]

        self._build_index("ALL", docs, embeddings, dim, faiss)

        domains = sorted({str(doc.get("domain") or "UNKNOWN") for doc in docs})
        for domain in domains:
            idx_list = [idx for idx, doc in enumerate(docs) if str(doc.get("domain") or "UNKNOWN") == domain]
            if not idx_list:
                continue
            domain_docs = [docs[idx] for idx in idx_list]
            domain_embeddings = embeddings[idx_list]
            self._build_index(domain, domain_docs, domain_embeddings, dim, faiss)

        logger.info("[UnifiedFAISS] All unified indexes built in %s", FAISS_DIR)
        return True

    def _build_index(self, name: str, docs: list[dict[str, Any]], embeddings: np.ndarray, dim: int, faiss) -> None:
        n = len(docs)
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
        ids_path = FAISS_DIR / f"faiss_{name}_ids.json"

        tmp_idx = index_path.with_suffix(".tmp.index")
        faiss.write_index(index, str(tmp_idx))
        shutil.move(str(tmp_idx), str(index_path))

        id_map = {i: docs[i] for i in range(len(docs))}
        tmp_ids = ids_path.with_suffix(".tmp.json")
        with open(tmp_ids, "w", encoding="utf-8") as handle:
            json.dump(id_map, handle, ensure_ascii=False)
        shutil.move(str(tmp_ids), str(ids_path))

        logger.info("[UnifiedFAISS] %s: %s vectors -> %s", name, n, index_path.name)

    def _load_docs(self) -> list[dict[str, Any]]:
        docs = []
        with open(DOCS_PATH, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))
        return docs

    @staticmethod
    def query(query_text: str, domain: str = "ALL", top_k: int = 10) -> list[dict[str, Any]]:
        import faiss

        index_path = FAISS_DIR / f"faiss_{domain}.index"
        ids_path = FAISS_DIR / f"faiss_{domain}_ids.json"

        if not index_path.exists():
            raise FileNotFoundError(f"Unified FAISS index not built for domain {domain}: {index_path}")

        model = _load_model()
        q_emb = model.encode([query_text], normalize_embeddings=True).astype(np.float32)

        index = faiss.read_index(str(index_path))
        scores, indices = index.search(q_emb, top_k)

        with open(ids_path, encoding="utf-8") as handle:
            id_map = json.load(handle)

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
            if idx < 0:
                continue
            doc = dict(id_map.get(str(idx), {}))
            doc["faiss_score"] = float(score)
            doc["rank"] = rank
            results.append(doc)
        return results


def _embed_text(doc: dict[str, Any]) -> str:
    tags = ", ".join(str(tag) for tag in doc.get("tags", []) or [])
    return " ".join(
        part
        for part in [
            f"Source type: {doc.get('source_type', '')}.",
            f"Evidence kind: {doc.get('evidence_kind', '')}.",
            f"Domain: {doc.get('domain', '')}.",
            f"Entity: {doc.get('entity', '')}.",
            f"Model name: {doc.get('model_name', '')}.",
            f"Model version: {doc.get('model_version', '')}.",
            f"Score meaning: {doc.get('score_meaning', '')}.",
            f"Reliability note: {doc.get('reliability_note', '')}.",
            f"Summary: {doc.get('summary', '')}.",
            f"Tags: {tags}.",
            str(doc.get("text", "")).strip(),
        ]
        if str(part).strip()
    )


def _load_model(*, local_files_only: bool = False):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBED_MODEL, local_files_only=local_files_only)
