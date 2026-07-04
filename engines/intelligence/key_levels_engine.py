"""
Key Levels Engine  —  Phase KL
Computes institutional-grade support/resistance levels for every cached symbol.

Methods (9):
  1. Monthly Pivot Points   (PP, R1-R3, S1-S3)
  2. Weekly Pivot Points    (PP, R1-R2, S1-S2)
  3. Fibonacci Retracements (23.6%, 38.2%, 50%, 61.8%, 78.6% from 52W range)
  4. ATR(14)                (Average True Range — adaptive stop basis)
  5. Swing Highs/Lows       (N=5 bar pivot detection, last 2 each)
  6. Volume Profile POC     (Point of Control — 30-bin, 126-day histogram)
  7. Round Number Levels    (nearest major round above/below)
  8. Previous Week H/L
  9. Previous Month H/L

Confluence scoring:
  Each candidate level carries a method weight (1-3).
  Levels within ±1.5% are grouped into clusters.
  Top-2 clusters above price → resistance; top-2 below → support.
  Tags stored as pipe-separated strings for easy UI rendering.

Output: data/intelligence/key_levels.csv
Run:    py -3.11 -m engines.intelligence.key_levels_engine
"""

import shutil
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT  = cfg.INTELLIGENCE_DIR / "key_levels.csv"
CACHE   = cfg.STOCK_HISTORY_CACHE
TECH_F  = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"

LOOKBACK_SWING = 252   # ~1 trading year for swing detection
LOOKBACK_VOL   = 126   # ~6 months for volume profile
ATR_PERIOD     = 14
SWING_N        = 5     # bars before/after for swing pivot detection
VOL_BINS       = 30    # price bins for volume profile
CONF_BAND      = 0.015 # ±1.5% confluence cluster band

# ── Method weights (higher = more institutional significance) ─────────────────
WEIGHTS: dict[str, int] = {
    "dma_200":      3,
    "fib_618":      3,
    "vol_poc":      3,
    "mp_pp":        3,
    "mp_s1":        3,
    "mp_r1":        3,
    "fib_500":      2,
    "fib_382":      2,
    "swing_high":   2,
    "swing_low":    2,
    "mp_s2":        2,
    "mp_r2":        2,
    "wp_pp":        2,
    "wp_s1":        2,
    "wp_r1":        2,
    "52w_high":     2,
    "52w_low":      2,
    "dma_50":       1,
    "dma_20":       1,
    "fib_786":      1,
    "fib_236":      1,
    "mp_s3":        1,
    "mp_r3":        1,
    "wp_s2":        1,
    "wp_r2":        1,
    "prev_month_h": 1,
    "prev_month_l": 1,
    "prev_week_h":  1,
    "prev_week_l":  1,
    "round_num":    1,
}

# Human-readable labels for each method tag
LABELS: dict[str, str] = {
    "dma_200":      "200 DMA",
    "dma_50":       "50 DMA",
    "dma_20":       "20 DMA",
    "fib_786":      "Fib 78.6%",
    "fib_618":      "Fib 61.8%",
    "fib_500":      "Fib 50%",
    "fib_382":      "Fib 38.2%",
    "fib_236":      "Fib 23.6%",
    "vol_poc":      "Vol POC",
    "mp_pp":        "M-Pivot",
    "mp_r1":        "M-R1",
    "mp_r2":        "M-R2",
    "mp_r3":        "M-R3",
    "mp_s1":        "M-S1",
    "mp_s2":        "M-S2",
    "mp_s3":        "M-S3",
    "wp_pp":        "W-Pivot",
    "wp_r1":        "W-R1",
    "wp_r2":        "W-R2",
    "wp_s1":        "W-S1",
    "wp_s2":        "W-S2",
    "swing_high":   "Swing Hi",
    "swing_low":    "Swing Lo",
    "52w_high":     "52W High",
    "52w_low":      "52W Low",
    "prev_month_h": "Prev-Mo Hi",
    "prev_month_l": "Prev-Mo Lo",
    "prev_week_h":  "Prev-Wk Hi",
    "prev_week_l":  "Prev-Wk Lo",
    "round_num":    "Round",
}


