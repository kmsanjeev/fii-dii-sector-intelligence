"""
News Sentiment Intelligence Engine — Phase F
Fetches RSS from Mint + MoneyControl, extracts symbol mentions and theme signals
via Claude Haiku, produces rolling 7-day sentiment per symbol.

Run:
    py -3.11 engines/intelligence/news_sentiment_engine.py

Outputs:
    data/intelligence/news_sentiment.csv   — one row per article-symbol pair
    data/intelligence/news_signals.csv     — 7-day rolling aggregated per symbol

Guardrails: G-D-02 atomic writes, G-D-03 no empty df, G-A-01 rate limiting
"""

import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.llm_client import call_llm, available_providers

logger = get_logger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
SENTIMENT_PATH  = cfg.INTELLIGENCE_DIR / "news_sentiment.csv"
SIGNALS_PATH    = cfg.INTELLIGENCE_DIR / "news_signals.csv"
SEEN_IDS_PATH   = cfg.INTELLIGENCE_DIR / "news_seen_ids.json"
ROLLING_DAYS    = 7
MAX_ARTICLES_PER_RUN = 200

RSS_FEEDS = [
    ("MINT_MARKETS",    "https://www.livemint.com/rss/markets"),
    ("MINT_COMPANIES",  "https://www.livemint.com/rss/companies"),
    ("MINT_ECONOMY",    "https://www.livemint.com/rss/economy"),
    ("MC_BUZZING",      "https://www.moneycontrol.com/rss/buzzingstocks.xml"),
    ("MC_NEWS",         "https://www.moneycontrol.com/rss/latestnews.xml"),
]

SENTIMENT_SYSTEM = """You are a financial news analyst specializing in Indian stock markets.
Given a news headline and summary, extract:
1. Indian NSE symbols mentioned (use exact NSE trading symbols like INFY, RELIANCE, TCS)
2. Sentiment for each symbol: BULLISH / NEUTRAL / BEARISH
3. Theme tags from this list (comma-separated, max 3):
   CAPEX_CYCLE, CHINA_PLUS_ONE, FINANCIALISATION, RURAL_CONSUMPTION, DIGITAL_INDIA,
   HEALTHCARE_EXPANSION, PREMIUMISATION, EV_TRANSITION, INFRASTRUCTURE_BUILD,
   REAL_ESTATE_RECOVERY, GREEN_ENERGY, LOGISTICS_MODERNISATION, DEFENCE_ELECTRONICS,
   EXPORT_GROWTH, PSU_REVIVAL, DATA_CENTRE, AI_ENABLERS, SEMICONDUCTOR, FINTECH_INFRASTR,
   CYBERSECURITY, POWER_TD, WATER_MANAGEMENT, RAILWAYS_METRO, PORTS_SHIPPING, GREEN_HYDROGEN,
   BANKING_CREDIT, INSURANCE_GROWTH, WEALTH_MGMT, MICROFINANCE, HEALTHTECH, SPECIALTY_CHEM,
   QUICK_COMMERCE, GOLD_JEWELLERY, TOURISM_HOSP, MEDIA_ENTERTAIN, LARGECAP_VALUE,
   MIDCAP_MOMENTUM, SMALLCAP_QUALITY, DIVIDEND_YIELD, QUALITY_GROWTH, TURNAROUND,
   SPACE_ECONOMY, AGRITECH, BATTERY_STORAGE, GAMING_ESPORTS, INDIA_PLUS_ONE,
   INTEREST_RATE_CYCLE, COMMODITY_SUPER, MONSOON_AGRI, SMART_CITIES

Respond ONLY in this exact JSON format:
{
  "symbols": [{"symbol": "NSE_SYMBOL", "sentiment": "BULLISH/NEUTRAL/BEARISH"}],
  "themes": ["THEME1", "THEME2"],
  "signal_type": "COMPANY_SPECIFIC|SECTOR|MACRO|IRRELEVANT",
  "india_relevant": true/false
}
If no Indian stocks mentioned, return {"symbols": [], "themes": [], "signal_type": "IRRELEVANT", "india_relevant": false}
"""


def _load_seen_ids() -> set:
    if SEEN_IDS_PATH.exists():
        try:
            return set(json.loads(SEEN_IDS_PATH.read_text()))
        except Exception:
            return set()
    return set()


def _save_seen_ids(seen: set):
    tmp = SEEN_IDS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(list(seen)[-5000:]))  # keep last 5000
    shutil.move(str(tmp), str(SEEN_IDS_PATH))


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _fetch_articles() -> list[dict]:
    """Fetch all RSS feeds and return deduplicated article dicts."""
    articles = []
    seen_titles: set[str] = set()

    for source, url in RSS_FEEDS:
        try:
            d = feedparser.parse(url)
            for e in d.entries:
                title = e.get("title", "").strip()
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                articles.append({
                    "id":        e.get("id", e.get("link", title))[:200],
                    "source":    source,
                    "title":     title,
                    "summary":   _strip_html(e.get("summary", ""))[:500],
                    "published": e.get("published", ""),
                    "link":      e.get("link", "")[:300],
                })
            logger.info(f"[NewsSentiment] {source}: {len(d.entries)} articles")
        except Exception as ex:
            logger.warning(f"[NewsSentiment] Feed {source} failed: {ex}")

    return articles


def _llm_extract(title: str, summary: str) -> dict:
    """Extract symbols, sentiment, themes from one article via fallback LLM chain."""
    prompt = f"Headline: {title}\n\nSummary: {summary[:400]}"
    raw = call_llm(system=SENTIMENT_SYSTEM, user=prompt, max_tokens=300)
    if raw:
        try:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception as ex:
            logger.warning(f"[NewsSentiment] JSON parse failed: {ex}")
    return {"symbols": [], "themes": [], "signal_type": "IRRELEVANT", "india_relevant": False}


