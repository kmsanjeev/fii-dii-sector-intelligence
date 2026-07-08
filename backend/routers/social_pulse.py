"""
Social Pulse Router -- X (Twitter) Intelligence Ticker
Scans curated X handles of Indian ministers, G20 leaders, and global market movers
for tweets that can disrupt Indian or global market sentiment.

Fetch path: nitter.net RSS -> fallback nitter instances (no Twitter API key required).
Impact filter: only tweets with market_impact_score >= category threshold surface.

GET /api/social-pulse          -> { handles, active, total, cached_at }
GET /api/social-pulse?refresh  -> force re-fetch (bypasses 15-min cache)
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
from fastapi import APIRouter

log = logging.getLogger("social_pulse")

router = APIRouter(prefix="/api/social-pulse", tags=["social_pulse"])

# ── Config ────────────────────────────────────────────────────────────────────
_UA      = "Mozilla/5.0 (compatible; MarketIntelBot/1.0)"
_TIMEOUT = 12.0
_TTL     = 900    # 15-min cache (tweets move fast)
_PER     = 5      # max tweets per handle to surface

# Nitter instances (tried in order)
_NITTER = [
    "https://nitter.net",
    "https://nitter.poast.org",
    "https://nitter.lucahammer.com",
    "https://nitter.1d4.us",
]

_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Handle Registry (X handles only) ─────────────────────────────────────────
# All entries are X/Twitter accounts.  Company press rooms live in the News section.
# min_score: tweets scoring below this are silently dropped (too low impact).
#   0 = show all (use for regulators where every post is market-relevant)
#   1 = show anything mentioning policy/trade/rates
#   2 = show only high-signal tweets (use for very active handles like elonmusk)

_HANDLES = [
    # ── Indian Government ─────────────────────────────────────────────────────
    {
        "handle": "@narendramodi",  "twitter": "narendramodi",
        "display_name": "PM Modi",
        "avatar": "MOD",  "category": "INDIA_GOVT",      "region": "INDIA",
        "min_score": 1,
        "desc": "PM India -- bilateral deals, infra, economic policy",
    },
    {
        "handle": "@nsitharaman",   "twitter": "nsitharaman",
        "display_name": "FM Sitharaman",
        "avatar": "NST",  "category": "INDIA_GOVT",      "region": "INDIA",
        "min_score": 1,
        "desc": "Finance Minister -- budget, taxes, capital markets",
    },
    {
        "handle": "@PMOIndia",      "twitter": "PMOIndia",
        "display_name": "PMO India",
        "avatar": "PMO",  "category": "INDIA_GOVT",      "region": "INDIA",
        "min_score": 1,
        "desc": "Official PMO statements on policy & economy",
    },
    {
        "handle": "@PiyushGoyal",   "twitter": "PiyushGoyal",
        "display_name": "Min. Goyal",
        "avatar": "PGY",  "category": "INDIA_GOVT",      "region": "INDIA",
        "min_score": 1,
        "desc": "Commerce & Industry Minister -- trade deals, FDI, exports",
    },
    {
        "handle": "@nitin_gadkari", "twitter": "nitin_gadkari",
        "display_name": "Min. Gadkari",
        "avatar": "GDK",  "category": "INDIA_GOVT",      "region": "INDIA",
        "min_score": 1,
        "desc": "Roads/Transport Minister -- infra projects, EV policy",
    },
    {
        "handle": "@DrSJaishankar", "twitter": "DrSJaishankar",
        "display_name": "EAM Jaishankar",
        "avatar": "EAM",  "category": "INDIA_GOVT",      "region": "INDIA",
        "min_score": 1,
        "desc": "External Affairs -- geopolitics affecting India",
    },
    # ── Indian Regulators ────────────────────────────────────────────────────
    {
        "handle": "@SEBI_India",    "twitter": "SEBI_India",
        "display_name": "SEBI",
        "avatar": "SBI",  "category": "INDIA_REGULATOR", "region": "INDIA",
        "min_score": 0,   # all SEBI posts are market-relevant
        "desc": "Markets regulator -- circulars, F&O rules, listing norms",
    },
    {
        "handle": "@RBI",           "twitter": "RBI",
        "display_name": "RBI",
        "avatar": "RBI",  "category": "INDIA_REGULATOR", "region": "INDIA",
        "min_score": 0,   # all RBI posts are market-relevant
        "desc": "Monetary policy, repo rate, rupee, banking sector",
    },
    # ── G20 Leaders & Global Market Movers ───────────────────────────────────
    {
        "handle": "@POTUS",          "twitter": "POTUS",
        "display_name": "US President",
        "avatar": "US",   "category": "G20_LEADER",      "region": "GLOBAL",
        "min_score": 1,
        "desc": "US President -- tariffs, sanctions, India-US trade",
    },
    {
        "handle": "@realDonaldTrump","twitter": "realDonaldTrump",
        "display_name": "Donald Trump",
        "avatar": "DJT",  "category": "G20_LEADER",      "region": "GLOBAL",
        "min_score": 1,
        "desc": "Tariffs, crypto, geopolitics -- major market mover",
    },
    {
        "handle": "@elonmusk",       "twitter": "elonmusk",
        "display_name": "Elon Musk",
        "avatar": "ELN",  "category": "G20_LEADER",      "region": "GLOBAL",
        "min_score": 2,   # very active -- filter harder
        "desc": "Tesla, SpaceX, DOGE, AI, crypto -- enormous market-moving handle",
    },
    # ── Multilateral / Economic Bodies ───────────────────────────────────────
    {
        "handle": "@IMFNews",        "twitter": "IMFNews",
        "display_name": "IMF",
        "avatar": "IMF",  "category": "MULTILATERAL",    "region": "GLOBAL",
        "min_score": 1,
        "desc": "Global outlook, India GDP forecasts, currency, debt",
    },
    {
        "handle": "@NATO",           "twitter": "NATO",
        "display_name": "NATO",
        "avatar": "NAT",  "category": "GEOPOLITICAL",    "region": "GLOBAL",
        "min_score": 1,
        "desc": "Military alliances, conflict signals -- crude oil, defense stocks",
    },
]

# ── Market Impact Scorer ──────────────────────────────────────────────────────
# Score  2 per HIGH keyword, 1 per MED keyword.
# High-negative → NEGATIVE sentiment; High-positive → POSITIVE; else NEUTRAL.

_HIGH_NEG = frozenset({
    "war", "attack", "missile", "bomb", "nuclear", "sanction", "sanctions",
    "ban", "crisis", "recession", "collapse", "default", "blockade",
    "terror", "conflict", "invasion", "escalation", "strike", "ceasefire",
    "coup", "assassination", "arrested", "detained",
})
_HIGH_POS = frozenset({
    "deal", "agreement", "signed", "treaty", "invest", "investment",
    "reform", "stimulus", "alliance", "partnership", "bilateral",
    "cooperation", "fdi", "approved", "launch", "boost", "record",
})
_MED = frozenset({
    "tariff", "tariffs", "rate", "rates", "inflation", "gdp", "policy",
    "budget", "trade", "rupee", "dollar", "crude", "oil", "interest",
    "growth", "export", "import", "subsidy", "tax", "regulation",
    "rbi", "sebi", "fed", "central bank", "monetary", "fiscal",
    "debt", "deficit", "banking", "market", "economy", "economic",
    "jobs", "employment", "unemployment", "supply chain",
})


def _score(text: str) -> int:
    t = text.lower()
    return (sum(2 for w in _HIGH_NEG if w in t) +
            sum(2 for w in _HIGH_POS if w in t) +
            sum(1 for w in _MED if w in t))


def _sentiment(text: str) -> str:
    t = text.lower()
    neg = sum(1 for w in _HIGH_NEG if w in t)
    pos = sum(1 for w in _HIGH_POS if w in t)
    if pos > neg:  return "POSITIVE"
    if neg > pos:  return "NEGATIVE"
    return "NEUTRAL"

# ── Date helpers ──────────────────────────────────────────────────────────────

def _parse_dt(raw: str) -> int:
    if not raw:
        return int(time.time())
    try:
        return int(parsedate_to_datetime(raw).timestamp())
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return int(datetime.strptime(raw, fmt).timestamp())
        except Exception:
            pass
    return int(time.time())


def _rel(ts: int) -> str:
    d = int(time.time()) - ts
    if d < 60:    return f"{d}s"
    if d < 3600:  return f"{d // 60}m"
    if d < 86400: return f"{d // 3600}h"
    return f"{d // 86400}d"

# ── Nitter RSS parser ─────────────────────────────────────────────────────────

_HTML = re.compile(r"<[^>]+>")
# Patterns to skip
_SKIP_RE = re.compile(r"^Pinned:\s*", re.IGNORECASE)
# Prefix cleaner: "R: " or "RT by @handle: " at start of title
_RT_PREFIX = re.compile(r"^R(?:T by @\w+)?:\s*", re.IGNORECASE)


@dataclass
class TweetItem:
    title:         str
    url:           str
    published_ts:  int
    published_rel: str
    sentiment:     str
    impact_score:  int


def _strip(s: str) -> str:
    return _HTML.sub("", s or "").strip()


def _parse_nitter(xml_bytes: bytes, min_score: int) -> list[TweetItem]:
    items: list[TweetItem] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    for el in root.iter("item"):
        te = el.find("title")
        raw = _strip(te.text or "") if te is not None else ""
        if not raw or _SKIP_RE.match(raw):
            continue

        # Clean "R: " / "RT by @handle: " prefix from nitter titles
        title = _RT_PREFIX.sub("", raw).strip()
        if not title:
            continue

        le = el.find("link")
        url = (_strip(le.text or "") if le is not None else "")

        de = el.find("pubDate")
        ts = _parse_dt((de.text or "").strip() if de is not None else "")

        impact = _score(title)
        if impact < min_score:
            continue

        items.append(TweetItem(
            title=title,
            url=url,
            published_ts=ts,
            published_rel=_rel(ts),
            sentiment=_sentiment(title),
            impact_score=impact,
        ))

    items.sort(key=lambda x: x.published_ts, reverse=True)
    return items

# ── Nitter fetch with instance fallback ──────────────────────────────────────

def _fetch_x(h: dict) -> dict:
    """Fetch tweets for a single X handle via nitter RSS (sync, thread-safe)."""
    twitter = h["twitter"]
    min_sc  = h.get("min_score", 1)
    hdrs    = {
        "User-Agent": _UA,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    items: list[TweetItem] = []
    fetched = False

    for instance in _NITTER:
        url = f"{instance}/{twitter}/rss"
        for attempt in range(2):
            try:
                if attempt:
                    time.sleep(0.5)
                with httpx.Client(headers=hdrs, follow_redirects=True,
                                  timeout=_TIMEOUT) as client:
                    r = client.get(url)
                if r.status_code == 429:
                    break          # rate-limited on this instance, try next
                r.raise_for_status()
                items   = _parse_nitter(r.content, min_sc)[:_PER]
                fetched = True
                break
            except Exception as exc:
                last = f"{type(exc).__name__}: {exc}"
                continue
        if fetched:
            break

    if not fetched:
        try:
            log.warning("social_pulse FAIL %s: all nitter instances failed", h["handle"])
        except Exception:
            pass

    return {
        "handle":       h["handle"],
        "display_name": h["display_name"],
        "avatar":       h["avatar"],
        "category":     h["category"],
        "region":       h["region"],
        "desc":         h.get("desc", ""),
        "item_count":   len(items),
        "items":        [asdict(it) for it in items],
        "is_x":         True,
    }

# ── Cache & thread pool ───────────────────────────────────────────────────────

_cache_ts:   float      = 0.0
_cache_data: list[dict] = []
_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=16)


async def _get_pulse() -> list[dict]:
    global _cache_ts, _cache_data
    if time.time() - _cache_ts < _TTL and _cache_data:
        return _cache_data

    loop    = asyncio.get_running_loop()
    futures = [loop.run_in_executor(_POOL, _fetch_x, h) for h in _HANDLES]
    results = list(await asyncio.gather(*futures))

    _cache_data = results
    _cache_ts   = time.time()
    return _cache_data

# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("")
async def get_social_pulse(refresh: bool = False):
    """X (Twitter) intelligence ticker: Indian ministers, G20 leaders, global movers.
    Only surfaces tweets with market impact score above per-handle threshold.
    Pass ?refresh=true to force a cache bypass."""
    global _cache_ts
    if refresh:
        _cache_ts = 0.0
    handles = await _get_pulse()
    active  = sum(1 for h in handles if h["item_count"] > 0)
    return {
        "handles":   handles,
        "active":    active,
        "total":     len(handles),
        "cached_at": int(_cache_ts),
    }
