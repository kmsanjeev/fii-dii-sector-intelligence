"""
Unified BM25 Indexer -- Phase 2A
Builds a keyword index over the unified durable Veda corpus.

Input:  data/intelligence/rag_knowledge/veda_unified_documents.jsonl
Output: data/intelligence/rag_knowledge/veda_unified_bm25_index.pkl
"""

from __future__ import annotations

import json
import pickle
import re
import shutil
from typing import Any

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

DOCS_PATH = cfg.VEDA_UNIFIED_KNOWLEDGE_DOCS
INDEX_OUT = cfg.VEDA_UNIFIED_BM25_INDEX


class UnifiedBM25Indexer:
    def run(self) -> bool:
        from rank_bm25 import BM25Okapi

        logger.info("[UnifiedBM25] Building unified BM25 index")

        if not DOCS_PATH.exists():
            raise FileNotFoundError(f"Run unified_corpus_builder.py first: {DOCS_PATH}")

        docs = self._load_docs()
        if not docs:
            logger.error("[UnifiedBM25] No unified documents to index")
            return False

        corpus = [_tokenize(_search_text(doc)) for doc in docs]
        payload = {
            "bm25": BM25Okapi(corpus),
            "docs": docs,
            "n_docs": len(docs),
        }

        tmp = INDEX_OUT.with_suffix(".tmp.pkl")
        with open(tmp, "wb") as handle:
            pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
        shutil.move(str(tmp), str(INDEX_OUT))

        logger.info("[UnifiedBM25] Indexed %s unified documents -> %s", len(docs), INDEX_OUT)
        return True

    def _load_docs(self) -> list[dict[str, Any]]:
        docs = []
        with open(DOCS_PATH, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))
        return docs

    @staticmethod
    def query(query_text: str, top_k: int = 10) -> list[dict[str, Any]]:
        if not INDEX_OUT.exists():
            raise FileNotFoundError(f"Unified BM25 index not built: {INDEX_OUT}")

        with open(INDEX_OUT, "rb") as handle:
            payload = pickle.load(handle)

        bm25 = payload["bm25"]
        docs = payload["docs"]
        tokens = _tokenize(query_text)
        scores = bm25.get_scores(tokens)

        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for rank, idx in enumerate(top_idx, start=1):
            doc = dict(docs[idx])
            doc["bm25_score"] = float(scores[idx])
            doc["rank"] = rank
            results.append(doc)
        return results


def _search_text(doc: dict[str, Any]) -> str:
    entity_keys = doc.get("entity_keys", {}) or {}
    provenance = doc.get("provenance", {}) or {}
    tags = " ".join(str(tag) for tag in doc.get("tags", []) or [])
    parts = [
        doc.get("source_type", ""),
        doc.get("evidence_kind", ""),
        doc.get("domain", ""),
        doc.get("entity", ""),
        doc.get("summary", ""),
        doc.get("text", ""),
        doc.get("model_name", ""),
        doc.get("model_version", ""),
        doc.get("score_meaning", ""),
        doc.get("reliability_note", ""),
        tags,
        entity_keys.get("symbol", ""),
        entity_keys.get("sector", ""),
        entity_keys.get("topic", ""),
        entity_keys.get("repo_label", ""),
        entity_keys.get("attachment_name", ""),
        provenance.get("source_label", ""),
        provenance.get("repo_label", ""),
        provenance.get("attachment_name", ""),
        provenance.get("license_name", ""),
    ]
    return " ".join(str(part or "") for part in parts if str(part or "").strip())


def _tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    return re.findall(r"[a-z0-9_]+", text)
