"""
Market Router — Phase 10
GET /api/market/regime  — current market regime + participant flow scores
GET /api/market/freshness — data load timestamps for all datasets
"""

from fastapi import APIRouter, HTTPException
from backend.services import data_loader

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/regime")
def get_market_regime():
    df = data_loader.get("participant_intel")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="participant_intelligence not loaded")

    df_sorted = df.sort_values("date")
    latest = df_sorted.iloc[-1]

    regime = str(latest.get("Market_Regime", "UNKNOWN"))
    smart_money = float(latest.get("Smart_Money_Score", 0) or 0)
    fii_conviction = float(latest.get("FII_conviction", 0) or 0)
    data_date = str(latest.get("date", ""))

    flows_df = data_loader.get("participant_flows")
    flow_snapshot = {}
    if flows_df is not None and not flows_df.empty:
        flatest = flows_df.sort_values("date").iloc[-1]
        flow_snapshot = {
            "FII":    round(float(flatest.get("FII_flow_score",    0) or 0), 2),
            "DII":    round(float(flatest.get("DII_flow_score",    0) or 0), 2),
            "PRO":    round(float(flatest.get("PRO_flow_score",    0) or 0), 2),
            "CLIENT": round(float(flatest.get("CLIENT_flow_score", 0) or 0), 2),
        }

    return {
        "regime": regime,
        "smart_money_score": round(smart_money, 2),
        "fii_conviction_pct": round(fii_conviction, 1),
        "flow_scores": flow_snapshot,
        "data_date": data_date,
    }


@router.get("/context")
def get_market_context():
    """
    Single endpoint for the dashboard pulse strip.
    Returns regime + PCR + FII/DII/MF cash flows + data date.
    """
    regime_data = get_market_regime()

    # PCR from market_context.json (written by fno_engine)
    ctx = data_loader.get_market_context()

    # Latest cash flows from participant_flows
    flows_df = data_loader.get("participant_flows")
    cash = {}
    if flows_df is not None and not flows_df.empty:
        fl = flows_df.sort_values("date").iloc[-1]
        def _f(v, d=0):
            try:
                return round(float(v or 0), d)
            except (TypeError, ValueError):
                return 0.0
        cash = {
            "fpi_5d_cr":       _f(fl.get("FPI_flow_5D")),
            "mf_5d_cr":        _f(fl.get("MF_flow_5D")),
            "insurance_5d_cr": _f(fl.get("INSURANCE_flow_5D")),
            "fpi_20d_cr":      _f(fl.get("FPI_flow_20D")),
            "mf_20d_cr":       _f(fl.get("MF_flow_20D")),
        }

    # Breadth: label counts across bull_run universe
    bull_df = data_loader.get("bull_run")
    breadth = {}
    if bull_df is not None and not bull_df.empty and "label" in bull_df.columns:
        vc = bull_df["label"].value_counts().to_dict()
        breadth = {
            "strong_candidate": int(vc.get("STRONG_CANDIDATE", 0)),
            "emerging":         int(vc.get("EMERGING", 0)),
            "watchlist":        int(vc.get("WATCHLIST", 0)),
            "neutral":          int(vc.get("NEUTRAL", 0)),
            "avoid":            int(vc.get("AVOID", 0)),
        }

    return {
        **regime_data,
        "pcr":        ctx.get("pcr"),
        "pcr_signal": ctx.get("pcr_signal", "UNKNOWN"),
        "pcr_date":   ctx.get("trade_date", ""),
        "cash_flows": cash,
        "breadth":    breadth,
    }


@router.get("/freshness")
def get_freshness():
    return data_loader.freshness()
