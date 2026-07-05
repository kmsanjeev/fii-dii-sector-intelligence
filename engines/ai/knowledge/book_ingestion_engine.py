"""
Book Ingestion Engine - Phase AF-1
Extracts text from AstroFinance PDF books, chunks it, and appends
ASTRO-domain documents to the RAG knowledge base.

Books processed:
  - A Trader's Guide to Financial Astrology (Pesavento & Smoleny)
  - Financial Astrology Almanac 2023
  - Planetary Effects to Financial Market
  - Stock Market Astrology & Astrological Theory (Banerjee)
  - Meridian, B. -- Johndro's Astrology
  - Brown: Stellar Theology and Masonic Astronomy

Output: appends to data/intelligence/rag_knowledge/documents.jsonl
        then triggers ASTRO FAISS index rebuild
"""

from __future__ import annotations
import hashlib
import json
import re
import shutil
from pathlib import Path

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

RAG_DIR = cfg.INTELLIGENCE_DIR / "rag_knowledge"
DOCS_PATH = RAG_DIR / "documents.jsonl"

CHUNK_SIZE = 600    # target chars per chunk
CHUNK_OVERLAP = 80  # overlap between consecutive chunks

BOOK_PATHS = [
    r"c:\Users\hp\Desktop\AstroFinance Book\Astro\A_traders_guide_to_financial_astrology.pdf",
    r"c:\Users\hp\Desktop\AstroFinance Book\Astro\financial_astrology_almanac_2023_trading_investing_using_the_planets.pdf",
    r"c:\Users\hp\Desktop\AstroFinance Book\Astro\Planetary effects to Financial Market.pdf",
    r"c:\Users\hp\Desktop\AstroFinance Book\Astro\Stock_Market_Astrology_&_Astrological.pdf",
    r"c:\Users\hp\Desktop\AstroFinance Book\Astro\Brown_Stellar_Theology_and_Masonic_Astronomy_by_Robert_Hewitt_B_.pdf",
    r"c:\Users\hp\Desktop\AstroFinance Book\Astro\Meridian, B.(2001)_Johndro's Astrology [8 p.].pdf",
]

BOOK_META = {
    "A_traders_guide": {
        "title": "A Trader's Guide to Financial Astrology",
        "authors": "Pesavento & Smoleny",
        "year": 2015,
        "focus": "planetary cycles, aspects, Bradley Barometer, lunar cycles",
    },
    "financial_astrology_almanac": {
        "title": "Financial Astrology Almanac 2023",
        "authors": "Multiple",
        "year": 2023,
        "focus": "Gann Master Cycle, McWhirter 18.6yr cycle, Venus/Mercury retrograde, declination",
    },
    "Planetary_effects": {
        "title": "Planetary Effects to Financial Market",
        "authors": "Various",
        "year": 2020,
        "focus": "eclipse signals, Mercury-Sun connection, aspect timing for market drops",
    },
    "Stock_Market_Astrology": {
        "title": "Stock Market Astrology & Astrological Theory of Business Cycles",
        "authors": "Indrodeep Banerjee",
        "year": 2009,
        "focus": "Indian/Vedic system, NSE sector-planet mapping, Nakshatras, Hora trading",
    },
    "Brown_Stellar": {
        "title": "Stellar Theology and Masonic Astronomy",
        "authors": "Robert Hewitt Brown",
        "year": 1882,
        "focus": "stellar symbolism, ancient astronomy, zodiac history",
    },
    "Meridian_Johndro": {
        "title": "Johndro's Astrology",
        "authors": "Meridian B.",
        "year": 2001,
        "focus": "geodetic astrology, locality charts, financial locality mapping",
    },
}