# ── Computation helpers ───────────────────────────────────────────────────────

def _atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> Optional[float]:
    """ATR from last `period` rows. Requires columns: high, low, close."""
    if len(df) < period + 1:
        return None
    tail = df.tail(period + 1).copy()
    tr = pd.concat([
        tail["high"] - tail["low"],
        (tail["high"] - tail["close"].shift(1)).abs(),
        (tail["low"]  - tail["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    return float(tr.iloc[1:].mean())


def _pivots(h: float, l: float, c: float) -> dict[str, float]:
    """Classic floor-trader pivot points from period OHLC."""
    pp = (h + l + c) / 3
    r1 = 2 * pp - l
    r2 = pp + (h - l)
    r3 = h + 2 * (pp - l)
    s1 = 2 * pp - h
    s2 = pp - (h - l)
    s3 = l - 2 * (h - pp)
    return {"pp": pp, "r1": r1, "r2": r2, "r3": r3, "s1": s1, "s2": s2, "s3": s3}


def _fibonacci(low: float, high: float) -> dict[str, float]:
    """Fibonacci retracement levels from swing range."""
    rng = high - low
    return {
        "786": round(high - 0.786 * rng, 2),
        "618": round(high - 0.618 * rng, 2),
        "500": round(high - 0.500 * rng, 2),
        "382": round(high - 0.382 * rng, 2),
        "236": round(high - 0.236 * rng, 2),
    }


def _swing_points(df: pd.DataFrame, n: int = SWING_N) -> tuple[list[float], list[float]]:
    """
    Detect swing highs/lows using N-bar pivot rule.
    Returns (swing_highs, swing_lows) sorted most-recent first.
    """
    highs, lows = [], []
    arr_h = df["high"].values
    arr_l = df["low"].values
    for i in range(n, len(df) - n):
        if arr_h[i] == max(arr_h[i - n: i + n + 1]):
            highs.append(float(arr_h[i]))
        if arr_l[i] == min(arr_l[i - n: i + n + 1]):
            lows.append(float(arr_l[i]))
    # Return last 2 unique values, highest first for highs, lowest first for lows
    sh = sorted(set(highs), reverse=True)[:2]
    sl = sorted(set(lows))[:2]
    return sh, sl


def _volume_poc(df: pd.DataFrame, bins: int = VOL_BINS) -> Optional[float]:
    """
    Daily volume-profile Point of Control.
    Uses typical price (H+L+C)/3 weighted by volume to find the price level
    with the highest cumulative volume.
    """
    if len(df) < 10 or "volume" not in df.columns:
        return None
    tail = df.tail(LOOKBACK_VOL).copy()
    tail = tail[tail["volume"] > 0].copy()
    if tail.empty:
        return None
    typ = (tail["high"] + tail["low"] + tail["close"]) / 3
    lo, hi = typ.min(), typ.max()
    if hi <= lo:
        return None
    bin_edges = np.linspace(lo, hi, bins + 1)
    bin_idx = np.digitize(typ.values, bin_edges) - 1
    bin_idx = np.clip(bin_idx, 0, bins - 1)
    vol_at_bin = np.zeros(bins)
    for i, vol in zip(bin_idx, tail["volume"].values):
        vol_at_bin[i] += vol
    poc_bin = int(np.argmax(vol_at_bin))
    poc_price = (bin_edges[poc_bin] + bin_edges[poc_bin + 1]) / 2
    return round(float(poc_price), 2)


def _round_levels(price: float) -> tuple[float, float]:
    """Nearest major round number above and below price."""
    if price <= 0:
        return price, price
    # Determine step based on magnitude
    if price >= 5000:
        step = 500
    elif price >= 2000:
        step = 250
    elif price >= 1000:
        step = 100
    elif price >= 500:
        step = 50
    elif price >= 100:
        step = 25
    elif price >= 50:
        step = 10
    else:
        step = 5
    sup = (price // step) * step
    res = sup + step
    if sup == price:
        sup -= step
    return round(res, 2), round(sup, 2)


def _period_ohlc(df: pd.DataFrame, period: str) -> Optional[dict]:
    """
    Aggregate OHLCV to period frequency (ME=monthly, W=weekly) and
    return the PREVIOUS complete period's H, L, C.
    """
    if df.empty:
        return None
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["date"])
    tmp = tmp.set_index("date").sort_index()
    agg = tmp.resample(period).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna(subset=["close"])
    # Drop the last incomplete period; use the second-to-last complete one
    if len(agg) < 2:
        return None
    prev = agg.iloc[-2]
    return {"h": float(prev["high"]), "l": float(prev["low"]), "c": float(prev["close"])}


# ── Confluence engine ─────────────────────────────────────────────────────────

def _confluence(candidates: list[tuple[float, str]], current: float) -> dict:
    """
    Group candidate levels into clusters (±CONF_BAND), score each cluster,
    return top-2 support and top-2 resistance clusters with tags.

    candidates: list of (price, method_key) tuples
    Returns dict with keys: sup1, sup1_score, sup1_tags, sup2, ..., res1, ...
    """
    above = [(p, k) for p, k in candidates if p > current * (1 + 0.002)]
    below = [(p, k) for p, k in candidates if p < current * (1 - 0.002)]

    def cluster(items: list[tuple[float, str]], descending: bool) -> list[dict]:
        if not items:
            return []
        # Sort by price
        srt = sorted(items, key=lambda x: x[0])
        clusters: list[dict] = []
        cur_cluster: dict = {"prices": [srt[0][0]], "methods": [srt[0][1]]}
        for price, method in srt[1:]:
            ref = np.mean(cur_cluster["prices"])
            if ref != 0 and abs(price - ref) / ref <= CONF_BAND:
                cur_cluster["prices"].append(price)
                cur_cluster["methods"].append(method)
            else:
                clusters.append(cur_cluster)
                cur_cluster = {"prices": [price], "methods": [method]}
        clusters.append(cur_cluster)

        # Score each cluster
        scored = []
        for cl in clusters:
            price = round(float(np.mean(cl["prices"])), 2)
            score = sum(WEIGHTS.get(m, 1) for m in cl["methods"])
            tags  = "|".join(LABELS.get(m, m) for m in cl["methods"])
            scored.append({"price": price, "score": score, "tags": tags})

        scored.sort(key=lambda x: x["score"], reverse=True)
        # For resistance: want closest levels above (lowest price first among top)
        # For support: want closest levels below (highest price first)
        return scored

    res_clusters = sorted(cluster(above, descending=False), key=lambda x: x["price"])[:4]
    res_clusters.sort(key=lambda x: x["score"], reverse=True)

    sup_clusters = sorted(cluster(below, descending=True), key=lambda x: x["price"], reverse=True)[:4]
    sup_clusters.sort(key=lambda x: x["score"], reverse=True)

    def _get(lst, idx, key, default=None):
        try:
            return lst[idx][key]
        except (IndexError, KeyError):
            return default

    return {
        "res_1":       _get(res_clusters, 0, "price"),
        "res_1_score": _get(res_clusters, 0, "score", 0),
        "res_1_tags":  _get(res_clusters, 0, "tags", ""),
        "res_2":       _get(res_clusters, 1, "price"),
        "res_2_score": _get(res_clusters, 1, "score", 0),
        "res_2_tags":  _get(res_clusters, 1, "tags", ""),
        "sup_1":       _get(sup_clusters, 0, "price"),
        "sup_1_score": _get(sup_clusters, 0, "score", 0),
        "sup_1_tags":  _get(sup_clusters, 0, "tags", ""),
        "sup_2":       _get(sup_clusters, 1, "price"),
        "sup_2_score": _get(sup_clusters, 1, "score", 0),
        "sup_2_tags":  _get(sup_clusters, 1, "tags", ""),
    }


# ── Per-symbol computation ────────────────────────────────────────────────────

def _compute_symbol(symbol: str, tech_row: Optional[pd.Series]) -> Optional[dict]:
    """Compute all key levels for one symbol. Returns flat dict or None."""
    try:
        pq = CACHE / f"{symbol}.parquet"
        if not pq.exists():
            return None

        df = pd.read_parquet(pq)
        df = df.sort_values("date").reset_index(drop=True)

        if len(df) < ATR_PERIOD + 2:
            return None

        close = float(df["close"].iloc[-1])
        if close <= 0:
            return None

        as_of = str(df["date"].iloc[-1])[:10]

        # ── ATR(14) ───────────────────────────────────────────────────────────
        atr = _atr(df)
        if atr is None:
            atr = close * 0.02  # fallback: 2% of price

        # ── Monthly Pivot ──────────────────────────────────────────────────────
        mo = _period_ohlc(df, "ME")
        mp: dict[str, Optional[float]] = {k: None for k in ("pp","r1","r2","r3","s1","s2","s3")}
        if mo:
            mp = _pivots(mo["h"], mo["l"], mo["c"])

        # ── Weekly Pivot ───────────────────────────────────────────────────────
        wk = _period_ohlc(df, "W-FRI")
        wp: dict[str, Optional[float]] = {k: None for k in ("pp","r1","r2","s1","s2")}
        if wk:
            p = _pivots(wk["h"], wk["l"], wk["c"])
            wp = {k: p[k] for k in ("pp", "r1", "r2", "s1", "s2")}

        # ── 52W High/Low from technical_indicators ─────────────────────────────
        if tech_row is not None:
            h52 = float(tech_row.get("high_52w", 0) or 0)
            l52 = float(tech_row.get("low_52w", 0) or 0)
            dma20  = tech_row.get("dma_20")
            dma50  = tech_row.get("dma_50")
            dma200 = tech_row.get("dma_200")
        else:
            tail_252 = df.tail(252)
            h52  = float(tail_252["high"].max())
            l52  = float(tail_252["low"].min())
            dma20 = dma50 = dma200 = None

        dma20  = float(dma20)  if dma20  is not None and not np.isnan(float(dma20 or 0))  else None
        dma50  = float(dma50)  if dma50  is not None and not np.isnan(float(dma50 or 0))  else None
        dma200 = float(dma200) if dma200 is not None and not np.isnan(float(dma200 or 0)) else None

        # ── Fibonacci Retracements ─────────────────────────────────────────────
        fib: dict[str, Optional[float]] = {k: None for k in ("786","618","500","382","236")}
        if h52 > 0 and l52 > 0 and h52 > l52:
            fib = _fibonacci(l52, h52)

        # ── Swing Highs/Lows (last 252 bars) ──────────────────────────────────
        swing_df = df.tail(LOOKBACK_SWING).reset_index(drop=True)
        swing_highs, swing_lows = _swing_points(swing_df)
        sh1 = swing_highs[0] if len(swing_highs) > 0 else None
        sh2 = swing_highs[1] if len(swing_highs) > 1 else None
        sl1 = swing_lows[0]  if len(swing_lows)  > 0 else None
        sl2 = swing_lows[1]  if len(swing_lows)  > 1 else None

        # ── Volume Profile POC ─────────────────────────────────────────────────
        poc = _volume_poc(df)

        # ── Round Numbers ──────────────────────────────────────────────────────
        round_res, round_sup = _round_levels(close)

        # ── Previous Week / Month H/L ──────────────────────────────────────────
        pw_h = pw_l = pm_h = pm_l = None
        if wk:
            pw_h, pw_l = wk["h"], wk["l"]
        if mo:
            pm_h, pm_l = mo["h"], mo["l"]

        # ── ATR-based levels ───────────────────────────────────────────────────
        stop_1atr  = round(close - 1.0 * atr, 2)
        stop_2atr  = round(close - 2.0 * atr, 2)
        tgt_1atr   = round(close + 1.0 * atr, 2)
        tgt_2atr   = round(close + 2.0 * atr, 2)

        # ── Build candidate list for confluence ────────────────────────────────
        candidates: list[tuple[float, str]] = []

        def _add(price, method):
            if price and price > 0 and not np.isnan(float(price)):
                candidates.append((round(float(price), 2), method))

        # Fibonacci
        _add(fib.get("786"), "fib_786")
        _add(fib.get("618"), "fib_618")
        _add(fib.get("500"), "fib_500")
        _add(fib.get("382"), "fib_382")
        _add(fib.get("236"), "fib_236")

        # Monthly Pivots
        _add(mp.get("pp"),  "mp_pp")
        _add(mp.get("r1"),  "mp_r1")
        _add(mp.get("r2"),  "mp_r2")
        _add(mp.get("r3"),  "mp_r3")
        _add(mp.get("s1"),  "mp_s1")
        _add(mp.get("s2"),  "mp_s2")
        _add(mp.get("s3"),  "mp_s3")

        # Weekly Pivots
        _add(wp.get("pp"),  "wp_pp")
        _add(wp.get("r1"),  "wp_r1")
        _add(wp.get("r2"),  "wp_r2")
        _add(wp.get("s1"),  "wp_s1")
        _add(wp.get("s2"),  "wp_s2")

        # DMAs
        _add(dma20,  "dma_20")
        _add(dma50,  "dma_50")
        _add(dma200, "dma_200")

        # Swings
        _add(sh1, "swing_high")
        _add(sh2, "swing_high")
        _add(sl1, "swing_low")
        _add(sl2, "swing_low")

        # 52W
        _add(h52,     "52w_high")
        _add(l52,     "52w_low")

        # Volume POC
        _add(poc,     "vol_poc")

        # Previous period
        _add(pm_h,   "prev_month_h")
        _add(pm_l,   "prev_month_l")
        _add(pw_h,   "prev_week_h")
        _add(pw_l,   "prev_week_l")

        # Round numbers
        _add(round_res, "round_num")
        _add(round_sup, "round_num")

        # ── Confluence scoring ─────────────────────────────────────────────────
        conf = _confluence(candidates, close)

        # ── Entry zone and final stop ─────────────────────────────────────────
        # Entry zone: half-ATR band around current close
        entry_low  = round(close - 0.5 * atr, 2)
        entry_high = round(close + 0.3 * atr, 2)
        # Stop: below strongest support or 2-ATR stop, whichever is less aggressive
        sup1 = conf.get("sup_1")
        stop_loss = round(
            max(
                (sup1 * 0.985 if sup1 else stop_2atr),
                stop_2atr,
            ), 2
        )
        # Ensure stop is not too tight (at least 1.5% below close)
        if stop_loss > close * 0.985:
            stop_loss = round(close * 0.985, 2)

        def _r(v):
            return round(float(v), 2) if v is not None else None

        return {
            "symbol":       symbol,
            "close":        _r(close),
            "atr_14":       _r(atr),
            # Monthly Pivots
            "mp_pp":        _r(mp.get("pp")),
            "mp_r1":        _r(mp.get("r1")),
            "mp_r2":        _r(mp.get("r2")),
            "mp_r3":        _r(mp.get("r3")),
            "mp_s1":        _r(mp.get("s1")),
            "mp_s2":        _r(mp.get("s2")),
            "mp_s3":        _r(mp.get("s3")),
            # Weekly Pivots
            "wp_pp":        _r(wp.get("pp")),
            "wp_r1":        _r(wp.get("r1")),
            "wp_r2":        _r(wp.get("r2")),
            "wp_s1":        _r(wp.get("s1")),
            "wp_s2":        _r(wp.get("s2")),
            # Fibonacci
            "fib_786":      _r(fib.get("786")),
            "fib_618":      _r(fib.get("618")),
            "fib_500":      _r(fib.get("500")),
            "fib_382":      _r(fib.get("382")),
            "fib_236":      _r(fib.get("236")),
            # Swings
            "swing_high_1": _r(sh1),
            "swing_high_2": _r(sh2),
            "swing_low_1":  _r(sl1),
            "swing_low_2":  _r(sl2),
            # Volume
            "vol_poc":      _r(poc),
            # Previous period
            "prev_week_h":  _r(pw_h),
            "prev_week_l":  _r(pw_l),
            "prev_month_h": _r(pm_h),
            "prev_month_l": _r(pm_l),
            # Round numbers
            "round_res":    _r(round_res),
            "round_sup":    _r(round_sup),
            # ATR stops & targets
            "stop_1atr":    stop_1atr,
            "stop_2atr":    stop_2atr,
            "target_1atr":  tgt_1atr,
            "target_2atr":  tgt_2atr,
            # Confluence
            "conf_res_1":       conf.get("res_1"),
            "conf_res_1_score": conf.get("res_1_score", 0),
            "conf_res_1_tags":  conf.get("res_1_tags", ""),
            "conf_res_2":       conf.get("res_2"),
            "conf_res_2_score": conf.get("res_2_score", 0),
            "conf_res_2_tags":  conf.get("res_2_tags", ""),
            "conf_sup_1":       conf.get("sup_1"),
            "conf_sup_1_score": conf.get("sup_1_score", 0),
            "conf_sup_1_tags":  conf.get("sup_1_tags", ""),
            "conf_sup_2":       conf.get("sup_2"),
            "conf_sup_2_score": conf.get("sup_2_score", 0),
            "conf_sup_2_tags":  conf.get("sup_2_tags", ""),
            # Entry/stop
            "entry_zone_low":  entry_low,
            "entry_zone_high": entry_high,
            "stop_loss":       stop_loss,
            "as_of_date":      as_of,
        }

    except Exception as exc:
        logger.warning("[KeyLevels] %s: %s", symbol, exc)
        return None


# ── Main runner ───────────────────────────────────────────────────────────────

def run() -> dict:
    """Compute key levels for all cached symbols. Writes key_levels.csv."""
    logger.info("[KeyLevels] Starting key levels computation")

    # Load technical indicators for 52W H/L and DMA reference
    tech: Optional[pd.DataFrame] = None
    if TECH_F.exists():
        tech = pd.read_csv(TECH_F)
        tech["symbol"] = tech["symbol"].str.upper()
        tech = tech.set_index("symbol")
        logger.info("[KeyLevels] Loaded technical_indicators: %d rows", len(tech))

    # Discover all cached symbols
    cache_files = sorted(CACHE.glob("*.parquet"))
    if not cache_files:
        return {"status": "ERROR", "error": "No parquet files in stock_history cache"}

    logger.info("[KeyLevels] Processing %d symbols from cache", len(cache_files))

    records = []
    errors  = 0

    for i, pq in enumerate(cache_files):
        sym = pq.stem.upper()
        tech_row = tech.loc[sym] if (tech is not None and sym in tech.index) else None
        result = _compute_symbol(sym, tech_row)
        if result:
            records.append(result)
        else:
            errors += 1

        if (i + 1) % 500 == 0:
            logger.info("[KeyLevels] Progress: %d / %d", i + 1, len(cache_files))

    if not records:
        return {"status": "ERROR", "error": "No records computed"}

    df_out = pd.DataFrame(records)

    # Atomic write
    tmp = OUTPUT.with_suffix(".tmp")
    df_out.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT))

    logger.info(
        "[KeyLevels] Complete — %d symbols, %d errors. Output: %s",
        len(records), errors, OUTPUT
    )
    return {"status": "OK", "symbols": len(records), "errors": errors}


if __name__ == "__main__":
    result = run()
    print(result)
