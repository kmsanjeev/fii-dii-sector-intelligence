"""
Screener Engine -- Phase 23
Builds a master universe DataFrame from all intelligence CSVs and applies
filter/sort criteria. Results are used by both the Screener and Comparator tools.

Universe: ~2400 symbols with ~35 columns across price, intelligence, ML,
corporate, shareholding, sector rotation, and index membership dimensions.

In-process cache (5 min TTL) avoids redundant CSV joins on repeated API calls.
"""

import math
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Source paths ───────────────────────────────────────────────────────────────

BULL_RUN_CSV  = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
MOMENTUM_CSV  = cfg.INTELLIGENCE_DIR / "price_momentum.csv"
ML_CSV        = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"
CONF_CSV      = cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
ROT_CSV       = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
HOLDING_CSV   = cfg.DATA_DIR / "NSE" / "shareholding" / "holding_trends.csv"
INDEX_CSV     = cfg.DATA_DIR / "NSE" / "indices" / "index_membership.csv"

# ── Universe cache ─────────────────────────────────────────────────────────────

_cache: Optional[tuple[pd.DataFrame, float]] = None
_CACHE_TTL = 300.0   # 5 minutes


def _build_universe() -> pd.DataFrame:
    global _cache
    now = time.monotonic()
    if _cache and (now - _cache[1]) < _CACHE_TTL:
        return _cache[0]
    df = _load_and_join()
    _cache = (df, now)
    logger.info("[Screener] Universe built: %d symbols, %d columns", len(df), len(df.columns))
    return df


def _load_and_join() -> pd.DataFrame:
    if not BULL_RUN_CSV.exists():
        raise RuntimeError("bull_run_probability.csv not found -- run Phase 8B first")

    # 1. Base: bull run probability (label, scores, sector)
    df = pd.read_csv(BULL_RUN_CSV, usecols=[
        "symbol", "sector", "label", "bull_run_score",
        "price_score", "sector_flow_score", "deal_score",
        "corporate_score", "base_score", "close_now",
    ])
    df["symbol"] = df["symbol"].str.strip().str.upper()

    # 2. Price momentum (returns)
    if MOMENTUM_CSV.exists():
        mom = pd.read_csv(MOMENTUM_CSV, usecols=[
            "symbol", "ret_30d", "ret_60d", "ret_90d", "ret_365d", "vol_ratio",
        ])
        mom["symbol"] = mom["symbol"].str.strip().str.upper()
        df = df.merge(mom, on="symbol", how="left")

    # 3. ML scores (ml_scores_combined has "label" col -- skip to avoid conflict with base)
    if ML_CSV.exists():
        ml = pd.read_csv(ML_CSV, usecols=[
            "symbol", "ml_bull_run_score", "accumulation_score",
        ])
        ml["symbol"] = ml["symbol"].str.strip().str.upper()
        df = df.merge(ml, on="symbol", how="left")

    # 4. Corporate confidence
    if CONF_CSV.exists():
        conf = pd.read_csv(CONF_CSV, usecols=[
            "symbol", "confidence_score_12m", "confidence_label", "action_count_12m",
        ])
        conf["symbol"] = conf["symbol"].str.strip().str.upper()
        df = df.merge(conf, on="symbol", how="left")

    # 5. Sector rotation (join on sector)
    if ROT_CSV.exists():
        rot = pd.read_csv(ROT_CSV, usecols=["sector", "rotation_signal", "combined_score"])
        df = df.merge(rot, on="sector", how="left")

    # 6. Shareholding trends (latest quarter per symbol)
    if HOLDING_CSV.exists():
        ht = pd.read_csv(HOLDING_CSV, dtype=str)
        ht["quarter_end_date"] = pd.to_datetime(ht["quarter_end_date"], errors="coerce")
        for col in ["promoter_pct","fii_pct","dii_pct","promoter_delta","fii_delta","dii_delta"]:
            ht[col] = pd.to_numeric(ht[col], errors="coerce")
        # Keep most recent row per symbol
        ht = (ht.sort_values("quarter_end_date")
                .groupby("symbol", as_index=False)
                .last()
                [["symbol","promoter_pct","fii_pct","dii_pct",
                  "promoter_delta","fii_delta","dii_delta","conviction_signal"]])
        ht["symbol"] = ht["symbol"].str.strip().str.upper()
        df = df.merge(ht, on="symbol", how="left")

    # 7. Index membership
    if INDEX_CSV.exists():
        idx = pd.read_csv(INDEX_CSV, usecols=["symbol", "index_names"])
        idx["symbol"] = idx["symbol"].str.strip().str.upper()
        df = df.merge(idx, on="symbol", how="left")

    # Numeric coercion
    num_cols = [
        "bull_run_score", "price_score", "sector_flow_score", "deal_score",
        "corporate_score", "base_score", "close_now",
        "ret_30d", "ret_60d", "ret_90d", "ret_365d", "vol_ratio",
        "ml_bull_run_score", "accumulation_score",
        "confidence_score_12m", "action_count_12m",
        "promoter_pct", "fii_pct", "dii_pct",
        "promoter_delta", "fii_delta", "dii_delta",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.drop_duplicates(subset=["symbol"])


def invalidate_cache() -> None:
    """Force rebuild on next call (call after pipeline run)."""
    global _cache
    _cache = None


# ── Screener ───────────────────────────────────────────────────────────────────

def screen(filters: dict) -> tuple[list[dict], int]:
    """
    Apply filters to the master universe and return (records, total_before_limit).

    filters keys (all optional):
      labels            list[str]   label values to include
      sectors           list[str]   sector names
      indices           list[str]   index name substrings (e.g. "NIFTY50")
      conviction_signal str         "BUYING" | "SELLING" | "STABLE"
      fii_delta_dir     str         "positive" | "negative"
      min/max_score     float       bull_run_score range
      min/max_ml        float       ml_bull_run_score range
      min/max_ret_30d   float       30d return %
      min/max_ret_90d   float       90d return %
      min/max_ret_365d  float       365d return %
      min/max_confidence float      confidence_score_12m range
      min_promoter_pct  float       promoter % floor
      sort_by           str         column name (default: bull_run_score)
      sort_dir          str         "asc" | "desc"
      limit             int         max rows returned (default 200, cap 500)
    """
    df = _build_universe().copy()

    labels = filters.get("labels")
    if labels:
        df = df[df["label"].isin(labels)]

    sectors = filters.get("sectors")
    if sectors:
        df = df[df["sector"].isin(sectors)]

    indices = filters.get("indices")
    if indices:
        mask = df["index_names"].fillna("").apply(
            lambda x: any(idx in x for idx in indices)
        )
        df = df[mask]

    conviction = filters.get("conviction_signal")
    if conviction:
        df = df[df["conviction_signal"].fillna("") == conviction]

    fii_dir = filters.get("fii_delta_dir")
    if fii_dir == "positive":
        df = df[df["fii_delta"].fillna(0) > 0]
    elif fii_dir == "negative":
        df = df[df["fii_delta"].fillna(0) < 0]

    _range_filters = [
        ("bull_run_score",     "min_score",       "max_score"),
        ("ml_bull_run_score",  "min_ml",          "max_ml"),
        ("ret_30d",            "min_ret_30d",      "max_ret_30d"),
        ("ret_90d",            "min_ret_90d",      "max_ret_90d"),
        ("ret_365d",           "min_ret_365d",     "max_ret_365d"),
        ("confidence_score_12m","min_confidence",  "max_confidence"),
        ("promoter_pct",       "min_promoter_pct", None),
    ]
    for col, key_min, key_max in _range_filters:
        if col not in df.columns:
            continue
        v_min = filters.get(key_min)
        v_max = filters.get(key_max) if key_max else None
        if v_min is not None:
            df = df[df[col].fillna(-1e9) >= v_min]
        if v_max is not None:
            df = df[df[col].fillna(1e9) <= v_max]

    sort_by  = filters.get("sort_by", "bull_run_score")
    sort_dir = filters.get("sort_dir", "desc")
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=(sort_dir == "asc"), na_position="last")

    total = len(df)
    limit = min(int(filters.get("limit", 200)), 500)
    df    = df.head(limit)

    rows = df.to_dict(orient="records")
    # float("nan") is not JSON-serialisable; replace with None after dict conversion
    clean = [
        {k: None if isinstance(v, float) and math.isnan(v) else v for k, v in row.items()}
        for row in rows
    ]
    return clean, total


