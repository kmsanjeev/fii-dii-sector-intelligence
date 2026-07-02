"""
AGM Intelligence Engine -- Phase H
Classifies BOARD_OUTCOME, DIVIDEND, MANAGEMENT_CHANGE, CAPEX_EXPANSION announcements
using Claude Haiku to extract governance signals per symbol.

Source: data/intelligence/company_announcements.csv  (Phase 18)
        Filters to BOARD/GOVERNANCE announcement types.
        Latest 1 record per symbol, cached by seq_id.

Run:
    py -3.11 engines/intelligence/agm_intelligence_engine.py

Outputs:
    data/intelligence/agm_signals.csv    -- latest governance signal per symbol

Guardrails: G-D-02 atomic writes, G-A-01 rate limiting, cost guard (max 400/run)
"""

import json
import os
import re
import shutil
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OUTPUT_PATH  = cfg.INTELLIGENCE_DIR / "agm_signals.csv"
CACHE_PATH   = cfg.INTELLIGENCE_DIR / "agm_seen_ids.json"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
MAX_PER_RUN  = 400     # cost guard: ~400 × 300 tokens ≈ 120K tokens ≈ $0.012

# Announcement types carrying governance intelligence
GOVERNANCE_TYPES = {
    "BOARD_OUTCOME",
    "DIVIDEND",
    "MANAGEMENT_CHANGE",
    "CAPEX_EXPANSION",
    "BUYBACK",
    "FUNDRAISE",
    "ACQUISITION",
}

SYSTEM_PROMPT = """You are a corporate governance analyst for Indian listed companies.
Given NSE announcement text, extract:

1. governance_risk: LOW | MEDIUM | HIGH
   (HIGH = auditor change, director exit, regulatory action, promoter pledge; LOW = routine)
2. dividend_signal: INCREASE | MAINTAIN | CUT | NONE
3. capex_confirm: YES | NO (new capital expenditure approved?)
4. management_change: YES | NO (CEO/MD/CFO/director change?)
5. sentiment: POSITIVE | NEUTRAL | NEGATIVE (overall corporate governance tone)
6. key_decision: one sentence (max 100 chars) capturing the most important board decision

Respond ONLY in this exact JSON (no markdown):
{
  "governance_risk": "LOW",
  "dividend_signal": "NONE",
  "capex_confirm": "NO",
  "management_change": "NO",
  "sentiment": "NEUTRAL",
  "key_decision": "Board approved Q2 results and declared interim dividend of Rs 5 per share."
}"""

GOVERNANCE_SCORE = {
    "LOW":    70,
    "MEDIUM": 50,
    "HIGH":   20,
}
SENTIMENT_SCORE = {
    "POSITIVE": 1,
    "NEUTRAL":  0,
    "NEGATIVE": -1,
}


def _load_cache() -> set:
    if CACHE_PATH.exists():
        try:
            return set(json.loads(CACHE_PATH.read_text()))
        except Exception:
            return set()
    return set()


def _save_cache(seen: set):
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(list(seen)[-15000:]))
    shutil.move(str(tmp), str(CACHE_PATH))


def _call_claude(text: str, client) -> dict:
    default = {
        "governance_risk": "MEDIUM", "dividend_signal": "NONE",
        "capex_confirm": "NO", "management_change": "NO",
        "sentiment": "NEUTRAL", "key_decision": "",
    }
    try:
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text[:700]}],
        )
        raw = msg.content[0].text.strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return {**default, **json.loads(m.group())}
    except Exception as ex:
        logger.warning("[AGMEngine] Claude failed: %s", ex)
    return default