class BookIngestionEngine:
    """
    Reads all AstroFinance books, chunks the text, and adds ASTRO-domain
    documents to the RAG knowledge base, then rebuilds the ASTRO FAISS index.
    """

    def run(self) -> int:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber not installed. Run: py -3.11 -m pip install pdfplumber")

        RAG_DIR.mkdir(parents=True, exist_ok=True)
        existing_ids = self._load_existing_ids()
        new_docs: list[dict] = []

        for pdf_path_str in BOOK_PATHS:
            pdf_path = Path(pdf_path_str)
            if not pdf_path.exists():
                logger.warning(f"[BookIngestion] Book not found: {pdf_path.name}")
                continue

            meta_key = self._find_meta_key(pdf_path.name)
            meta = BOOK_META.get(meta_key, {"title": pdf_path.stem, "authors": "Unknown", "year": 0, "focus": ""})
            logger.info(f"[BookIngestion] Processing: {meta['title']}")

            text = self._extract_text(pdf_path, pdfplumber)
            if not text.strip():
                logger.warning(f"[BookIngestion] No text extracted from {pdf_path.name}")
                continue

            chunks = self._chunk_text(text)
            logger.info(f"[BookIngestion] {pdf_path.name}: {len(chunks)} chunks from {len(text):,} chars")

            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 80:
                    continue
                doc_id = self._make_id(pdf_path.name, i)
                if doc_id in existing_ids:
                    continue

                formatted_text = (
                    f"[AstroFinance Knowledge] {meta['title']} ({meta['authors']}, {meta['year']}). "
                    f"Topic: {meta['focus']}. "
                    f"{chunk.strip()}"
                )
                new_docs.append({
                    "doc_id":   doc_id,
                    "domain":   "ASTRO",
                    "entity":   meta_key,
                    "text":     formatted_text,
                    "metadata": {
                        "source": pdf_path.name,
                        "title":  meta["title"],
                        "chunk":  i,
                    },
                })

        if not new_docs:
            logger.info("[BookIngestion] No new documents to add")
            return 0

        self._append_docs(new_docs)
        logger.info(f"[BookIngestion] Added {len(new_docs)} ASTRO documents to knowledge base")
        return len(new_docs)

    def _extract_text(self, pdf_path: Path, pdfplumber) -> str:
        parts = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Normalize encoding
                        text = text.encode("ascii", "replace").decode("ascii")
                        # Remove repeated short lines (headers/footers/page numbers)
                        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 3]
                        parts.append(" ".join(lines))
        except Exception as e:
            logger.error(f"[BookIngestion] PDF extraction failed for {pdf_path.name}: {e}")
        return " ".join(parts)

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks at sentence boundaries where possible.
        """
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE

            if end >= len(text):
                chunks.append(text[start:])
                break

            # Try to break at a sentence boundary
            boundary = -1
            for sep in (". ", "? ", "! ", "; "):
                idx = text.rfind(sep, start + CHUNK_SIZE // 2, end)
                if idx > boundary:
                    boundary = idx + len(sep)

            if boundary > start:
                chunks.append(text[start:boundary])
                start = boundary - CHUNK_OVERLAP
            else:
                chunks.append(text[start:end])
                start = end - CHUNK_OVERLAP

        return chunks

    def _make_id(self, filename: str, chunk_idx: int) -> str:
        h = hashlib.md5(f"{filename}_{chunk_idx}".encode()).hexdigest()[:8]
        return f"astro_{h}"

    def _find_meta_key(self, filename: str) -> str:
        filename_lower = filename.lower()
        for key in BOOK_META:
            if key.lower().replace("_", "") in filename_lower.replace("_", "").replace(" ", ""):
                return key
        # Partial matching
        if "trader" in filename_lower or "pesavento" in filename_lower:
            return "A_traders_guide"
        if "almanac" in filename_lower or "2023" in filename_lower:
            return "financial_astrology_almanac"
        if "planetary" in filename_lower:
            return "Planetary_effects"
        if "stock" in filename_lower and "astrology" in filename_lower:
            return "Stock_Market_Astrology"
        if "brown" in filename_lower or "stellar" in filename_lower:
            return "Brown_Stellar"
        if "meridian" in filename_lower or "johndro" in filename_lower:
            return "Meridian_Johndro"
        return "Unknown"

    def _load_existing_ids(self) -> set[str]:
        if not DOCS_PATH.exists():
            return set()
        ids = set()
        with open(DOCS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        ids.add(json.loads(line).get("doc_id", ""))
                    except Exception:
                        pass
        return ids

    def _append_docs(self, docs: list[dict]):
        tmp = DOCS_PATH.with_suffix(".tmp.jsonl")
        # Copy existing + append new
        if DOCS_PATH.exists():
            shutil.copy(str(DOCS_PATH), str(tmp))
        with open(tmp, "a", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        shutil.move(str(tmp), str(DOCS_PATH))


if __name__ == "__main__":
    engine = BookIngestionEngine()
    n = engine.run()
    print(f"Ingested {n} new ASTRO documents")

    if n > 0:
        print("Rebuilding FAISS indexes to include ASTRO domain...")
        from engines.ai.knowledge.faiss_indexer import FAISSIndexer
        FAISSIndexer().run()
        print("FAISS rebuild complete.")