# ── Comparator ─────────────────────────────────────────────────────────────────

COMPARE_COLS = [
    # "symbol" excluded -- becomes index after set_index("symbol")
    "sector", "label", "bull_run_score",
    "ml_bull_run_score", "accumulation_score", "close_now",
    "ret_30d", "ret_60d", "ret_90d", "ret_365d", "vol_ratio",
    "price_score", "sector_flow_score", "deal_score", "corporate_score",
    "confidence_score_12m", "confidence_label",
    "promoter_pct", "fii_pct", "dii_pct",
    "promoter_delta", "fii_delta", "dii_delta", "conviction_signal",
    "rotation_signal", "combined_score",
]


def compare(symbols: list[str]) -> dict[str, Optional[dict]]:
    """Return a per-symbol dict of all comparison metrics."""
    df = _build_universe()
    sym_upper = [s.strip().upper() for s in symbols if s.strip()]
    cols = [c for c in COMPARE_COLS if c in df.columns]
    subset = df[df["symbol"].isin(sym_upper)].set_index("symbol")[cols]

    result: dict[str, Optional[dict]] = {}
    for sym in sym_upper:
        if sym in subset.index:
            row = subset.loc[sym]
            result[sym] = row.where(pd.notna(row), None).to_dict()
        else:
            result[sym] = None
    return result


# ── Universe stats ─────────────────────────────────────────────────────────────

def universe_stats() -> dict:
    """Label + sector counts for populating filter dropdowns."""
    df = _build_universe()
    label_counts  = df["label"].value_counts().to_dict()
    sector_list   = sorted(df["sector"].dropna().unique().tolist())
    rotation_map  = {}
    if "rotation_signal" in df.columns:
        rotation_map = df.set_index("sector")["rotation_signal"].dropna().to_dict()
    return {
        "total_symbols": len(df),
        "label_counts":  label_counts,
        "sector_list":   sector_list,
        "rotation_map":  rotation_map,
    }
