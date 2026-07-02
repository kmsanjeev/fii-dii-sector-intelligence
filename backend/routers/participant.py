"""
Participant Router — Phase 10 + Phase A enrichment
GET /api/participant/latest    — latest scores, flow scores, cash market flows
GET /api/participant/history   — time-series flow scores (last N days)
"""

from fastapi import APIRouter, HTTPException, Query
from backend.services import data_loader

router = APIRouter(prefix="/api/participant", tags=["participant"])


def _f(v, decimals=2):
    try:
        return round(float(v or 0), decimals)
    except (TypeError, ValueError):
        return 0.0


@router.get("/latest")
def get_participant_latest():
    df = data_loader.get("participant_intel")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="participant_intelligence not loaded")

    latest = df.sort_values("date").iloc[-1]

    # Cash market 5-day net flows (FPI = FII cash, MF = mutual funds, INSURANCE, RETAIL)
    flows_df = data_loader.get("participant_flows")
    cash = {}
    if flows_df is not None and not flows_df.empty:
        fl = flows_df.sort_values("date").iloc[-1]
        cash = {
            "fpi_5d_cr":        _f(fl.get("FPI_flow_5D"),    0),
            "mf_5d_cr":         _f(fl.get("MF_flow_5D"),     0),
            "insurance_5d_cr":  _f(fl.get("INSURANCE_flow_5D"), 0),
            "retail_5d_cr":     _f(fl.get("RETAIL_flow_5D"), 0),
            "fpi_20d_cr":       _f(fl.get("FPI_flow_20D"),   0),
            "mf_20d_cr":        _f(fl.get("MF_flow_20D"),    0),
        }

    return {
        "date":                   str(latest.get("date", "")),
        "Market_Regime":          str(latest.get("Market_Regime", "")),
        # Flow scores (fixes score=0 bug — these are the actual z-scores)
        "FII_flow_score":         _f(latest.get("FII_flow_score")),
        "DII_flow_score":         _f(latest.get("DII_flow_score")),
        "PRO_flow_score":         _f(latest.get("PRO_flow_score")),
        "CLIENT_flow_score":      _f(latest.get("CLIENT_flow_score")),
        "FPI_flow_score":         _f(latest.get("FPI_flow_score")),
        "MF_flow_score":          _f(latest.get("MF_flow_score")),
        "INSURANCE_flow_score":   _f(latest.get("INSURANCE_flow_score")),
        "RETAIL_flow_score":      _f(latest.get("RETAIL_flow_score")),
        # Conviction levels
        "FII_conviction":         _f(latest.get("FII_conviction"), 1),
        "DII_conviction":         _f(latest.get("DII_conviction"), 1),
        # Derived signals
        "Smart_Money_Score":      _f(latest.get("Smart_Money_Score")),
        "Retail_Score":           _f(latest.get("Retail_Score")),
        "Cash_Institutional_Score": _f(latest.get("Cash_Institutional_Score")),
        "FII_DII_Divergence":     _f(latest.get("FII_DII_Divergence"), 3),
        "Smart_Retail_Divergence":_f(latest.get("Smart_Retail_Divergence"), 3),
        "Market_Opportunity":     _f(latest.get("Market_Opportunity")),
        "Ensemble_Score":         _f(latest.get("Ensemble_Score")),
        # Cash market net flows (Cr)
        "cash_flows":             cash,
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
        "FPI_flow_score", "MF_flow_score", "INSURANCE_flow_score", "RETAIL_flow_score",
        "FPI_flow_5D", "MF_flow_5D",
    ]
    available = [c for c in cols if c in df.columns]
    return {
        "rows":  df[available].to_dict(orient="records"),
        "count": len(df),
    }
