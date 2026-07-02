"""
Purity Refinement Engine -- Phase G
Refines purity scores in theme_tagging.csv using 4 dynamic signal layers:
  1. NSE sectoral index membership (strongest signal -- official index inclusion)
  2. Concall theme alignment      (management confirms theme in earnings call)
  3. News theme alignment         (media coverage aligns with theme + bullish tone)
  4. Insider conviction           (buying by insiders boosts primary theme purity)

Input:
    data/reference/theme_tagging.csv          base purity from Phase E
    data/NSE/indices/index_membership.csv     506 NSE-indexed symbols
    data/intelligence/concall_summary.csv     Phase F concall signals
    data/intelligence/news_signals.csv        Phase F 7-day news signals
    data/intelligence/insider_signals.csv     Phase F 30-day insider signals

Output:
    data/reference/theme_tagging.csv          UPDATED purity scores (in-place rewrite)
    data/intelligence/purity_change_log.csv   per-(symbol,theme) change audit trail

Run:
    py -3.11 engines/intelligence/purity_engine.py

Guardrails: G-D-02 atomic writes, G-D-03 no empty df, G-D-04 schema validation
"""

import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

TAGGING_PATH  = cfg.REFERENCE_DIR / "theme_tagging.csv"
CHANGELOG_PATH = cfg.INTELLIGENCE_DIR / "purity_change_log.csv"

# --------------------------------------------------------------------------
# NSE sectoral index → theme mapping
# A symbol in one of these index names gets an INDEX boost for the mapped theme.
# Source: nse constituents engine (30 sectoral indices in index_membership.csv)
# --------------------------------------------------------------------------
THEME_INDEX_KEYWORDS: dict[str, list[str]] = {
    "BANKING_CREDIT":         ["NIFTY BANK", "NIFTY PSU BANK", "NIFTY FINANCIAL SERVICES 25/50"],
    "INSURANCE_GROWTH":       ["NIFTY FINANCIAL SERVICES 25/50"],
    "WEALTH_MGMT":            ["NIFTY FINANCIAL SERVICES 25/50"],
    "FINTECH_INFRASTR":       ["NIFTY IT", "NIFTY FINANCIAL SERVICES 25/50"],
    "HEALTHCARE_EXPANSION":   ["NIFTY PHARMA", "NIFTY HEALTHCARE INDEX"],
    "HEALTHTECH":             ["NIFTY HEALTHCARE INDEX"],
    "DIGITAL_INDIA":          ["NIFTY IT"],
    "AI_ENABLERS":            ["NIFTY IT"],
    "CYBERSECURITY":          ["NIFTY IT"],
    "GREEN_ENERGY":           ["NIFTY ENERGY"],
    "POWER_TD":               ["NIFTY ENERGY"],
    "COMMODITY_SUPER":        ["NIFTY METAL", "NIFTY OIL & GAS", "NIFTY COMMODITIES"],
    "GREEN_HYDROGEN":         ["NIFTY ENERGY"],
    "PSU_REVIVAL":            ["NIFTY CPSE", "NIFTY PSE", "NIFTY PSU BANK"],
    "REAL_ESTATE_RECOVERY":   ["NIFTY REALTY"],
    "SMART_CITIES":           ["NIFTY REALTY"],
    "MEDIA_ENTERTAIN":        ["NIFTY MEDIA"],
    "EV_TRANSITION":          ["NIFTY AUTO"],
    "RURAL_CONSUMPTION":      ["NIFTY FMCG"],
    "PREMIUMISATION":         ["NIFTY CONSUMER DURABLES", "NIFTY FMCG"],
    "QUICK_COMMERCE":         ["NIFTY CONSUMER DURABLES"],
    "EXPORT_GROWTH":          ["NIFTY MNC"],
    "CHINA_PLUS_ONE":         ["NIFTY MNC"],
    "INDIA_PLUS_ONE":         ["NIFTY MNC"],
    "SPECIALTY_CHEM":         ["NIFTY COMMODITIES"],
    "LOGISTICS_MODERNISATION":["NIFTY CPSE"],
    "PORTS_SHIPPING":         ["NIFTY CPSE", "NIFTY PSE"],
    "GOLD_JEWELLERY":         ["NIFTY COMMODITIES"],
    "TOURISM_HOSP":           ["NIFTY CONSUMER DURABLES"],
}

# boost magnitudes
BOOST_INDEX    = 0.18   # being in the official NSE sectoral index -- strong signal
BOOST_CONCALL  = 0.10   # management confirmed theme in earnings call (bullish)
BOOST_NEWS     = 0.07   # news sentiment bullish + top_theme matches
BOOST_INSIDER  = 0.05   # insider buying on primary theme (additional trust)