def run() -> pd.DataFrame | None:
    logger.info("[AGMEngine] Phase H AGM/governance intelligence engine starting")

    if not ANTHROPIC_API_KEY:
        logger.error("[AGMEngine] ANTHROPIC_API_KEY not set")
        print("[AGMEngine] ERROR: set ANTHROPIC_API_KEY in .env")
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except ImportError:
        logger.error("[AGMEngine] anthropic package not installed")
        return None

    ann_path = cfg.INTELLIGENCE_DIR / "company_announcements.csv"
    if not ann_path.exists():
        logger.error("[AGMEngine] company_announcements.csv not found")
        return None

    ann = pd.read_csv(
        ann_path,
        usecols=["symbol", "date", "announcement_type", "title_snippet", "desc_raw"],
        dtype=str,
    )
    logger.info("[AGMEngine] Loaded %d announcements", len(ann))

    # Filter to governance types within last 12 months
    ann["date"] = pd.to_datetime(ann["date"], errors="coerce")
    cutoff = pd.Timestamp(date.today() - timedelta(days=365))
    gov_df = ann[
        ann["announcement_type"].isin(GOVERNANCE_TYPES)
        & (ann["date"] >= cutoff)
    ].copy()
    logger.info("[AGMEngine] %d governance announcements in last 12M (types: %s)",
                len(gov_df), gov_df["announcement_type"].value_counts().to_dict())

    if gov_df.empty:
        logger.error("[AGMEngine] No governance announcements found")
        return None

    # Latest 1 per symbol (most recent governance event)
    gov_df = (
        gov_df.sort_values("date", ascending=False)
        .groupby("symbol")
        .head(1)
        .reset_index(drop=True)
    )
    gov_df["symbol"] = gov_df["symbol"].str.upper().str.strip()
    logger.info("[AGMEngine] %d symbols with governance announcements", len(gov_df))

    # Cache filter
    seen_ids = _load_cache()
    seq_col = None
    if "seq_id" in ann.columns:
        seq_col = "seq_id"
        pending = gov_df[~gov_df["seq_id"].astype(str).isin(seen_ids)].copy()
    else:
        # Fallback key: symbol + date
        gov_df["_key"] = gov_df["symbol"] + "|" + gov_df["date"].astype(str)
        pending = gov_df[~gov_df["_key"].isin(seen_ids)].copy()
        seq_col = "_key"

    logger.info("[AGMEngine] %d new records to process (%d cached)",
                len(pending), len(gov_df) - len(pending))

    if pending.empty:
        logger.info("[AGMEngine] All records cached -- nothing new to process")
        print("[AGMEngine] All governance records already processed")
        return None

    batch = pending.head(MAX_PER_RUN)
    logger.info("[AGMEngine] Processing %d records (max %d/run)", len(batch), MAX_PER_RUN)

    rows = []
    for i, (_, rec) in enumerate(batch.iterrows()):
        symbol   = str(rec.get("symbol", "")).upper().strip()
        ann_type = str(rec.get("announcement_type", ""))
        title    = str(rec.get("title_snippet", "") or "")
        desc     = str(rec.get("desc_raw", "") or "")
        rec_date = rec["date"].strftime("%Y-%m-%d") if pd.notna(rec.get("date")) else ""
        seq_id   = str(rec.get(seq_col, f"{symbol}_{i}"))

        text = f"Company: {symbol}\nType: {ann_type}\nTitle: {title}\nDescription: {desc}"
        result = _call_claude(text, client)
        time.sleep(0.35)  # G-A-01 rate limit

        rows.append({
            "symbol":           symbol,
            "date":             rec_date,
            "announcement_type": ann_type,
            "governance_risk":  result.get("governance_risk", "MEDIUM"),
            "governance_score": GOVERNANCE_SCORE.get(result.get("governance_risk", "MEDIUM"), 50),
            "dividend_signal":  result.get("dividend_signal", "NONE"),
            "capex_confirm":    result.get("capex_confirm", "NO"),
            "management_change": result.get("management_change", "NO"),
            "sentiment":        result.get("sentiment", "NEUTRAL"),
            "sentiment_score":  SENTIMENT_SCORE.get(result.get("sentiment", "NEUTRAL"), 0),
            "key_decision":     str(result.get("key_decision", ""))[:120],
            "processed_at":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

        seen_ids.add(seq_id)
        if (i + 1) % 50 == 0:
            logger.info("[AGMEngine] %d/%d processed", i + 1, len(batch))

    _save_cache(seen_ids)

    if not rows:
        logger.warning("[AGMEngine] No rows generated")
        return None

    new_df = pd.DataFrame(rows)

    # Merge with existing (keep latest per symbol)
    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
        combined = (
            combined.sort_values("date", ascending=False)
            .drop_duplicates(subset=["symbol"], keep="first")
            .reset_index(drop=True)
        )
        combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")
    else:
        combined = new_df

    combined["as_of_date"] = date.today().isoformat()

    tmp = OUTPUT_PATH.with_suffix(".tmp")
    combined.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT_PATH))

    # Summary
    high_risk = (combined["governance_risk"] == "HIGH").sum()
    dividends  = (combined["dividend_signal"] != "NONE").sum()
    capex_yes  = (combined["capex_confirm"] == "YES").sum()
    mgmt_chg   = (combined["management_change"] == "YES").sum()

    print(f"\n[AGMEngine] Phase H AGM/governance intelligence complete")
    print(f"  Records processed  : {len(batch)}")
    print(f"  Symbols with signal: {len(combined)}")
    print(f"  High governance risk: {high_risk}")
    print(f"  Dividend signals    : {dividends}")
    print(f"  Capex confirmations : {capex_yes}")
    print(f"  Management changes  : {mgmt_chg}")
    print()
    if high_risk:
        print("  HIGH RISK governance signals:")
        top_risk = combined[combined["governance_risk"] == "HIGH"].head(6)
        for _, r in top_risk.iterrows():
            print(f"    {r['symbol']:<14} {str(r.get('key_decision',''))[:60]}")

    logger.info("[AGMEngine] Done -- %d symbols, %d high-risk", len(combined), high_risk)
    return combined


if __name__ == "__main__":
    run()
