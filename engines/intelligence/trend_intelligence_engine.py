"""
Trend Intelligence Engine -- Phase H
Fetches Google Trends interest data for all 50 theme keywords (India geo, weekly).
Produces a trend_score per theme that feeds into theme_intelligence and consensus.

Run:
    py -3.11 engines/intelligence/trend_intelligence_engine.py

Output:
    data/intelligence/trend_scores.csv   -- per-theme trend score + direction

Guardrails: G-A-01 rate limiting (1.5s between batches), G-A-02 retry+backoff,
            G-D-02 atomic writes, G-D-03 no empty df
"""

import json
import shutil
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT_PATH  = cfg.INTELLIGENCE_DIR / "trend_scores.csv"
CACHE_PATH   = cfg.INTELLIGENCE_DIR / "trend_cache.json"
BATCH_SIZE   = 5          # Google Trends max keywords per query
SLEEP_BATCH  = 2.0        # seconds between batches (rate limit)
SLEEP_RETRY  = 8.0        # seconds on 429
MAX_RETRIES  = 3
GEO          = "IN"       # India
TIMEFRAME    = "now 3-m"  # last 3 months (weekly granularity)

# --------------------------------------------------------------------------
# Theme → Google Trends keyword mapping (India-specific search terms)
# --------------------------------------------------------------------------
THEME_KEYWORDS: dict[str, str] = {
    "CAPEX_CYCLE":             "capex India stocks",
    "DIGITAL_INDIA":           "digital India technology",
    "AI_ENABLERS":             "AI artificial intelligence India stocks",
    "DATA_CENTRE":             "data centre India",
    "POWER_TD":                "power transmission India",
    "GREEN_ENERGY":            "renewable energy India stocks",
    "RAILWAYS_METRO":          "railways metro India stocks",
    "DEFENCE_ELECTRONICS":     "defence stocks India",
    "EV_TRANSITION":           "electric vehicle EV India",
    "BANKING_CREDIT":          "banking stocks India NIFTY BANK",
    "EXPORT_GROWTH":           "export growth India",
    "CHINA_PLUS_ONE":          "China plus one India manufacturing",
    "HEALTHCARE_EXPANSION":    "pharma healthcare India stocks",
    "SPECIALTY_CHEM":          "specialty chemicals India",
    "INFRASTRUCTURE_BUILD":    "infrastructure India stocks",
    "GREEN_HYDROGEN":          "green hydrogen India",
    "BATTERY_STORAGE":         "battery storage India",
    "SEMICONDUCTOR":           "semiconductor India chip",
    "INDIA_PLUS_ONE":          "Make in India manufacturing",
    "COMMODITY_SUPER":         "commodity metals India stocks",
    "FINANCIALISATION":        "mutual fund SIP India",
    "RURAL_CONSUMPTION":       "rural consumption FMCG India",
    "PREMIUMISATION":          "premium consumer durables India",
    "REAL_ESTATE_RECOVERY":    "real estate property India stocks",
    "LOGISTICS_MODERNISATION": "logistics warehousing India",
    "PSU_REVIVAL":             "PSU CPSE stocks India",
    "INTEREST_RATE_CYCLE":     "RBI repo rate India",
    "MONSOON_AGRI":            "monsoon agriculture India",
    "SMART_CITIES":            "smart city India",
    "SPACE_ECONOMY":           "ISRO space economy India",
    "AGRITECH":                "agritech farming India",
    "GAMING_ESPORTS":          "gaming esports India stocks",
    "GOLD_JEWELLERY":          "gold jewellery India stocks",
    "TOURISM_HOSP":            "tourism hotel hospitality India",
    "MEDIA_ENTERTAIN":         "OTT streaming media India",
    "MICROFINANCE":            "microfinance MFI India",
    "INSURANCE_GROWTH":        "insurance stocks India LIC",
    "WEALTH_MGMT":             "wealth management India stocks",
    "FINTECH_INFRASTR":        "fintech payments India",
    "HEALTHTECH":              "health tech digital health India",
    "QUICK_COMMERCE":          "quick commerce 10 minute delivery India",
    "CYBERSECURITY":           "cybersecurity India stocks",
    "WATER_MANAGEMENT":        "water management India stocks",
    "PORTS_SHIPPING":          "ports shipping India stocks",
    "LARGECAP_VALUE":          "Nifty 50 largecap India",
    "MIDCAP_MOMENTUM":         "midcap stocks India NIFTY MIDCAP",
    "SMALLCAP_QUALITY":        "smallcap stocks India",
    "DIVIDEND_YIELD":          "dividend stocks India yield",
    "QUALITY_GROWTH":          "quality growth stocks India",
    "TURNAROUND":              "turnaround stocks India recovery",
}


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict):
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache))
    shutil.move(str(tmp), str(CACHE_PATH))