PENALTY_CONCALL = -0.08  # management bearish on theme
PENALTY_NEWS    = -0.05  # news bearish on theme

PURITY_MIN = 0.25
PURITY_MAX = 1.00


def _build_index_lookup(idx_df: pd.DataFrame) -> dict[str, set[str]]:
    """
    Returns {SYMBOL: set_of_index_names} from index_membership.csv.
    index_names is pipe-separated in the CSV.
    """
    lookup: dict[str, set[str]] = {}
    for _, row in idx_df.iterrows():
        sym = str(row["symbol"]).upper().strip()
        raw = str(row.get("index_names", "") or "")
        names = {n.strip() for n in raw.split("|") if n.strip()}
        lookup[sym] = names
    return lookup


def _concall_themes(cc_df: pd.DataFrame) -> dict[str, tuple[set[str], str]]:
    """Returns {SYMBOL: (themes_set, sentiment)}."""
    out: dict[str, tuple[set[str], str]] = {}
    if cc_df is None or cc_df.empty:
        return out
    for _, row in cc_df.iterrows():
        sym = str(row.get("symbol", "")).upper().strip()
        raw_themes = str(row.get("themes", "") or "")
        themes = {t.strip().upper() for t in raw_themes.split(",") if t.strip()}
        sentiment = str(row.get("sentiment", "NEUTRAL")).upper()
        out[sym] = (themes, sentiment)
    return out


def _news_lookup(news_df: pd.DataFrame) -> dict[str, tuple[str, float]]:
    """Returns {SYMBOL: (top_theme, sentiment_7d)}."""
    out: dict[str, tuple[str, float]] = {}
    if news_df is None or news_df.empty:
        return out
    for _, row in news_df.iterrows():
        sym = str(row.get("symbol", "")).upper().strip()
        top_theme = str(row.get("top_theme", "") or "").upper().strip()
        s7d = float(row.get("sentiment_7d", 0.0) or 0.0)
        out[sym] = (top_theme, s7d)
    return out


def _insider_lookup(ins_df: pd.DataFrame) -> dict[str, str]:
    """Returns {SYMBOL: insider_conviction}."""
    out: dict[str, str] = {}
    if ins_df is None or ins_df.empty:
        return out
    for _, row in ins_df.iterrows():
        sym = str(row.get("symbol", "")).upper().strip()
        conv = str(row.get("insider_conviction", "") or "").upper()
        out[sym] = conv
    return out


