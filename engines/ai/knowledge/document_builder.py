"""
Document Builder -- Phase 13A
Converts intelligence CSVs into structured text documents for RAG indexing.

Each document = one logical unit of knowledge:
  - One document per sector (rotation signal, flow scores, top stocks)
  - One document per top-scoring stock (label, scores, sector, corporate data)
  - One market-regime document (participant summary, regime, date)
  - One document per corporate deal / catalyst
  - One document per participant snapshot

Output: data/intelligence/rag_knowledge/documents.jsonl
        data/intelligence/rag_knowledge/doc_metadata.csv
"""

import json
import shutil
from pathlib import Path
from typing import Optional
import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

RAG_DIR = cfg.INTELLIGENCE_DIR / "rag_knowledge"
DOCS_OUT = RAG_DIR / "documents.jsonl"
META_OUT = RAG_DIR / "doc_metadata.csv"

# Intelligence source paths
BULL_RUN   = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
SECTOR_ROT = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
PART_INTEL = cfg.INTELLIGENCE_DIR / "participant_intelligence.csv"
DEAL_SIG   = cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv"
CORP_CONF  = cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
ML_SCORES  = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"


def _latest_snapshot_date() -> str | None:
    if not PART_INTEL.exists():
        return None
    try:
        part = pd.read_csv(PART_INTEL, usecols=lambda c: c == "date")
    except Exception:
        return None
    if part.empty or "date" not in part.columns:
        return None
    values = [str(value).strip() for value in part["date"].tolist() if str(value).strip() and str(value).strip().lower() != "nan"]
    return sorted(values)[-1] if values else None


