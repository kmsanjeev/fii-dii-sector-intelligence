"""
Corporate Router — Phase 10
GET /api/corporate/deals           — institutional deal signals (sortable)
GET /api/corporate/catalysts       — upcoming catalysts (next 60D)
GET /api/corporate/confidence      — corporate confidence scores
GET /api/corporate/events          — event calendar (recent)
"""

import math
from fastapi import APIRouter, HTTPException, Query
from backend.services import data_loader


def _clean(records):
    return [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in rec.items()}
        for rec in records
    ]

router = APIRouter(prefix="/api/corporate", tags=["corporate"])


@router.get("/deals")
def get_deals(
    min_cr: float = Query(0.0, description="Min absolute inst_net_value_cr"),
    limit: int = 50,
):
    df = data_loader.get("deal_signals")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="institutional_deal_signals not loaded")

    if min_cr > 0:
        df = df[df["inst_net_value_cr"].fillna(0).abs() >= min_cr]

    df = df.sort_values("inst_net_value_cr", ascending=False).head(limit)
    return {
        "count": len(df),
        "deals": _clean(df.to_dict(orient="records")),
    }


@router.get("/catalysts")
def get_upcoming_catalysts():
    df = data_loader.get("upcoming_catalysts")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="upcoming_catalysts not loaded")

    return {
        "count": len(df),
        "catalysts": _clean(df.to_dict(orient="records")),
    }


@router.get("/confidence")
def get_corporate_confidence(
    min_score: float = Query(0.0),
    limit: int = 100,
):
    df = data_loader.get("corporate_confidence")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="corporate_confidence_scores not loaded")

    if min_score > 0:
        df = df[df["confidence_score_12m"].fillna(0) >= min_score]

    df = df.sort_values("confidence_score_12m", ascending=False).head(limit)
    return {
        "count": len(df),
        "confidence_scores": _clean(df.to_dict(orient="records")),
    }


@router.get("/events")
def get_events(limit: int = 100):
    df = data_loader.get("event_calendar")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="event_calendar not loaded")

    date_col = "event_date" if "event_date" in df.columns else "date"
    df = df.sort_values(date_col, ascending=False).head(limit)
    return {
        "count": len(df),
        "events": _clean(df.to_dict(orient="records")),
    }
