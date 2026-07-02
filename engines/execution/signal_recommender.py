"""
Signal Recommender -- Phase 24
Converts intelligence signals into sized order recommendations.

Composite score: 60% bull_run_score + 40% ml_bull_run_score.
Position size: composite_score/100 * max_position_pct * portfolio_value (INR).
"""

import sys
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.execution.risk_engine import load_config

logger = get_logger(__name__)


def recommend(
    portfolio_value: float,
    top_n: int = 10,
    min_score: float = 50.0,
    labels: Optional[list[str]] = None,
    action: str = "BUY",
) -> list[dict]:
    """
    Return up to top_n order recommendations ranked by composite signal score.

    Each recommendation dict:
      symbol, sector, label, bull_run_score, ml_score, composite_score,
      rotation_signal, close_now, action,
      suggested_qty, suggested_value, suggested_pct
    """
    risk_cfg = load_config()
    max_pos_pct = risk_cfg.get("max_position_pct", 10.0) / 100.0

    # If caller did not supply portfolio_value, fall back to config
    if portfolio_value <= 0:
        portfolio_value = float(risk_cfg.get("portfolio_value", 0.0))

    br_path = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
    ml_path = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"
    rt_path = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"

    if not br_path.exists():
        raise RuntimeError("bull_run_probability.csv not found -- run Phase 8B first")

    df = pd.read_csv(br_path, usecols=["symbol", "sector", "label", "bull_run_score", "close_now"])
    df["symbol"] = df["symbol"].str.strip().str.upper()

    if ml_path.exists():
        ml = pd.read_csv(ml_path, usecols=["symbol", "ml_bull_run_score"])
        ml["symbol"] = ml["symbol"].str.strip().str.upper()
        df = df.merge(ml, on="symbol", how="left")
    else:
        df["ml_bull_run_score"] = 0.0

    if rt_path.exists():
        rot = pd.read_csv(rt_path, usecols=["sector", "rotation_signal"])
        df = df.merge(rot, on="sector", how="left")
    else:
        df["rotation_signal"] = "NEUTRAL"

    df["ml_bull_run_score"] = pd.to_numeric(df["ml_bull_run_score"], errors="coerce").fillna(0.0)
    df["bull_run_score"]    = pd.to_numeric(df["bull_run_score"],    errors="coerce").fillna(0.0)
    df["composite_score"]   = df["bull_run_score"] * 0.6 + df["ml_bull_run_score"] * 0.4
    df["close_now"]         = pd.to_numeric(df["close_now"], errors="coerce").fillna(0.0)

    if labels:
        df = df[df["label"].isin(labels)]
    df = df[df["composite_score"] >= min_score]
    df = df[df["close_now"] > 0]
    df = df.sort_values("composite_score", ascending=False).head(top_n)

    recs: list[dict] = []
    for _, row in df.iterrows():
        ltp = float(row["close_now"])
        if portfolio_value > 0:
            max_value = portfolio_value * max_pos_pct
            qty = max(1, int(max_value / ltp))
        else:
            qty = 1
        suggested_value = round(qty * ltp, 2)

        recs.append({
            "symbol":          str(row["symbol"]),
            "sector":          str(row.get("sector") or ""),
            "label":           str(row.get("label") or ""),
            "bull_run_score":  round(float(row["bull_run_score"]), 2),
            "ml_score":        round(float(row["ml_bull_run_score"]), 2),
            "composite_score": round(float(row["composite_score"]), 2),
            "rotation_signal": str(row.get("rotation_signal") or "NEUTRAL"),
            "close_now":       round(ltp, 2),
            "action":          action.upper(),
            "suggested_qty":   qty,
            "suggested_value": suggested_value,
            "suggested_pct":   round(suggested_value / portfolio_value * 100, 2) if portfolio_value > 0 else 0.0,
        })

    logger.info("[Recommender] %d recommendations (pf=%.0f)", len(recs), portfolio_value)
    return recs
