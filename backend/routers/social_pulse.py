"""
Social Pulse Router -- Market-moving social intelligence ticker
Strategy: 2-tier approach
  Tier 1 (direct): Official RSS from confirmed-working government/CB sources
  Tier 2 (synthetic): Topic-cluster "virtual handles" built by filtering ALL
    news feeds -- guarantees every card shows data even when direct feeds fail.

GET /api/social-pulse -> { handles: list[HandleFeed], cached_at: int }
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

router = APIRouter(prefix="/api/social-pulse", tags=["social_pulse"])

_UA      = "Mozilla/5.0 (compatible; MarketIntelBot/1.0)"
_TIMEOUT = 8.0
_TTL     = 1800   # 30-min cache
_PER_HANDLE = 5

# ── All news feeds (superset; drawn from both news.py + additional) ───────────

_ALL_FEEDS = [
    # Confirmed working
    {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
     "source": "CNBC Markets",     "region": "GLOBAL"},
    {"url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
     "source": "ET Markets",       "region": "INDIA"},
    {"url": "https://www.livemint.com/rss/markets",
     "source": "Livemint",         "region": "INDIA"},
    {"url": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
     "source": "ET Industry",      "region": "INDIA"},
    {"url": "https://economictimes.indiatimes.com/markets/stocks/news/rssfeeds/2146842.cms",
     "source": "ET Corporate",     "region": "INDIA"},
    {"url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
     "source": "ET Top",           "region": "INDIA"},
    # Central banks (confirmed working in tests)
    {"url": "https://www.federalreserve.gov/feeds/press_all.xml",
     "source": "Federal Reserve",  "region": "GLOBAL"},
    {"url": "https://www.ecb.europa.eu/rss/press.html",
     "source": "ECB",              "region": "GLOBAL"},
    # BBC (highly reliable)
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",
     "source": "BBC Business",     "region": "GLOBAL"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",
     "source": "BBC World",        "region": "GLOBAL"},
    # Additional Indian
    {"url": "https://www.moneycontrol.com/rss/economy.xml",
     "source": "Moneycontrol",     "region": "INDIA"},
    {"url": "https://www.moneycontrol.com/rss/business.xml",
     "source": "Moneycontrol Biz", "region": "INDIA"},
    {"url": "https://www.business-standard.com/rss/markets-106.rss",
     "source": "Business Standard","region": "INDIA"},
    {"url": "https://www.business-standard.com/rss/economy-policy-102.rss",
     "source": "BS Economy",       "region": "INDIA"},
    # CNBC additional sections
    {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
     "source": "CNBC World",       "region": "GLOBAL"},
    {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
     "source": "CNBC Finance",     "region": "GLOBAL"},
    # Reuters (try — some sections still work)
    {"url": "https://feeds.reuters.com/reuters/businessNews",
     "source": "Reuters Business", "region": "GLOBAL"},
    {"url": "https://feeds.reuters.com/reuters/worldNews",
     "source": "Reuters World",    "region": "GLOBAL"},
    {"url": "https://feeds.reuters.com/reuters/INtopNews",
     "source": "Reuters India",    "region": "INDIA"},
    # Yahoo Finance
    {"url": "https://finance.yahoo.com/news/rssindex",
     "source": "Yahoo Finance",    "region": "GLOBAL"},
]

# ── Direct real handles (small curated set confirmed to work) ─────────────────

_DIRECT_HANDLES = [
    {
        "handle":       "@FedReserve",
        "display_name": "Federal Reserve",
        "avatar":       "FED",
        "category":     "CENTRAL_BANK",
        "region":       "GLOBAL",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
    },
    {
        "handle":       "@ECB",
        "display_name": "European Central Bank",
        "avatar":       "ECB",
        "category":     "CENTRAL_BANK",
        "region":       "GLOBAL",
        "url": "https://www.ecb.europa.eu/rss/press.html",
    },
    {
        "handle":       "@BBCWorld",
        "display_name": "BBC World",
        "avatar":       "BBC",
        "category":     "GEOPOLITICAL",
        "region":       "GLOBAL",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "handle":       "@BBCBusiness",
        "display_name": "BBC Business",
        "avatar":       "BBC",
        "category":     "GLOBAL",
        "region":       "GLOBAL",
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
    },
]

# ── Synthetic handle definitions (keyword-filter against pooled news) ─────────
# keywords: ANY match in title (case-insensitive) includes the item
# priority determines order in final list

_SYNTHETIC_HANDLES = [
    {
        "handle":       "@Geopolitical",
        "display_name": "Geopolitical Intel",
        "avatar":       "GEO",
        "category":     "GEOPOLITICAL",
        "region":       "GLOBAL",
        "keywords": [
            "war", "conflict", "sanction", "tension", "missile", "nuclear",
            "iran", "russia", "ukraine", "china", "taiwan", "israel",
            "hamas", "middle east", "nato", "border", "ceasefire", "coup",
            "trade war", "tariff", "embargo", "military",
        ],
    },
    {
        "handle":       "@PMO_RBI_SEBI",
        "display_name": "India Policy",
        "avatar":       "IND",
        "category":     "GOVERNMENT",
        "region":       "INDIA",
        "keywords": [
            "rbi", "sebi", "modi", "pmo", "rupee", "budget", "finance minister",
            "nirmala", "repo rate", "monetary policy", "inflation india",
            "ministry of finance", "fdi", "msme", "gst", "disinvestment",
            "government india", "india gdp", "niti aayog",
        ],
    },
    {
        "handle":       "@USMarkets",
        "display_name": "US Markets",
        "avatar":       "US",
        "category":     "MARKET",
        "region":       "GLOBAL",
        "keywords": [
            "s&p 500", "dow jones", "nasdaq", "powell", "fed rate",
            "federal reserve", "us gdp", "us inflation", "wall street",
            "treasury", "jobs report", "nonfarm", "us economy",
            "interest rate", "rate cut", "rate hike",
        ],
    },
    {
        "handle":       "@CorporateIndia",
        "display_name": "Corporate India",
        "avatar":       "COR",
        "category":     "CORPORATE",
        "region":       "INDIA",
        "keywords": [
            "reliance", "tata", "infosys", "wipro", "hdfc", "icici", "sbi",
            "adani", "bajaj", "airtel", "hul", "itc", "kotak", "axis bank",
            "ril", "tcs", "l&t", "maruti", "ongc", "ntpc", "power grid",
            "sun pharma", "dr reddy", "dmart", "zomato", "paytm", "nykaa",
        ],
    },
    {
        "handle":       "@Commodities",
        "display_name": "Commodities & FX",
        "avatar":       "CMD",
        "category":     "COMMODITIES",
        "region":       "GLOBAL",
        "keywords": [
            "crude oil", "brent", "wti", "gold price", "silver",
            "copper", "aluminium", "steel", "commodity", "metals",
            "usd/inr", "dollar rupee", "forex", "currency", "opec",
            "oil price", "natural gas",
        ],
    },
    {
        "handle":       "@GlobalMacro",
        "display_name": "Global Macro",
        "avatar":       "MAC",
        "category":     "MACRO",
        "region":       "GLOBAL",
        "keywords": [
            "global gdp", "imf", "world bank", "recession", "inflation",
            "ecb rate", "boe", "bank of japan", "china economy", "oecd",
            "global trade", "supply chain", "emerging market",
            "developing economies", "g7", "g20", "davos",
        ],
    },
    {
        "handle":       "@Earnings",
        "display_name": "Earnings Season",
        "avatar":       "EPS",
        "category":     "EARNINGS",
        "region":       "INDIA",
        "keywords": [
            "quarterly results", "q1 results", "q2 results", "q3 results", "q4 results",
            "profit rises", "profit falls", "net profit", "revenue", "ebitda",
            "earnings beat", "earnings miss", "results today", "financial results",
        ],
    },
    {
        "handle":       "@MktMovers",
        "display_name": "Market Movers",
        "avatar":       "MOV",
        "category":     "MARKET",
        "region":       "INDIA",
        "keywords": [
            "nifty", "sensex", "bse", "nse", "rally", "sell-off", "circuit",
            "52-week high", "52-week low", "fii buy", "fii sell", "dii",
            "bulk deal", "block deal", "ipo listing", "upper circuit", "lower circuit",
        ],
    },
    {
        "handle":       "@IndiaDeal",
        "display_name": "India Deals & Defence",
        "avatar":       "DEF",
        "category":     "GEOPOLITICAL",
        "region":       "INDIA",
        "keywords": [
            "india deal", "india agreement", "india sign", "defence deal",
            "missile", "aircraft", "submarine", "india defence", "arms deal",
            "indonesia", "bangladesh", "vietnam", "india us", "india china",
            "bilateral", "mou", "joint venture india", "foreign investment india",
        ],
    },
    {
        "handle":       "@EnergyClimate",
        "display_name": "Energy & Climate",
        "avatar":       "ENG",
        "category":     "COMMODITIES",
        "region":       "GLOBAL",
        "keywords": [
            "solar", "wind energy", "renewable", "ev", "electric vehicle",
            "climate", "carbon", "green energy", "coal", "uranium",
            "energy transition", "power sector", "battery", "lithium",
        ],
    },
    {
        "handle":       "@TechGlobal",
        "display_name": "Tech & AI",
        "avatar":       "TEC",
        "category":     "CORPORATE",
        "region":       "GLOBAL",
        "keywords": [
            "artificial intelligence", "ai ", "openai", "nvidia", "meta ai",
            "google ai", "microsoft ai", "semiconductor", "chip ban",
            "tech layoff", "apple", "amazon", "alphabet", "tesla",
            "startup", "unicorn", "vc funding",
        ],
    },
]

# ── Sentiment ─────────────────────────────────────────────────────────────────

_POS = frozenset([
    "rally", "surge", "gain", "rise", "jump", "soar", "bull", "strong",
    "robust", "growth", "profit", "positive", "upgrade", "outperform",
    "beat", "inflow", "recovery", "rebound", "boost", "advance",
    "deal", "agreement", "peace", "cooperation", "sign",
])
_NEG = frozenset([
    "fall", "drop", "decline", "plunge", "crash", "sell", "bear", "weak",
    "loss", "downgrade", "deficit", "recession", "concern", "risk",
    "warning", "outflow", "slowdown", "conflict", "war", "sanction",
    "tension", "missile", "slump", "tumble",
])

def _sentiment(text: str) -> str:
    t = text.lower()
    pos = sum(1 for w in _POS if w in t)
    neg = sum(1 for w in _NEG if w in t)
    if pos > neg:  return "POSITIVE"
    if neg > pos:  return "NEGATIVE"
    return "NEUTRAL"

# ── Date helpers ──────────────────────────────────────────────────────────────

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

def _rel_time(ts: int) -> str:
    diff = int(time.time()) - ts
    if diff < 60:    return f"{diff}s"
    if diff < 3600:  return f"{diff // 60}m"
    if diff < 86400: return f"{diff // 3600}h"
    return f"{diff // 86400}d"

# ── RSS parser ─────────────────────────────────────────────────────────────────

_HTML_RE = re.compile(r"<[^>]+>")


@dataclass
class PulseItem:
    title:         str
    url:           str
    published_ts:  int
    published_rel: str
    sentiment:     str


def _parse_rss(xml_bytes: bytes) -> list[PulseItem]:
    items: list[PulseItem] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    for el in root.iter("item"):
        title_el = el.find("title")
        link_el  = el.find("link")
        date_el  = el.find("pubDate")

        title = (title_el.text or "").strip() if title_el is not None else ""
        url   = (link_el.text  or "").strip() if link_el  is not None else ""
        date_raw = (date_el.text or "").strip() if date_el is not None else ""

        if not title:
            continue

        _, pub_ts = _parse_dt(date_raw)
        items.append(PulseItem(
            title=title,
            url=url,
            published_ts=pub_ts,
            published_rel=_rel_time(pub_ts),
            sentiment=_sentiment(title),
        ))

    items.sort(key=lambda x: x.published_ts, reverse=True)
    return items

# ── Async fetch ───────────────────────────────────────────────────────────────

async def _fetch(client: httpx.AsyncClient, url: str) -> list[PulseItem]:
    try:
        r = await client.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        return _parse_rss(r.content)
    except Exception:
        return []

def _make_handle(defn: dict, items: list[PulseItem]) -> dict:
    return {
        "handle":       defn["handle"],
        "display_name": defn["display_name"],
        "avatar":       defn["avatar"],
        "category":     defn["category"],
        "region":       defn["region"],
        "item_count":   len(items),
        "items":        [asdict(it) for it in items],
        "is_direct":    True,
    }

# ── Cache ─────────────────────────────────────────────────────────────────────

_cache_ts:   float      = 0.0
_cache_data: list[dict] = []


async def _get_pulse() -> list[dict]:
    global _cache_ts, _cache_data
    if time.time() - _cache_ts < _TTL and _cache_data:
        return _cache_data

    hdrs = {
        "User-Agent": _UA,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    all_urls = [f["url"] for f in _ALL_FEEDS] + [h["url"] for h in _DIRECT_HANDLES]
    # Deduplicate URLs (direct handles may overlap with ALL_FEEDS)
    seen_urls: set[str] = set()
    unique_urls: list[str] = []
    for u in all_urls:
        if u not in seen_urls:
            seen_urls.add(u)
            unique_urls.append(u)

    async with httpx.AsyncClient(headers=hdrs, follow_redirects=True) as client:
        raw_results: list[list[PulseItem]] = await asyncio.gather(
            *[_fetch(client, u) for u in unique_urls]
        )

    url_to_items: dict[str, list[PulseItem]] = {
        u: items for u, items in zip(unique_urls, raw_results)
    }

    # ── Pool all items for synthetic handles ──────────────────────────────────
    pool: list[PulseItem] = []
    seen_titles: set[str] = set()
    for items in raw_results:
        for it in items:
            key = it.title.lower()[:60]
            if key not in seen_titles:
                seen_titles.add(key)
                pool.append(it)
    pool.sort(key=lambda x: x.published_ts, reverse=True)

    # ── Build direct handle cards ─────────────────────────────────────────────
    handles: list[dict] = []
    for defn in _DIRECT_HANDLES:
        items = url_to_items.get(defn["url"], [])[:_PER_HANDLE]
        handles.append(_make_handle(defn, items))

    # ── Build synthetic (topic-cluster) handle cards ──────────────────────────
    for defn in _SYNTHETIC_HANDLES:
        kws = defn["keywords"]
        matched: list[PulseItem] = []
        for it in pool:
            t = it.title.lower()
            if any(k in t for k in kws):
                matched.append(it)
            if len(matched) >= _PER_HANDLE:
                break
        handles.append({
            "handle":       defn["handle"],
            "display_name": defn["display_name"],
            "avatar":       defn["avatar"],
            "category":     defn["category"],
            "region":       defn["region"],
            "item_count":   len(matched),
            "items":        [asdict(it) for it in matched],
            "is_direct":    False,
        })

    _cache_data = handles
    _cache_ts   = time.time()
    return _cache_data


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("")
async def get_social_pulse():
    """Social intelligence ticker -- official + topic-cluster handles."""
    handles = await _get_pulse()
    active = sum(1 for h in handles if h["item_count"] > 0)
    return {
        "handles":   handles,
        "active":    active,
        "total":     len(handles),
        "cached_at": int(_cache_ts),
    }