def _fetch_batch(pytrends, keywords: list[str]) -> dict[str, dict]:
    """
    Fetches interest_over_time for a batch of keywords (max 5).
    Returns {keyword: {interest_now, interest_4w_avg, interest_12w_avg}}.
    """
    results: dict[str, dict] = {}
    for attempt in range(MAX_RETRIES):
        try:
            pytrends.build_payload(
                kw_list=keywords,
                cat=0,
                timeframe=TIMEFRAME,
                geo=GEO,
            )
            df = pytrends.interest_over_time()
            if df.empty:
                logger.warning("[TrendEngine] Empty response for batch %s", keywords)
                return {k: {} for k in keywords}

            for kw in keywords:
                if kw not in df.columns:
                    results[kw] = {}
                    continue
                series = df[kw].astype(float)
                now_val   = float(series.iloc[-1])
                avg_4w    = float(series.iloc[-4:].mean())  if len(series) >= 4  else now_val
                avg_12w   = float(series.mean())
                results[kw] = {
                    "interest_now":    round(now_val, 1),
                    "interest_4w_avg": round(avg_4w, 1),
                    "interest_12w_avg": round(avg_12w, 1),
                }
            return results

        except Exception as ex:
            msg = str(ex).lower()
            wait = SLEEP_RETRY * (2 ** attempt)
            if "429" in msg or "too many" in msg:
                logger.warning("[TrendEngine] Rate limited, sleeping %ss", wait)
                time.sleep(wait)
            else:
                logger.warning("[TrendEngine] Batch %s attempt %d failed: %s", keywords, attempt + 1, ex)
                time.sleep(SLEEP_RETRY)

    return {k: {} for k in keywords}


def _trend_direction(now_val: float, avg_12w: float) -> str:
    if avg_12w < 1:
        return "STABLE"
    delta_pct = (now_val - avg_12w) / avg_12w * 100
    if delta_pct >= 20:
        return "RISING"
    if delta_pct <= -20:
        return "FALLING"
    return "STABLE"


def _trend_score(now_val: float, direction: str) -> float:
    """Combine raw interest (0-100) with direction momentum into a 0-100 score."""
    base = now_val
    if direction == "RISING":
        base = min(100, base * 1.15)
    elif direction == "FALLING":
        base = max(0, base * 0.85)
    return round(base, 1)