def _sentiment_score(sentiment: str) -> float:
    return {"BULLISH": 1.0, "NEUTRAL": 0.0, "BEARISH": -1.0}.get(sentiment.upper(), 0.0)


def run():
    logger.info("[NewsSentiment] Starting Phase F news intelligence engine")

    providers = available_providers()
    if not providers:
        logger.error("[NewsSentiment] No LLM provider keys found in .env")
        print("[NewsSentiment] ERROR: add at least one of GROQ_API_KEY / GEMINI_API_KEY / OPENROUTER_API_KEY to .env")
        return None
    logger.info(f"[NewsSentiment] LLM providers available: {providers}")

    # Load seen IDs to skip reprocessing
    seen_ids = _load_seen_ids()

    # Fetch articles
    articles = _fetch_articles()
    new_articles = [a for a in articles if a["id"] not in seen_ids]
    logger.info(f"[NewsSentiment] {len(articles)} total, {len(new_articles)} new")

    if not new_articles:
        logger.info("[NewsSentiment] No new articles — nothing to process")
        print("[NewsSentiment] No new articles to process")
        return None

    # Cap to MAX_ARTICLES_PER_RUN (cost guard)
    batch = new_articles[:MAX_ARTICLES_PER_RUN]

    rows = []
    processed = 0
    for art in batch:
        result = _llm_extract(art["title"], art["summary"])
        time.sleep(0.3)  # G-A-01 rate limit

        if not result.get("india_relevant", False) or not result.get("symbols"):
            # Still mark as seen, just no signal
            seen_ids.add(art["id"])
            continue

        pub_str = art.get("published", "")
        try:
            from email.utils import parsedate_to_datetime
            pub_dt = parsedate_to_datetime(pub_str).strftime("%Y-%m-%d")
        except Exception:
            pub_dt = datetime.now().strftime("%Y-%m-%d")

        themes_str = ",".join(result.get("themes", [])[:3])
        signal_type = result.get("signal_type", "COMPANY_SPECIFIC")

        for sym_entry in result.get("symbols", []):
            symbol = str(sym_entry.get("symbol", "")).upper().strip()
            sentiment = str(sym_entry.get("sentiment", "NEUTRAL")).upper()
            if not symbol or len(symbol) > 20:
                continue
            rows.append({
                "symbol":      symbol,
                "date":        pub_dt,
                "source":      art["source"],
                "headline":    art["title"][:200],
                "sentiment":   sentiment,
                "sent_score":  _sentiment_score(sentiment),
                "themes":      themes_str,
                "signal_type": signal_type,
                "link":        art["link"],
                "article_id":  art["id"][:200],
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

        seen_ids.add(art["id"])
        processed += 1
        if processed % 20 == 0:
            logger.info(f"[NewsSentiment] Processed {processed}/{len(batch)}")

    _save_seen_ids(seen_ids)

    if not rows:
        logger.info("[NewsSentiment] No India-relevant articles found in batch")
        print("[NewsSentiment] No India-relevant signals extracted")
        return None

    new_df = pd.DataFrame(rows)

    # Append to existing sentiment CSV (keep last 90 days)
    if SENTIMENT_PATH.exists():
        old_df = pd.read_csv(SENTIMENT_PATH)
        cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        old_df = old_df[old_df["date"] >= cutoff]
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["article_id", "symbol"])
    else:
        combined = new_df

    tmp = SENTIMENT_PATH.with_suffix(".tmp")
    combined.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(SENTIMENT_PATH))
    logger.info(f"[NewsSentiment] Saved {len(combined)} rows to {SENTIMENT_PATH}")

    # ── Generate 7-day rolling signals per symbol ──────────────────────────────
    cutoff_7d = (datetime.now() - timedelta(days=ROLLING_DAYS)).strftime("%Y-%m-%d")
    recent = combined[combined["date"] >= cutoff_7d].copy()

    if recent.empty:
        logger.warning("[NewsSentiment] No recent data for rolling signals")
        return combined

    def _most_common(series):
        return series.value_counts().index[0] if len(series) else ""

    signals = (
        recent.groupby("symbol")
        .agg(
            news_count_7d    = ("article_id", "nunique"),
            sentiment_7d     = ("sent_score", "mean"),
            bullish_count    = ("sentiment", lambda x: (x == "BULLISH").sum()),
            bearish_count    = ("sentiment", lambda x: (x == "BEARISH").sum()),
            top_theme        = ("themes", _most_common),
            latest_headline  = ("headline", "last"),
            latest_date      = ("date", "max"),
        )
        .reset_index()
    )
    signals["sentiment_label"] = signals["sentiment_7d"].apply(
        lambda v: "BULLISH" if v > 0.2 else ("BEARISH" if v < -0.2 else "NEUTRAL")
    )
    signals["as_of_date"] = datetime.now().strftime("%Y-%m-%d")

    tmp2 = SIGNALS_PATH.with_suffix(".tmp")
    signals.to_csv(tmp2, index=False)
    shutil.move(str(tmp2), str(SIGNALS_PATH))

    # Summary
    print(f"\n[NewsSentiment] Phase F news intelligence complete")
    print(f"  Articles processed : {processed}")
    print(f"  Symbol-mentions    : {len(rows)}")
    print(f"  Unique symbols     : {new_df['symbol'].nunique()}")
    print(f"  7D signals written : {len(signals)} symbols")
    print(f"  Top mentioned:")
    top = new_df["symbol"].value_counts().head(8)
    for sym, cnt in top.items():
        print(f"    {sym:<15} {cnt} articles")

    logger.info(f"[NewsSentiment] Done — {len(signals)} symbol signals written")
    return signals


if __name__ == "__main__":
    run()
