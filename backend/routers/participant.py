"""
Participant Router — Phase 10
GET /api/participant/latest    — latest FII/DII/PRO/CLIENT scores + regime
GET /api/participant/history   — time-series flow scores (last N days)
"""

from fastapi import APIRouter, HTTPException, Query
from backend.services import data_loader

router = APIRouter(prefix="/api/participant", tags=["participant"])


@router.get("/latest")
def get_participant_latest():
    df = data_loader.get("participant_intel")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="participant_intelligence not loaded")

    latest = df.sort_values("date").iloc[-1]

    return {
        "date": str(latest.get("date", "")),
        "Market_Regime": str(latest.get("Market_Regime", "")),
        "Smart_Money_Score": round(float(latest.get("Smart_Money_Score", 0) or 0), 2),
        "Retail_Score": round(float(latest.get("Retail_Score", 0) or 0), 2),
        "FII_conviction": round(float(latest.get("FII_conviction", 0) or 0), 1),
        "DII_conviction": round(float(latest.get("DII_conviction", 0) or 0), 1),
        "FII_DII_Divergence": round(float(latest.get("FII_DII_Divergence", 0) or 0), 3),
        "Smart_Retail_Divergence": round(float(latest.get("Smart_Retail_Divergence", 0) or 0), 3),
        "Market_Opportunity": round(float(latest.get("Market_Opportunity", 0) or 0), 2),
        "Ensemble_Score": round(float(latest.get("Ensemble_Score", 0) or 0), 2),
    }


@router.get("/history")
def get_participant_history(limit: int = Query(252, le=2600)):
    flows = data_loader.get("participant_flows")
    if flows is None or flows.empty:
        raise HTTPException(status_code=503, detail="participant_flow_scores not loaded")

    df = flows.sort_values("date").tail(limit)
    cols = [
        "date",
        "FII_flow_score", "DII_flow_score", "PRO_flow_score", "CLIENT_flow_score",
        "FPI_flow_score", "MF_flow_score",
    ]
    available = [c for c in cols if c in df.columns]
    return {
        "rows": df[available].to_dict(orient="records"),
        "count": len(df),
    }