def run() -> pd.DataFrame | None:
    logger.info("[TrendEngine] Phase H Google Trends intelligence starting")

    try:
        from pytrends.request import TrendReq
    except ImportError:
        logger.error("[TrendEngine] pytrends not installed -- run: py -3.11 -m pip install pytrends")
        print("[TrendEngine] ERROR: install pytrends first")
        return None

    pytrends = TrendReq(hl="en-US", tz=330, timeout=(10, 25), retries=2, backoff_factor=1.5)

    cache = _load_cache()
    today_str = date.today().isoformat()
    cache_key = f"week_{date.today().isocalendar()[1]}_{date.today().year}"

    # Theme → keyword list
    themes = list(THEME_KEYWORDS.keys())
    keywords_by_theme = {t: THEME_KEYWORDS[t] for t in themes}
    unique_kws = list(set(keywords_by_theme.values()))

    # Skip keywords already cached this week
    pending_kws = [kw for kw in unique_kws if f"{cache_key}:{kw}" not in cache]
    cached_kws  = [kw for kw in unique_kws if f"{cache_key}:{kw}" in cache]
    logger.info("[TrendEngine] %d keywords total -- %d cached, %d to fetch",
                len(unique_kws), len(cached_kws), len(pending_kws))

    # Batch fetch
    kw_results: dict[str, dict] = {}
    # Load cached
    for kw in cached_kws:
        kw_results[kw] = cache[f"{cache_key}:{kw}"]

    # Fetch pending in batches
    batches = [pending_kws[i:i + BATCH_SIZE] for i in range(0, len(pending_kws), BATCH_SIZE)]
    for i, batch in enumerate(batches):
        logger.info("[TrendEngine] Batch %d/%d: %s", i + 1, len(batches), batch)
        batch_res = _fetch_batch(pytrends, batch)
        kw_results.update(batch_res)
        # Cache successful results
        for kw, data in batch_res.items():
            if data:
                cache[f"{cache_key}:{kw}"] = data
        time.sleep(SLEEP_BATCH)

    _save_cache(cache)

    # Build output rows per theme
    rows = []
    for theme, kw in keywords_by_theme.items():
        data = kw_results.get(kw, {})
        if not data:
            # Use zeros for missing (avoid NaN in downstream)
            rows.append({
                "theme":            theme,
                "keyword":          kw,
                "interest_now":     0.0,
                "interest_4w_avg":  0.0,
                "interest_12w_avg": 0.0,
                "trend_direction":  "STABLE",
                "trend_score":      0.0,
                "data_available":   False,
                "as_of_date":       today_str,
            })
            continue

        now_val   = data["interest_now"]
        avg_4w    = data["interest_4w_avg"]
        avg_12w   = data["interest_12w_avg"]
        direction = _trend_direction(now_val, avg_12w)
        score     = _trend_score(now_val, direction)

        rows.append({
            "theme":            theme,
            "keyword":          kw,
            "interest_now":     now_val,
            "interest_4w_avg":  avg_4w,
            "interest_12w_avg": avg_12w,
            "trend_direction":  direction,
            "trend_score":      score,
            "data_available":   True,
            "as_of_date":       today_str,
        })

    out_df = pd.DataFrame(rows)
    if out_df.empty:
        logger.error("[TrendEngine] No data generated")
        return None

    tmp = OUTPUT_PATH.with_suffix(".tmp")
    out_df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT_PATH))
    logger.info("[TrendEngine] Wrote %d theme trend scores to %s", len(out_df), OUTPUT_PATH)

    # Print summary
    available = out_df[out_df["data_available"]]
    print(f"\n[TrendEngine] Phase H Google Trends complete")
    print(f"  Themes scored     : {len(available)} / {len(out_df)}")
    if not available.empty:
        print(f"  Avg interest now  : {available['interest_now'].mean():.1f}")
        print(f"  Rising themes     : {(available['trend_direction'] == 'RISING').sum()}")
        print(f"  Falling themes    : {(available['trend_direction'] == 'FALLING').sum()}")
        print()
        print("  Top trending themes:")
        top = available.nlargest(10, "trend_score")[["theme", "interest_now", "trend_direction", "trend_score"]]
        for _, r in top.iterrows():
            arrow = "^" if r["trend_direction"] == "RISING" else ("v" if r["trend_direction"] == "FALLING" else "-")
            print(f"    {r['theme']:<30} interest={r['interest_now']:.0f}  {arrow}  score={r['trend_score']:.1f}")

    return out_df


if __name__ == "__main__":
    run()
