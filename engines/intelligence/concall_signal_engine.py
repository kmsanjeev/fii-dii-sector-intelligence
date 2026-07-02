"""
Concall Signal Intelligence Engine — Phase F
Extracts structured signals from NSE announcement text (ANALYST_MEET + RESULT_UPDATE types).
Uses Claude Haiku to classify: sentiment, capex signal, guidance direction, theme keywords.

Source: data/intelligence/company_announcements.csv  (371K rows, Phase 18)
        Filters to ANALYST_MEET + RESULT_UPDATE types (~71K rows)
        Processes latest 2 concall records per symbol, caches by seq_id.

Run:
    py -3.11 engines/intelligence/concall_signal_engine.py

Outputs:
    data/intelligence/concall_signals.csv    — one row per announcement processed
    data/intelligence/concall_summary.csv    — latest signal per symbol (ML-ready)

Guardrails: G-D-02 atomic writes, G-A-01 rate limiting, cost guard (max 500/run)
"""

import json
import os
import re
import shutil
import sys
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.llm_client import call_llm, available_providers

logger = get_logger(__name__)

SIGNALS_PATH  = cfg.INTELLIGENCE_DIR / "concall_signals.csv"
SUMMARY_PATH  = cfg.INTELLIGENCE_DIR / "concall_summary.csv"
CACHE_PATH    = cfg.INTELLIGENCE_DIR / "concall_seen_ids.json"
MAX_PER_RUN   = 500
RECORDS_PER_SYMBOL = 2  # process latest N concall records per symbol

CONCALL_TYPES = {"ANALYST_MEET", "RESULT_UPDATE"}

SYSTEM_PROMPT = """You are a financial analyst specialising in Indian listed companies.
Given NSE announcement text from a company concall / quarterly results, extract:

1. sentiment: BULLISH | NEUTRAL | BEARISH (overall management tone)
2. guidance_direction: RAISED | MAINTAINED | LOWERED | NOT_GIVEN
3. capex_signal: YES | NO (does management mention new capital expenditure plans?)
4. capex_amount_cr: numeric crore value if mentioned, else null
5. themes: list of 0-3 relevant themes from:
   [CAPEX_CYCLE, DIGITAL_INDIA, AI_ENABLERS, DATA_CENTRE, POWER_TD, GREEN_ENERGY,
    RAILWAYS_METRO, DEFENCE_ELECTRONICS, EV_TRANSITION, BANKING_CREDIT, EXPORT_GROWTH,
    CHINA_PLUS_ONE, HEALTHCARE_EXPANSION, SPECIALTY_CHEM, INFRASTRUCTURE_BUILD,
    GREEN_HYDROGEN, BATTERY_STORAGE, SEMICONDUCTOR, INDIA_PLUS_ONE, COMMODITY_SUPER]
6. key_statement: one sentence (max 120 chars) capturing the most important management signal

Respond ONLY in this exact JSON (no markdown):
{
  "sentiment": "BULLISH",
  "guidance_direction": "RAISED",
  "capex_signal": "YES",
  "capex_amount_cr": 5000,
  "themes": ["CAPEX_CYCLE", "POWER_TD"],
  "key_statement": "Management guided 25% revenue growth for FY27 driven by new order wins."
}"""

GUIDANCE_SCORE = {
    "RAISED":      2,
    "MAINTAINED":  1,
    "LOWERED":    -1,
    "NOT_GIVEN":   0,
}
SENTIMENT_SCORE = {"BULLISH": 1, "NEUTRAL": 0, "BEARISH": -1}


def _load_cache() -> set:
    if CACHE_PATH.exists():
        try:
            return set(json.loads(CACHE_PATH.read_text()))
        except Exception:
            return set()
    return set()


def _save_cache(seen: set):
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(list(seen)[-10000:]))
    shutil.move(str(tmp), str(CACHE_PATH))


def _call_llm(text: str) -> dict:
    raw = call_llm(system=SYSTEM_PROMPT, user=text[:800], max_tokens=250)
    if raw:
        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception as ex:
            logger.warning(f"[ConcallSignal] JSON parse failed: {ex}")
    return {
        "sentiment": "NEUTRAL", "guidance_direction": "NOT_GIVEN",
        "capex_signal": "NO", "capex_amount_cr": None,
        "themes": [], "key_statement": "",
    }