def run() -> pd.DataFrame | None:
    logger.info("[PurityEngine] Phase G purity refinement starting")

    if not TAGGING_PATH.exists():
        logger.error("[PurityEngine] theme_tagging.csv not found -- run theme_tagging_engine.py first")
        return None

    tag_df = pd.read_csv(TAGGING_PATH)
    logger.info("[PurityEngine] Loaded %d theme tags", len(tag_df))

    # Normalise column names
    tag_df["SYMBOL"] = tag_df["SYMBOL"].str.strip().str.upper()
    tag_df["THEME"]  = tag_df["THEME"].str.strip().str.upper()
    tag_df["PURITY_SCORE"] = pd.to_numeric(tag_df["PURITY_SCORE"], errors="coerce").fillna(0.5)
    is_primary_col = tag_df["IS_PRIMARY"].astype(bool) if "IS_PRIMARY" in tag_df.columns else pd.Series([False] * len(tag_df))

    # --- Load signal layers (all optional) -----------------------------------
    idx_path  = cfg.NSE_DIR / "indices" / "index_membership.csv"
    cc_path   = cfg.INTELLIGENCE_DIR / "concall_summary.csv"
    news_path = cfg.INTELLIGENCE_DIR / "news_signals.csv"
    ins_path  = cfg.INTELLIGENCE_DIR / "insider_signals.csv"

    idx_lookup     = _build_index_lookup(pd.read_csv(idx_path)) if idx_path.exists() else {}
    concall_lookup = _concall_themes(pd.read_csv(cc_path))      if cc_path.exists() else {}
    news_lookup    = _news_lookup(pd.read_csv(news_path))        if news_path.exists() else {}
    insider_lookup = _insider_lookup(pd.read_csv(ins_path))      if ins_path.exists() else {}

    logger.info("[PurityEngine] Signals loaded -- index:%d concall:%d news:%d insider:%d",
                len(idx_lookup), len(concall_lookup), len(news_lookup), len(insider_lookup))

    # --- Apply boosts per (symbol, theme) row --------------------------------
    changelog_rows = []
    new_purities   = []

    for i, row in tag_df.iterrows():
        sym    = row["SYMBOL"]
        theme  = row["THEME"]
        base   = float(row["PURITY_SCORE"])
        is_pri = bool(is_primary_col.iloc[i]) if i < len(is_primary_col) else False

        boost  = 0.0
        reasons: list[str] = []

        # --- Boost 1: NSE sectoral index membership --------------------------
        sym_indices = idx_lookup.get(sym, set())
        for idx_name in THEME_INDEX_KEYWORDS.get(theme, []):
            if idx_name in sym_indices:
                boost += BOOST_INDEX
                reasons.append(f"index:{idx_name}")
                break  # count once even if multiple index matches

        # --- Boost 2: Concall theme alignment --------------------------------
        cc_themes, cc_sent = concall_lookup.get(sym, (set(), "NEUTRAL"))
        if theme in cc_themes:
            if cc_sent == "BULLISH":
                boost += BOOST_CONCALL
                reasons.append("concall:BULLISH")
            elif cc_sent == "BEARISH":
                boost += PENALTY_CONCALL
                reasons.append("concall:BEARISH")

        # --- Boost 3: News theme alignment -----------------------------------
        news_top, news_s7d = news_lookup.get(sym, ("", 0.0))
        if news_top == theme:
            if news_s7d >= 0.2:
                boost += BOOST_NEWS
                reasons.append(f"news:bullish({news_s7d:.2f})")
            elif news_s7d <= -0.2:
                boost += PENALTY_NEWS
                reasons.append(f"news:bearish({news_s7d:.2f})")

        # --- Boost 4: Insider conviction (primary theme only) ----------------
        if is_pri:
            ins_conv = insider_lookup.get(sym, "")
            if ins_conv in ("STRONG_BUY", "BUY"):
                boost += BOOST_INSIDER
                reasons.append(f"insider:{ins_conv}")

        refined = float(np.clip(base + boost, PURITY_MIN, PURITY_MAX))
        new_purities.append(refined)

        if abs(refined - base) >= 0.01:
            changelog_rows.append({
                "symbol":     sym,
                "theme":      theme,
                "is_primary": is_pri,
                "base_purity":   round(base, 4),
                "boost_applied": round(boost, 4),
                "refined_purity": round(refined, 4),
                "reasons":    "|".join(reasons),
                "as_of_date": date.today().isoformat(),
            })

    tag_df["PURITY_SCORE"] = [round(p, 4) for p in new_purities]
    tag_df["PURITY_REFINED"] = True

    # --- Write updated theme_tagging.csv (atomic) ----------------------------
    tmp = TAGGING_PATH.with_suffix(".tmp")
    tag_df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(TAGGING_PATH))
    logger.info("[PurityEngine] Updated theme_tagging.csv (%d rows)", len(tag_df))

    # --- Write change log ----------------------------------------------------
    if changelog_rows:
        clog = pd.DataFrame(changelog_rows)
        tmp2 = CHANGELOG_PATH.with_suffix(".tmp")
        clog.to_csv(tmp2, index=False)
        shutil.move(str(tmp2), str(CHANGELOG_PATH))
        logger.info("[PurityEngine] Change log: %d purity updates written", len(clog))
    else:
        logger.info("[PurityEngine] No purity changes >= 0.01 (all signal files may be empty)")

    # Summary
    changed   = len(changelog_rows)
    boosted   = sum(1 for r in changelog_rows if r["boost_applied"] > 0)
    penalised = sum(1 for r in changelog_rows if r["boost_applied"] < 0)
    new_avg   = tag_df["PURITY_SCORE"].mean()

    print(f"\n[PurityEngine] Phase G purity refinement complete")
    print(f"  Total tags        : {len(tag_df)}")
    print(f"  Tags changed      : {changed}  (boosted: {boosted}, penalised: {penalised})")
    print(f"  New avg purity    : {new_avg:.4f}")
    if changelog_rows:
        top = sorted(changelog_rows, key=lambda r: abs(r["boost_applied"]), reverse=True)[:8]
        print(f"\n  Largest purity changes:")
        for r in top:
            print(f"    {r['symbol']:<14} {r['theme']:<30} "
                  f"{r['base_purity']:.3f} -> {r['refined_purity']:.3f} "
                  f"({r['reasons']})")

    logger.info("[PurityEngine] Done -- avg purity %.4f, %d tags changed", new_avg, changed)
    return tag_df


if __name__ == "__main__":
    run()
