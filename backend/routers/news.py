"""
News Router -- Dashboard market news aggregator
Fetches RSS from global reliable sources, caches 30 min, sentiment + region + category tags.
GET /api/news  ->  { items: list[NewsItem], cached_at: int }
"""

from __future__ import annotations
import asyncio
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/news", tags=["news"])

_UA      = "Mozilla/5.0 (compatible; MarketIntelBot/1.0)"
_TIMEOUT = 8.0
_TTL     = 1800   # 30-minute cache
_MAX     = 50     # max items returned

_FEEDS = [
    {"url": "https://feeds.reuters.com/reuters/businessNews",   "source": "Reuters Business",       "region": "GLOBAL"},
    {"url": "https://feeds.reuters.com/reuters/marketsNews",    "source": "Reuters Markets",        "region": "GLOBAL"},
    {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "source": "CNBC Markets", "region": "GLOBAL",
    },
    {
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "source": "Economic Times Markets", "region": "INDIA",
    },
    {
        "url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
        "source": "Economic Times", "region": "INDIA",
    },
    {
        "url": "https://www.business-standard.com/rss/markets-106.rss",
        "source": "Business Standard", "region": "INDIA",
    },
    {
        "url": "https://www.moneycontrol.com/rss/economy.xml",
        "source": "Moneycontrol", "region": "INDIA",
    },
    {
        "url": "https://www.livemint.com/rss/markets",
        "source": "Livemint", "region": "INDIA",
    },
    {
        "url": "https://finance.yahoo.com/news/rssindex",
        "source": "Yahoo Finance", "region": "GLOBAL",
    },
]

# ── Sentiment ─────────────────────────────────────────────────────────────────

_POS = frozenset([
    "rally", "surge", "gain", "rise", "jump", "soar", "bull", "strong",
    "robust", "growth", "profit", "positive", "upgrade", "outperform",
    "beat", "record high", "inflow", "recovery", "rebound", "boost",
    "advance", "climb", "optimism", "bullish", "overweight",
])
_NEG = frozenset([
    "fall", "drop", "decline", "plunge", "crash", "sell", "bear", "weak",
    "loss", "downgrade", "deficit", "recession", "concern", "risk",
    "warning", "below", "miss", "outflow", "slowdown", "contraction",
    "slump", "tumble", "pessimism", "bearish", "underweight", "cut",
])

def _sentiment(text: str) -> str:
    t = text.lower()
    pos = sum(1 for w in _POS if w in t)
    neg = sum(1 for w in _NEG if w in t)
    if pos > neg:  return "POSITIVE"
    if neg > pos:  return "NEGATIVE"
    return "NEUTRAL"

# ── Category tagging ──────────────────────────────────────────────────────────

_CATS = [
    (["fii", "dii", "institutional", "fund flow", "foreign investor", "mutual fund", "mf inflow"], "FLOWS"),
    (["ipo", "listing", "issue", "subscription", "allotment", "gmp"],                              "IPO"),
    (["earnings", "results", "profit", "revenue", "quarterly", " q1 ", " q2 ", " q3 ", " q4 ", "ebitda", "pat "], "EARNINGS"),
    (["rate", "inflation", "rbi", "fed", "gdp", "macro", "monetary policy", "cpi", "wpi", "repo", "rbi governor"], "MACRO"),
    (["oil", "gold", "silver", "commodity", "crude", "metal", "steel", "copper", "aluminium"],     "COMMODITIES"),
    (["rupee", " dollar", "forex", "currency", "usd/inr", "usd inr", "inr ", " eur "],            "FOREX"),
    (["crypto", "bitcoin", "ethereum", "blockchain", "web3"],                                       "CRYPTO"),
    (["sensex", "nifty", "stock", "equity", "share", "market", "index", "bse", "nse", "dalal"],   "EQUITIES"),
]

def _category(text: str) -> str:
    t = f" {text.lower()} "
    for kws, cat in _CATS:
        if any(k in t for k in kws):
            return cat
    return "OTHER"

# ── Date parsing ──────────────────────────────────────────────────────────────

def _parse_dt(raw: str) -> tuple[str, int]:
    if not raw:
        ts = int(time.time())
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ"), ts
    try:
        dt = parsedate_to_datetime(raw)
        ts = int(dt.timestamp())
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), ts
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(raw, fmt)
            ts = int(dt.timestamp())
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), ts
        except Exception:
            pass
    ts = int(time.time())
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ"), ts

# ── RSS parser ─────────────────────────────────────────────────────────────────

_HTML_RE = re.compile(r"<[^>]+>")


@dataclass
class _Item:
    title:        str
    url:          str
    source:       str
    published:    str
    published_ts: int
    summary:      str
    sentiment:    str
    region:       str
    category:     str


def _parse_rss(xml_bytes: bytes, source: str, region: str) -> list[_Item]:
    items: list[_Item] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    for el in root.iter("item"):
        title_el = el.find("title")
        link_el  = el.find("link")
        desc_el  = el.find("description")
        date_el  = el.find("pubDate")

        title   = (title_el.text or "").strip() if title_el is not None else ""
        url     = (link_el.text or "").strip()  if link_el  is not None else ""
        summary = ""
        if desc_el is not None and desc_el.text:
            summary = _HTML_RE.sub("", desc_el.text).strip()[:250]
        date_raw = (date_el.text or "").strip() if date_el is not None else ""

        if not title or not url:
            continue

        pub_iso, pub_ts = _parse_dt(date_raw)
        combined = f"{title} {summary}"
        items.append(_Item(
            title=title,
            url=url,
            source=source,
            published=pub_iso,
            published_ts=pub_ts,
            summary=summary,
            sentiment=_sentiment(combined),
            region=region,
            category=_category(combined),
        ))
    return items

# ── Async fetch ───────────────────────────────────────────────────────────────

async def _fetch_feed(client: httpx.AsyncClient, feed: dict) -> list[_Item]:
    try:
        r = await client.get(feed["url"], timeout=_TIMEOUT)
        r.raise_for_status()
        return _parse_rss(r.content, feed["source"], feed["region"])
    except Exception:
        return []

# ── In-memory cache ───────────────────────────────────────────────────────────

_cache_ts:   float      = 0.0
_cache_data: list[dict] = []


async def _get_news() -> list[dict]:
    global _cache_ts, _cache_data
    if time.time() - _cache_ts < _TTL and _cache_data:
        return _cache_data

    hdrs = {
        "User-Agent": _UA,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    async with httpx.AsyncClient(headers=hdrs, follow_redirects=True) as client:
        batches = await asyncio.gather(*[_fetch_feed(client, f) for f in _FEEDS])

    all_items: list[_Item] = [it for batch in batches for it in batch]

    seen: set[str] = set()
    unique: list[_Item] = []
    for it in sorted(all_items, key=lambda x: x.published_ts, reverse=True):
        if it.url and it.url not in seen:
            seen.add(it.url)
            unique.append(it)

    _cache_data = [asdict(it) for it in unique[:_MAX]]
    _cache_ts   = time.time()
    return _cache_data


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("")
async def get_news():
    """Latest market news from global RSS feeds (30-min cache)."""
    items = await _get_news()
    return {"items": items, "cached_at": int(_cache_ts), "count": len(items)}
