"""
Trade Conviction Engine
Server-side port of frontend/src/components/platform/TradeIntelligenceCard.tsx —
computes the same 7-factor conviction score (trend/DMA, F&O OI, sector rotation,
shareholding trends, valuation, management sentiment, ML model) so the alert
engine can fire on score thresholds without a browser in the loop.
Output: data/intelligence/trade_conviction_scores.csv

Run: py -3.11 -m engines.intelligence.trade_conviction_engine
"""

import shutil
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT           = cfg.INTELLIGENCE_DIR / "trade_conviction_scores.csv"
BULL_RUN         = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
TECHNICAL        = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"
FNO_INTEL        = cfg.INTELLIGENCE_DIR / "fno_intelligence.csv"
SECTOR_ROTATION  = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
HOLDING_TRENDS   = cfg.NSE_DIR / "shareholding" / "holding_trends.csv"
VALUATION        = cfg.NSE_DIR / "results" / "valuation_scores.csv"
MANAGEMENT       = cfg.NSE_DIR / "shareholding" / "management_sentiment.csv"
ML_SCORES        = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"


def _latest_holding_trend(df: pd.DataFrame) -> pd.DataFrame:
    """One row per symbol — most recent quarter by quarter_end_date."""
    d = df.copy()
    d["_sort"] = pd.to_datetime(d["quarter_end_date"], format="%d-%b-%Y", errors="coerce")
    d = d.sort_values("_sort").drop(columns=["_sort"])
    return d.groupby("symbol", as_index=False).last()


def _score_row(r: pd.Series) -> tuple[float, str]:
    score = 50.0

    # 1. Trend / DMA
    trend = r.get("trend_signal")
    if trend == "STRONG_UPTREND":
        score += 18
    elif trend == "UPTREND":
        score += 12
    elif trend == "CONSOLIDATING":
        score += 4
    elif trend == "DOWNTREND":
        score -= 18

    prox = r.get("prox_52w_high")
    if pd.notna(prox):
        if prox >= -3:
            score += 10
        elif prox >= -8:
            score += 6
        elif prox < -35:
            score -= 6

    # 2. F&O / OI signal
    oi_signal = r.get("oi_signal")
    if oi_signal == "LONG_BUILDUP":
        score += 15
    elif oi_signal == "SHORT_COVERING":
        score += 8
    elif oi_signal == "SHORT_BUILDUP":
        score -= 15
    elif oi_signal == "LONG_UNWINDING":
        score -= 10

    # 3. Sector rotation
    s_rot = r.get("sector_rotation_signal")
    if s_rot == "EARLY_ROTATION":
        score += 14
    elif s_rot == "LEADING":
        score += 10
    elif s_rot == "MOMENTUM":
        score += 7
    elif s_rot == "DECLINING":
        score -= 12
    elif s_rot == "LAGGING":
        score -= 5

    # 4. FII / DII / Promoter shareholding trends
    fii_d = r.get("fii_delta")
    if pd.notna(fii_d):
        if fii_d > 0.5:
            score += 9
        elif fii_d < -1:
            score -= 9

    dii_d = r.get("dii_delta")
    if pd.notna(dii_d) and dii_d > 0.5:
        score += 6

    pro_d = r.get("promoter_delta")
    if pd.notna(pro_d) and pro_d < -3:
        score -= 9

    if r.get("conviction_signal") == "STRONG_ACCUMULATION":
        score += 6

    # 5. Fundamentals
    val_label = r.get("valuation_label")
    if val_label == "CHEAP_QUALITY":
        score += 10
    elif val_label == "FAIR_VALUE":
        score += 5
    elif val_label == "EXPENSIVE":
        score -= 8

    yoy_p = r.get("yoy_profit_pct")
    if pd.notna(yoy_p):
        if yoy_p > 20:
            score += 8
        elif yoy_p > 0:
            score += 4
        elif yoy_p < -15:
            score -= 10
        elif yoy_p < 0:
            score -= 5

    yoy_r = r.get("yoy_revenue_pct")
    if pd.notna(yoy_r) and yoy_r > 15:
        score += 5

    roe = r.get("roe_pct")
    if pd.notna(roe) and roe > 20:
        score += 4

    # 6. Management sentiment
    mgmt_score = r.get("management_score")
    if pd.notna(mgmt_score):
        if mgmt_score > 65:
            score += 6
        elif mgmt_score < 35:
            score -= 6
    if r.get("management_label") == "DECLINING":
        score -= 4

    # 7. ML model
    ml_score = r.get("ml_bull_run_score")
    if pd.notna(ml_score):
        if ml_score >= 70:
            score += 6
        elif ml_score < 30:
            score -= 6

    final_score = max(0.0, min(100.0, round(score)))

    hard_exit = trend == "DOWNTREND" or oi_signal == "SHORT_BUILDUP"
    if final_score >= 72 and not hard_exit:
        action = "STRONG_BUY"
    elif final_score >= 58 and not hard_exit:
        action = "BUY"
    elif final_score >= 42:
        action = "HOLD_WATCH"
    elif final_score >= 28:
        action = "REDUCE"
    else:
        action = "EXIT_AVOID"

    return final_score, action


def _entry_stop(r: pd.Series, score: float) -> tuple[float | None, float | None, float | None]:
    close = r.get("close_now")
    if pd.isna(close) or close is None or close <= 0:
        return None, None, None

    entry_low = entry_high = None
    if score >= 58:
        entry_low, entry_high = round(close * 0.99, 2), round(close * 1.02, 2)
    elif score >= 42:
        entry_low, entry_high = round(close * 0.97, 2), round(close * 1.00, 2)

    dma_200 = r.get("dma_200")
    if pd.notna(dma_200) and close > dma_200:
        stop_loss = round(max(dma_200 * 0.98, close * 0.90), 2)
    else:
        stop_loss = round(close * 0.92, 2)

    return entry_low, entry_high, stop_loss


