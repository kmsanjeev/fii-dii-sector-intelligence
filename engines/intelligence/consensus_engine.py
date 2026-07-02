"""
Multi-Signal Consensus Engine -- Phase G
Combines 4 independent signal layers into a single per-symbol consensus score.

Signal layers (weighted):
  concall_score     35%  management guidance + tone (most deliberate, high-signal)
  insider_score     25%  NSE PIT 30D net buy/sell (informed capital)
  news_sentiment    20%  7-day rolling media sentiment (broad awareness proxy)
  deal_score        20%  institutional block/bulk deal net flow (smart money)

Each raw signal is normalised to [0, 100] before weighting.
Missing signals are replaced by 50.0 (neutral) so the score degrades gracefully
as signal files become available incrementally.

Inputs:
    data/intelligence/concall_summary.csv          Phase F
    data/intelligence/insider_signals.csv          Phase F
    data/intelligence/news_signals.csv             Phase F
    data/intelligence/institutional_deal_signals.csv  Phase 7A

Output:
    data/intelligence/consensus_scores.csv         per-symbol consensus intelligence

Run:
    py -3.11 engines/intelligence/consensus_engine.py

Guardrails: G-D-02 atomic writes, G-D-03 no empty df, G-I-04 no fillna(0) on signals
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

OUTPUT_PATH = cfg.INTELLIGENCE_DIR / "consensus_scores.csv"

# Weights must sum to 1.0
W_CONCALL = 0.35
W_INSIDER  = 0.25
W_NEWS     = 0.20
W_DEAL     = 0.20

NEUTRAL = 50.0  # neutral placeholder when a signal file is missing

# Raw score normalisation bounds (clip then rescale to 0-100)
CONCALL_MIN, CONCALL_MAX = -1.6,  2.0   # concall_score formula range
INSIDER_MIN, INSIDER_MAX = -20.0, 20.0  # insider_score = net_value_30d_cr.clip(-20,20)
NEWS_MIN,    NEWS_MAX    = -1.0,   1.0  # sentiment_7d weighted mean of sent_scores


def _norm(v: float, lo: float, hi: float) -> float:
    """Linearly map [lo, hi] -> [0, 100], clip at boundaries."""
    return float(np.clip((v - lo) / (hi - lo) * 100.0, 0.0, 100.0))


def _pct_rank(series: pd.Series) -> pd.Series:
    """Percentile rank 0-100 (NaN stays NaN)."""
    return series.rank(pct=True, na_option="keep") * 100.0


def _consensus_label(score: float) -> str:
    if score >= 68:
        return "STRONG_BUY"
    if score >= 58:
        return "BUY"
    if score >= 42:
        return "NEUTRAL"
    if score >= 32:
        return "SELL"
    return "STRONG_SELL"


def run() -> pd.DataFrame | None:
    logger.info("[ConsensusEngine] Phase G multi-signal consensus engine starting")

    # ── Load base universe from bull_run (always present) ────────────────────
    bull_path = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
    if not bull_path.exists():
        logger.error("[ConsensusEngine] bull_run_probability.csv missing -- cannot build universe")
        return None

    universe = pd.read_csv(bull_path, usecols=["symbol", "sector", "label", "bull_run_score"])
    universe["symbol"] = universe["symbol"].str.strip().str.upper()
    logger.info("[ConsensusEngine] Universe: %d symbols", len(universe))

    signals_loaded: list[str] = []

    # ── Signal 1: Concall score (35%) ─────────────────────────────────────────
    cc_path = cfg.INTELLIGENCE_DIR / "concall_summary.csv"
    if cc_path.exists():
        cc = pd.read_csv(cc_path, usecols=["symbol", "concall_score"])
        cc["symbol"] = cc["symbol"].str.strip().str.upper()
        cc["concall_score"] = pd.to_numeric(cc["concall_score"], errors="coerce")
        cc["concall_norm"] = cc["concall_score"].apply(
            lambda v: _norm(v, CONCALL_MIN, CONCALL_MAX) if pd.notna(v) else np.nan
        )
        universe = universe.merge(cc[["symbol", "concall_score", "concall_norm"]], on="symbol", how="left")
        filled = universe["concall_norm"].notna().sum()
        signals_loaded.append(f"concall({filled})")
        logger.info("[ConsensusEngine] Concall: %d symbols with signal", filled)
    else:
        universe["concall_score"] = np.nan
        universe["concall_norm"]  = np.nan
        logger.warning("[ConsensusEngine] concall_summary.csv missing -- concall signal = NEUTRAL")

    # ── Signal 2: Insider score (25%) ─────────────────────────────────────────
    ins_path = cfg.INTELLIGENCE_DIR / "insider_signals.csv"
    if ins_path.exists():
        ins = pd.read_csv(ins_path, usecols=["symbol", "insider_score", "insider_conviction"])
        ins["symbol"] = ins["symbol"].str.strip().str.upper()
        ins["insider_score"] = pd.to_numeric(ins["insider_score"], errors="coerce")
        ins["insider_norm"] = ins["insider_score"].apply(
            lambda v: _norm(v, INSIDER_MIN, INSIDER_MAX) if pd.notna(v) else np.nan
        )
        universe = universe.merge(ins[["symbol", "insider_score", "insider_norm", "insider_conviction"]], on="symbol", how="left")
        filled = universe["insider_norm"].notna().sum()
        signals_loaded.append(f"insider({filled})")
        logger.info("[ConsensusEngine] Insider: %d symbols with signal", filled)
    else:
        universe["insider_score"]      = np.nan
        universe["insider_norm"]       = np.nan
        universe["insider_conviction"] = ""
        logger.warning("[ConsensusEngine] insider_signals.csv missing -- insider signal = NEUTRAL")

    # ── Signal 3: News sentiment (20%) ────────────────────────────────────────
    news_path = cfg.INTELLIGENCE_DIR / "news_signals.csv"
    if news_path.exists():
        news = pd.read_csv(news_path, usecols=["symbol", "sentiment_7d", "sentiment_label", "news_count_7d"])
        news["symbol"] = news["symbol"].str.strip().str.upper()
        news["sentiment_7d"] = pd.to_numeric(news["sentiment_7d"], errors="coerce")
        news["news_norm"] = news["sentiment_7d"].apply(
            lambda v: _norm(v, NEWS_MIN, NEWS_MAX) if pd.notna(v) else np.nan
        )
        universe = universe.merge(
            news[["symbol", "sentiment_7d", "news_norm", "sentiment_label", "news_count_7d"]],
            on="symbol", how="left"
        )
        filled = universe["news_norm"].notna().sum()
        signals_loaded.append(f"news({filled})")
        logger.info("[ConsensusEngine] News: %d symbols with signal", filled)
    else:
        universe["sentiment_7d"]    = np.nan
        universe["news_norm"]       = np.nan
        universe["sentiment_label"] = ""
        universe["news_count_7d"]   = np.nan
        logger.warning("[ConsensusEngine] news_signals.csv missing -- news signal = NEUTRAL")

    # ── Signal 4: Institutional deal flow (20%) ───────────────────────────────
    deal_path = cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv"
    if deal_path.exists():
        deals = pd.read_csv(deal_path, usecols=["symbol", "inst_net_value_cr"])
        deals["symbol"] = deals["symbol"].str.strip().str.upper()
        deals["inst_net_value_cr"] = pd.to_numeric(deals["inst_net_value_cr"], errors="coerce")
        # Percentile rank across the universe (deals file may not cover all symbols)
        deals["deal_norm"] = _pct_rank(deals["inst_net_value_cr"])
        universe = universe.merge(deals[["symbol", "inst_net_value_cr", "deal_norm"]], on="symbol", how="left")
        filled = universe["deal_norm"].notna().sum()
        signals_loaded.append(f"deals({filled})")
        logger.info("[ConsensusEngine] Deals: %d symbols with signal", filled)
    else:
        universe["inst_net_value_cr"] = np.nan
        universe["deal_norm"]         = np.nan
        logger.warning("[ConsensusEngine] institutional_deal_signals.csv missing -- deal signal = NEUTRAL")

    # ── Composite score (NaN signals → NEUTRAL placeholder) ──────────────────
    def _fill(col: str) -> pd.Series:
        return universe[col].fillna(NEUTRAL)

    universe["consensus_score"] = (
        _fill("concall_norm") * W_CONCALL
        + _fill("insider_norm")  * W_INSIDER
        + _fill("news_norm")     * W_NEWS
        + _fill("deal_norm")     * W_DEAL
    ).round(2)

    # Only include symbols where at least ONE real signal exists
    has_signal = (
        universe["concall_norm"].notna()
        | universe["insider_norm"].notna()
        | universe["news_norm"].notna()
        | universe["deal_norm"].notna()
    )
    scored = universe[has_signal].copy()
    logger.info("[ConsensusEngine] Symbols with >= 1 signal: %d", len(scored))

    if scored.empty:
        logger.warning("[ConsensusEngine] No symbols with any signal -- check Phase F engines are run")
        print("[ConsensusEngine] WARNING: no Phase F signal data found. Run news/insider/concall engines first.")
        # Still write the full universe with neutral scores for downstream use
        scored = universe.copy()
        scored["consensus_score"] = NEUTRAL

    scored["consensus_label"] = scored["consensus_score"].apply(_consensus_label)
    scored["as_of_date"]      = date.today().isoformat()

    # Which signals contributed
    scored["signals_used"] = scored.apply(lambda r: "|".join([
        "CONCALL"  if pd.notna(r.get("concall_norm"))  else "",
        "INSIDER"  if pd.notna(r.get("insider_norm"))  else "",
        "NEWS"     if pd.notna(r.get("news_norm"))     else "",
        "DEALS"    if pd.notna(r.get("deal_norm"))     else "",
    ]).strip("|").replace("||", "|"), axis=1)

    # Canonical output columns
    output_cols = [
        "symbol", "sector", "label", "bull_run_score",
        "consensus_score", "consensus_label", "signals_used",
        # raw normalised sub-scores
        "concall_norm", "insider_norm", "news_norm", "deal_norm",
        # raw signal values for reference
        "concall_score", "insider_score", "insider_conviction",
        "sentiment_7d", "sentiment_label", "news_count_7d",
        "inst_net_value_cr",
        "as_of_date",
    ]
    available_cols = [c for c in output_cols if c in scored.columns]
    out_df = scored[available_cols].sort_values("consensus_score", ascending=False)

    if out_df.empty:
        logger.error("[ConsensusEngine] Output dataframe is empty -- aborting write")
        return None

    tmp = OUTPUT_PATH.with_suffix(".tmp")
    out_df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT_PATH))
    logger.info("[ConsensusEngine] Wrote %d rows to %s", len(out_df), OUTPUT_PATH)

    # ── Summary ───────────────────────────────────────────────────────────────
    label_counts = out_df["consensus_label"].value_counts()
    print(f"\n[ConsensusEngine] Phase G multi-signal consensus complete")
    print(f"  Signals loaded    : {', '.join(signals_loaded) if signals_loaded else 'NONE (Phase F not run)'}")
    print(f"  Symbols scored    : {len(out_df)}")
    print(f"  Score range       : {out_df['consensus_score'].min():.1f} - {out_df['consensus_score'].max():.1f}")
    print(f"  Label breakdown   :")
    for lbl in ["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]:
        cnt = label_counts.get(lbl, 0)
        bar = "#" * (cnt // 20)
        print(f"    {lbl:<20} {cnt:4d}  {bar}")
    print()
    print("  Top STRONG_BUY signals:")
    top = out_df[out_df["consensus_label"] == "STRONG_BUY"].head(10)
    for _, r in top.iterrows():
        sigs = str(r.get("signals_used", ""))
        print(f"    {str(r['symbol']):<14} score={r['consensus_score']:.1f}  [{sigs}]")

    return out_df


if __name__ == "__main__":
    run()