def run():
    logger.info("[ConcallSignal] Starting Phase F concall signal engine")

    providers = available_providers()
    if not providers:
        logger.error("[ConcallSignal] No LLM provider keys found in .env")
        print("[ConcallSignal] ERROR: add at least one API key to .env")
        return None
    logger.info(f"[ConcallSignal] LLM providers available: {providers}")

    ann_path = cfg.INTELLIGENCE_DIR / "company_announcements.csv"
    if not ann_path.exists():
        logger.error(f"[ConcallSignal] Announcements file not found: {ann_path}")
        return None

    ann_df = pd.read_csv(ann_path, low_memory=False)
    logger.info(f"[ConcallSignal] Loaded {len(ann_df)} announcements")

    # Filter concall-type announcements
    concall_df = ann_df[ann_df["announcement_type"].isin(CONCALL_TYPES)].copy()
    logger.info(f"[ConcallSignal] {len(concall_df)} concall-type records across types: "
                f"{concall_df['announcement_type'].value_counts().to_dict()}")

    if concall_df.empty:
        logger.error("[ConcallSignal] No ANALYST_MEET/RESULT_UPDATE records found")
        return None

    # Sort by date descending; take latest N per symbol
    concall_df["date"] = pd.to_datetime(concall_df["date"], errors="coerce")
    concall_df = concall_df.dropna(subset=["date"])
    concall_df = concall_df.sort_values("date", ascending=False)
    concall_df = (
        concall_df.groupby("symbol", group_keys=False)
        .head(RECORDS_PER_SYMBOL)
        .reset_index(drop=True)
    )
    logger.info(f"[ConcallSignal] After top-{RECORDS_PER_SYMBOL}/symbol filter: {len(concall_df)} records")

    # Load cache of already-processed seq_ids
    seen_ids = _load_cache()

    # Skip already processed
    seq_col = "seq_id" if "seq_id" in concall_df.columns else None
    if seq_col:
        pending = concall_df[~concall_df[seq_col].astype(str).isin(seen_ids)].copy()
    else:
        pending = concall_df.copy()

    logger.info(f"[ConcallSignal] {len(pending)} records to process (skipping {len(concall_df) - len(pending)} cached)")

    if pending.empty:
        logger.info("[ConcallSignal] All records already cached — nothing new to process")
        print("[ConcallSignal] All concall records already processed (cached)")
        return None

    batch = pending.head(MAX_PER_RUN)
    logger.info(f"[ConcallSignal] Processing {len(batch)} records (max {MAX_PER_RUN}/run)")

    rows = []
    for i, (_, rec) in enumerate(batch.iterrows()):
        symbol = str(rec.get("symbol", "")).upper().strip()
        ann_type = str(rec.get("announcement_type", ""))
        title = str(rec.get("title_snippet", "") or "")
        desc  = str(rec.get("desc_raw", "") or "")
        seq_id = str(rec.get(seq_col, f"{symbol}_{i}")) if seq_col else f"{symbol}_{i}"
        rec_date = rec["date"].strftime("%Y-%m-%d") if pd.notna(rec["date"]) else ""

        # Combine text for Claude
        text = f"Company: {symbol}\nType: {ann_type}\nTitle: {title}\nDescription: {desc}"

        result = _call_llm(text)
        time.sleep(0.4)  # G-A-01 rate limit (~2.5 req/s)

        rows.append({
            "symbol":             symbol,
            "date":               rec_date,
            "announcement_type":  ann_type,
            "seq_id":             seq_id,
            "sentiment":          result.get("sentiment", "NEUTRAL"),
            "sentiment_score":    SENTIMENT_SCORE.get(result.get("sentiment", "NEUTRAL"), 0),
            "guidance_direction": result.get("guidance_direction", "NOT_GIVEN"),
            "guidance_score":     GUIDANCE_SCORE.get(result.get("guidance_direction", "NOT_GIVEN"), 0),
            "capex_signal":       result.get("capex_signal", "NO"),
            "capex_amount_cr":    result.get("capex_amount_cr"),
            "themes":             ",".join(result.get("themes", [])[:3]),
            "key_statement":      str(result.get("key_statement", ""))[:150],
            "processed_at":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

        seen_ids.add(seq_id)

        if (i + 1) % 50 == 0:
            logger.info(f"[ConcallSignal] {i+1}/{len(batch)} processed")

    _save_cache(seen_ids)

    if not rows:
        logger.warning("[ConcallSignal] No rows generated")
        return None

    new_df = pd.DataFrame(rows)

    # Append to existing signals CSV
    if SIGNALS_PATH.exists():
        old_df = pd.read_csv(SIGNALS_PATH)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        if seq_col:
            combined = combined.drop_duplicates(subset=["seq_id"], keep="last")
    else:
        combined = new_df

    tmp = SIGNALS_PATH.with_suffix(".tmp")
    combined.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(SIGNALS_PATH))
    logger.info(f"[ConcallSignal] Wrote {len(combined)} rows to {SIGNALS_PATH}")

    # ── Summary: latest signal per symbol (for ML features) ────────────────────
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    summary = (
        combined.sort_values("date", ascending=False)
        .groupby("symbol")
        .first()
        .reset_index()
    )[["symbol", "date", "sentiment", "sentiment_score", "guidance_direction",
       "guidance_score", "capex_signal", "capex_amount_cr", "themes", "key_statement"]]

    summary["date"] = summary["date"].dt.strftime("%Y-%m-%d")
    summary["as_of_date"] = date.today().strftime("%Y-%m-%d")

    # Compound concall score: guidance drives 60%, sentiment 40%
    summary["concall_score"] = (
        summary["guidance_score"] * 0.6 + summary["sentiment_score"] * 0.4
    ).round(2)

    tmp2 = SUMMARY_PATH.with_suffix(".tmp")
    summary.to_csv(tmp2, index=False)
    shutil.move(str(tmp2), str(SUMMARY_PATH))

    # Print summary
    bull = (summary["sentiment"] == "BULLISH").sum()
    bear = (summary["sentiment"] == "BEARISH").sum()
    capex_yes = (summary["capex_signal"] == "YES").sum()
    raised = (summary["guidance_direction"] == "RAISED").sum()

    print(f"\n[ConcallSignal] Phase F concall intelligence complete")
    print(f"  Records processed  : {len(batch)}")
    print(f"  Symbols with signal: {len(summary)}")
    print(f"  Bullish / Bearish  : {bull} / {bear}")
    print(f"  Guidance raised    : {raised}")
    print(f"  Capex signals      : {capex_yes}")
    print()
    print("  Top BULLISH signals:")
    top = summary[summary["sentiment"] == "BULLISH"].nlargest(6, "concall_score")
    for _, r in top.iterrows():
        print(f"    {r['symbol']:<15} guidance={r['guidance_direction']}  score={r['concall_score']}")

    logger.info(f"[ConcallSignal] Done — {len(summary)} symbol summaries written")
    return summary


if __name__ == "__main__":
    run()