def run() -> dict:
    if not BULL_RUN.exists():
        return {"status": "ERROR", "error": "bull_run_probability.csv not found"}

    base = pd.read_csv(BULL_RUN, usecols=["symbol", "sector", "as_of_date"])
    base["symbol"] = base["symbol"].str.strip().str.upper()
    as_of_date = str(base["as_of_date"].iloc[-1]) if not base.empty else ""
    df = base.drop(columns=["as_of_date"])

    if TECHNICAL.exists():
        tech = pd.read_csv(TECHNICAL, usecols=[
            "symbol", "close_now", "dma_200", "prox_52w_high", "trend_signal"
        ])
        tech["symbol"] = tech["symbol"].str.strip().str.upper()
        df = df.merge(tech, on="symbol", how="left")
    else:
        logger.warning("[TradeConviction] technical_indicators.csv missing")

    if FNO_INTEL.exists():
        fno = pd.read_csv(FNO_INTEL, usecols=["symbol", "oi_signal", "oi_1d"])
        fno["symbol"] = fno["symbol"].str.strip().str.upper()
        df = df.merge(fno, on="symbol", how="left")
    else:
        logger.warning("[TradeConviction] fno_intelligence.csv missing")

    if SECTOR_ROTATION.exists():
        rot = pd.read_csv(SECTOR_ROTATION, usecols=["sector", "rotation_signal"])
        rot = rot.rename(columns={"rotation_signal": "sector_rotation_signal"})
        df = df.merge(rot, on="sector", how="left")
    else:
        logger.warning("[TradeConviction] sector_rotation_intelligence.csv missing")

    if HOLDING_TRENDS.exists():
        ht = pd.read_csv(HOLDING_TRENDS, usecols=[
            "symbol", "quarter_end_date", "fii_delta", "dii_delta",
            "promoter_delta", "conviction_signal"
        ])
        ht["symbol"] = ht["symbol"].str.strip().str.upper()
        ht_latest = _latest_holding_trend(ht)
        df = df.merge(ht_latest.drop(columns=["quarter_end_date"]), on="symbol", how="left")
    else:
        logger.warning("[TradeConviction] holding_trends.csv missing")

    if VALUATION.exists():
        val = pd.read_csv(VALUATION, usecols=[
            "symbol", "valuation_label", "yoy_profit_pct", "yoy_revenue_pct", "roe_pct"
        ])
        val["symbol"] = val["symbol"].str.strip().str.upper()
        df = df.merge(val, on="symbol", how="left")
    else:
        logger.warning("[TradeConviction] valuation_scores.csv missing")

    if MANAGEMENT.exists():
        mgmt = pd.read_csv(MANAGEMENT, usecols=["symbol", "management_score", "management_label"])
        mgmt["symbol"] = mgmt["symbol"].str.strip().str.upper()
        df = df.merge(mgmt, on="symbol", how="left")
    else:
        logger.warning("[TradeConviction] management_sentiment.csv missing")

    if ML_SCORES.exists():
        ml = pd.read_csv(ML_SCORES, usecols=["symbol", "ml_bull_run_score"])
        ml["symbol"] = ml["symbol"].str.strip().str.upper()
        df = df.merge(ml, on="symbol", how="left")
    else:
        logger.warning("[TradeConviction] ml_scores_combined.csv missing")

    if df.empty:
        return {"status": "ERROR", "error": "No symbols in bull_run_probability.csv"}

    logger.info("[TradeConviction] Scoring %d symbols", len(df))

    scores, actions, entry_lows, entry_highs, stops = [], [], [], [], []
    for _, row in df.iterrows():
        score, action = _score_row(row)
        entry_low, entry_high, stop_loss = _entry_stop(row, score)
        scores.append(score)
        actions.append(action)
        entry_lows.append(entry_low)
        entry_highs.append(entry_high)
        stops.append(stop_loss)

    df["score"]      = scores
    df["action"]     = actions
    df["entry_low"]  = entry_lows
    df["entry_high"] = entry_highs
    df["stop_loss"]  = stops
    df["as_of_date"] = as_of_date

    out_cols = [
        "symbol", "sector", "close_now", "score", "action",
        "trend_signal", "prox_52w_high", "oi_signal", "oi_1d",
        "sector_rotation_signal",
        "fii_delta", "dii_delta", "promoter_delta", "conviction_signal",
        "valuation_label", "yoy_profit_pct", "roe_pct",
        "management_score", "management_label",
        "ml_bull_run_score",
        "entry_low", "entry_high", "stop_loss", "as_of_date",
    ]
    df_out = df[[c for c in out_cols if c in df.columns]]

    cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp.csv")
    df_out.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT))
    logger.info("[TradeConviction] Saved %d rows to %s", len(df_out), OUTPUT.name)

    return {
        "status": "DONE",
        "symbols": len(df_out),
        "strong_buy": int((df_out["action"] == "STRONG_BUY").sum()),
        "exit_avoid": int((df_out["action"] == "EXIT_AVOID").sum()),
        "as_of_date": as_of_date,
    }


if __name__ == "__main__":
    r = run()
    print(f"Status:      {r['status']}")
    print(f"Symbols:     {r.get('symbols', 0)}")
    print(f"STRONG_BUY:  {r.get('strong_buy', 0)}")
    print(f"EXIT_AVOID:  {r.get('exit_avoid', 0)}")
    print(f"As of:       {r.get('as_of_date', '')}")
    if r.get("error"):
        print(f"Error:       {r['error']}")