class DocumentBuilder:
    """
    Builds text documents from intelligence layer outputs.
    Each document has: doc_id, domain, entity, text, metadata.
    """

    def run(self) -> int:
        logger.info("[DocBuilder] Starting document construction")
        RAG_DIR.mkdir(parents=True, exist_ok=True)

        docs = []
        docs.extend(self._build_market_docs())
        docs.extend(self._build_sector_docs())
        docs.extend(self._build_stock_docs())
        docs.extend(self._build_deal_docs())
        docs.extend(self._build_corporate_docs())

        if not docs:
            logger.error("[DocBuilder] No documents built -- check intelligence CSVs")
            return 0

        self._save(docs)
        logger.info(f"[DocBuilder] Built {len(docs)} documents")
        return len(docs)

    # ------------------------------------------------------------------
    # Market regime document (1 per run)
    # ------------------------------------------------------------------

    def _build_market_docs(self) -> list[dict]:
        if not PART_INTEL.exists():
            logger.warning("[DocBuilder] participant_intelligence.csv missing")
            return []

        part = pd.read_csv(PART_INTEL)
        if part.empty:
            return []

        latest = part.sort_values("date").iloc[-1]
        date = str(latest.get("date", "unknown"))
        regime = str(latest.get("Market_Regime", "UNKNOWN"))
        fii_score = _fmt(latest.get("FII_flow_score"))
        dii_score = _fmt(latest.get("DII_flow_score"))
        smart_money = _fmt(latest.get("Smart_Money_Score"))

        text = (
            f"Market Intelligence Report as of {date}. "
            f"Current market regime is {regime}. "
            f"FII flow score is {fii_score} (positive = net buying, negative = net selling). "
            f"DII flow score is {dii_score}. "
            f"Smart money score is {smart_money}, which measures combined institutional conviction. "
            f"A regime of STRONG_ACCUMULATION or ACCUMULATION indicates institutional buying. "
            f"DISTRIBUTION or STRONG_DISTRIBUTION signals institutional selling or caution."
        )

        return [_doc("MARKET", "MARKET_REGIME", "market_regime", text, {"date": date, "regime": regime})]

    # ------------------------------------------------------------------
    # Sector documents
    # ------------------------------------------------------------------

    def _build_sector_docs(self) -> list[dict]:
        if not SECTOR_ROT.exists():
            logger.warning("[DocBuilder] sector_rotation_intelligence.csv missing")
            return []

        sectors = pd.read_csv(SECTOR_ROT)
        if sectors.empty:
            return []
        snapshot_date = _latest_snapshot_date()

        # Load bull run for top-stock-per-sector context
        stock_map: dict[str, list[str]] = {}
        if BULL_RUN.exists():
            br = pd.read_csv(BULL_RUN)
            # Taxonomy fix (Phase V-DATA-2): was EMERGING/STRONG_CANDIDATE --
            # STRONG_CANDIDATE stopped being produced a while back, so
            # BULL_RUN stocks (the platform's best label) never appeared in
            # any "top accumulation candidates" RAG sector document.
            for sec, grp in br[br["label"].isin(["EMERGING", "BULL_RUN"])].groupby("sector"):
                stock_map[sec] = grp.nlargest(5, "bull_run_score")["symbol"].tolist()

        docs = []
        for _, row in sectors.iterrows():
            sector = str(row.get("sector", "UNKNOWN"))
            rotation = str(row.get("rotation_signal", "UNKNOWN"))
            fii_flow = _fmt(row.get("FII_flow_score"))
            dii_flow = _fmt(row.get("DII_flow_score"))
            combined = _fmt(row.get("combined_score"))
            top_stocks = stock_map.get(sector, [])
            top_str = ", ".join(top_stocks) if top_stocks else "none identified"

            text = (
                f"Sector Analysis: {sector}. "
                f"Rotation signal is {rotation}. "
                f"FII flow score is {fii_flow} and DII flow score is {dii_flow}. "
                f"Combined institutional flow score is {combined}. "
                f"EARLY_ROTATION signals emerging institutional interest before broad market recognition. "
                f"LEADING indicates confirmed sector leadership. "
                f"Top accumulation candidates in this sector: {top_str}."
            )

            docs.append(_doc(
                "SECTOR", sector, f"sector_{_slug(sector)}", text,
                {
                    "sector": sector,
                    "rotation_signal": rotation,
                    "combined_score": combined,
                    "date": snapshot_date,
                }
            ))

        return docs

    # ------------------------------------------------------------------
    # Stock documents (top EMERGING + BULL_RUN)
    # ------------------------------------------------------------------

    def _build_stock_docs(self) -> list[dict]:
        if not BULL_RUN.exists():
            return []

        br = pd.read_csv(BULL_RUN)
        if br.empty:
            return []
        snapshot_date = _latest_snapshot_date()

        # ML scores enrichment
        ml: Optional[pd.DataFrame] = None
        if ML_SCORES.exists():
            ml = pd.read_csv(ML_SCORES, usecols=lambda c: c in
                             ["symbol", "ml_bull_run_score", "accumulation_score"])

        # Corporate confidence enrichment
        corp: Optional[pd.DataFrame] = None
        if CORP_CONF.exists():
            corp = pd.read_csv(CORP_CONF, usecols=lambda c: c in
                               ["symbol", "confidence_score_12m"])

        # Taxonomy fix (Phase V-DATA-2): STRONG_CANDIDATE was replaced by
        # BULL_RUN a while back -- this filter was silently excluding the
        # platform's best-labelled stocks from ever getting a RAG document.
        target = br[br["label"].isin(["EMERGING", "BULL_RUN", "WATCHLIST"])]
        target = target.nlargest(500, "bull_run_score")

        if ml is not None:
            target = target.merge(ml, on="symbol", how="left")
        if corp is not None:
            target = target.merge(corp, on="symbol", how="left")

        docs = []
        for _, row in target.iterrows():
            sym = str(row.get("symbol", "UNKNOWN"))
            sector = str(row.get("sector", "UNKNOWN"))
            label = str(row.get("label", "UNKNOWN"))
            score = _fmt(row.get("bull_run_score"))
            price_score = _fmt(row.get("price_score"))
            deal_score = _fmt(row.get("deal_score"))
            corp_score = _fmt(row.get("corporate_score"))
            ml_score = _fmt(row.get("ml_bull_run_score"))
            acc_score = _fmt(row.get("accumulation_score"))
            conf_12m = _fmt(row.get("confidence_score_12m"))
            predictive_ml = ml_score != "N/A" or acc_score != "N/A"

            text = (
                f"Stock Analysis: {sym} (sector: {sector}). "
                f"Accumulation label is {label} with bull run score of {score}. "
                f"Price momentum score is {price_score}. "
                f"Institutional deal score is {deal_score} and corporate action score is {corp_score}. "
            )
            if ml_score and ml_score != "N/A":
                text += f"ML bull run score is {ml_score} and accumulation score is {acc_score}. "
            if conf_12m and conf_12m != "N/A":
                text += f"Corporate confidence score over 12 months is {conf_12m}. "
            text += (
                f"A score above 65 puts this stock in BULL_RUN territory. "
                f"The capital flow cascade for {sym} goes: Institutional participant -> "
                f"{sector} sector -> {sym} stock."
            )

            docs.append(_doc(
                "STOCK", sym, f"stock_{sym}", text,
                {
                    "symbol": sym,
                    "sector": sector,
                    "label": label,
                    "score": score,
                    "bull_run_score": _num(row.get("bull_run_score")),
                    "price_score": _num(row.get("price_score")),
                    "deal_score": _num(row.get("deal_score")),
                    "corporate_score": _num(row.get("corporate_score")),
                    "ml_bull_run_score": _num(row.get("ml_bull_run_score")),
                    "accumulation_score": _num(row.get("accumulation_score")),
                    "confidence_score_12m": _num(row.get("confidence_score_12m")),
                    "date": snapshot_date,
                    "feature_date": snapshot_date,
                    "model_name": cfg.VEDA_PLATFORM_ML_MODEL_NAME if predictive_ml else None,
                    "model_version": cfg.VEDA_PLATFORM_ML_MODEL_VERSION if predictive_ml else None,
                    "score_meaning": (
                        "Higher bull-run and accumulation scores indicate a stronger local bullish "
                        "continuation signal in the platform scoring pipeline."
                        if predictive_ml
                        else None
                    ),
                    "reliability_note": (
                        "Treat these scores as predictive local signals, not guaranteed outcomes. "
                        "Confirm with current flows, price action, and corporate context."
                        if predictive_ml
                        else None
                    ),
                }
            ))

        return docs

    # ------------------------------------------------------------------
    # Deal documents
    # ------------------------------------------------------------------

    def _build_deal_docs(self) -> list[dict]:
        if not DEAL_SIG.exists():
            return []

        deals = pd.read_csv(DEAL_SIG)
        if deals.empty:
            return []
        snapshot_date = _latest_snapshot_date()

        docs = []
        for _, row in deals.iterrows():
            sym = str(row.get("symbol", "UNKNOWN"))
            net_val = _fmt(row.get("inst_net_value_cr"))
            deal_type = str(row.get("deal_type", "UNKNOWN"))

            text = (
                f"Institutional Deal Signal: {sym}. "
                f"Deal type is {deal_type} with net institutional value of {net_val} crores. "
                f"Positive values indicate net institutional buying (smart money accumulation). "
                f"Deal signals above 50 Cr trigger a P4 priority alert."
            )

            docs.append(_doc(
                "DEAL", sym, f"deal_{sym}", text,
                {"symbol": sym, "deal_type": deal_type, "net_value_cr": net_val, "date": snapshot_date}
            ))

        return docs

    # ------------------------------------------------------------------
    # Corporate confidence documents
    # ------------------------------------------------------------------

    def _build_corporate_docs(self) -> list[dict]:
        if not CORP_CONF.exists():
            return []

        corp = pd.read_csv(CORP_CONF)
        if corp.empty:
            return []
        snapshot_date = _latest_snapshot_date()

        # Top 200 by confidence
        top = corp.nlargest(200, "confidence_score_12m") if "confidence_score_12m" in corp.columns else corp.head(200)

        docs = []
        for _, row in top.iterrows():
            sym = str(row.get("symbol", "UNKNOWN"))
            score_12m = _fmt(row.get("confidence_score_12m"))
            score_6m = _fmt(row.get("confidence_score_6m", row.get("confidence_score", "N/A")))

            text = (
                f"Corporate Confidence: {sym}. "
                f"12-month corporate confidence score is {score_12m}. "
                f"6-month confidence score is {score_6m}. "
                f"Corporate confidence reflects promoter buybacks, dividend consistency, "
                f"and positive board announcements. A score above 2.0 triggers a P5 alert."
            )

            docs.append(_doc(
                "CORPORATE", sym, f"corp_{sym}", text,
                {
                    "symbol": sym,
                    "confidence_12m": score_12m,
                    "confidence_score_12m": _num(row.get("confidence_score_12m")),
                    "confidence_score_6m": _num(row.get("confidence_score_6m", row.get("confidence_score"))),
                    "date": snapshot_date,
                }
            ))

        return docs

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save(self, docs: list[dict]):
        tmp_docs = DOCS_OUT.with_suffix(".tmp.jsonl")
        with open(tmp_docs, "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        shutil.move(str(tmp_docs), str(DOCS_OUT))

        meta_rows = [
            {"doc_id": d["doc_id"], "domain": d["domain"],
             "entity": d["entity"], "text_len": len(d["text"])}
            for d in docs
        ]
        meta_df = pd.DataFrame(meta_rows)
        tmp_meta = META_OUT.with_suffix(".tmp.csv")
        meta_df.to_csv(tmp_meta, index=False)
        shutil.move(str(tmp_meta), str(META_OUT))

        logger.info(f"[DocBuilder] Saved {len(docs)} docs -> {DOCS_OUT}")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _doc(domain: str, entity: str, doc_id: str, text: str, meta: dict) -> dict:
    return {"doc_id": doc_id, "domain": domain, "entity": entity, "text": text, "meta": meta}


def _fmt(val) -> str:
    if val is None or (isinstance(val, float) and __import__("math").isnan(val)):
        return "N/A"
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)


def _num(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _slug(s: str) -> str:
    return s.lower().replace(" ", "_").replace("/", "_")


if __name__ == "__main__":
    engine = DocumentBuilder()
    n = engine.run()
    print(f"Built {n} documents")
    if n > 0:
        import json
        with open(DOCS_OUT) as f:
            sample = [json.loads(f.readline()) for _ in range(3)]
        for d in sample:
            print(f"  [{d['domain']}] {d['doc_id']}: {d['text'][:120]}...")
