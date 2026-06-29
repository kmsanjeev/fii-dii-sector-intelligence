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


@router.get("/freshness")
def get_freshness():
    return data_loader.freshness()
