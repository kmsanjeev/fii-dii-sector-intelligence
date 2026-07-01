"""
Corporate Router — Phase 10 + Phase 18
GET /api/corporate/deals                    — institutional deal signals (sortable)
GET /api/corporate/catalysts                — upcoming catalysts (next 60D)
GET /api/corporate/confidence               — corporate confidence scores
GET /api/corporate/events                   — event calendar (recent)
GET /api/corporate/announcements            — Phase 18: recent announcements (filterable)
GET /api/corporate/announcements/{symbol}   — Phase 18: per-symbol announcement history
GET /api/corporate/announcement-signals     — Phase 18: per-symbol 30d signal summary
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


# ── Phase 18 — Corporate Announcements Intelligence ───────────────────────────

@router.get("/announcements")
def get_announcements(
    ann_type: str = Query(None, description="Filter by announcement_type (e.g. RESULT_UPDATE)"),
    min_score: int = Query(0, description="Min signal_score"),
    days: int = Query(30, description="Lookback window in days"),
    limit: int = 200,
):
    df = data_loader.get("announcements")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="company_announcements not loaded")

    import pandas as pd
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    df = df[df["date"] >= cutoff]

    if ann_type:
        df = df[df["announcement_type"].str.upper() == ann_type.upper()]
    if min_score > 0:
        df = df[df["signal_score"].astype(int) >= min_score]

    df = df.sort_values("date", ascending=False).head(limit)
    return {
        "count": len(df),
        "days": days,
        "announcements": _clean(df.to_dict(orient="records")),
    }


@router.get("/announcements/{symbol}")
def get_symbol_announcements(
    symbol: str,
    days: int = Query(90, description="Lookback window in days"),
    limit: int = 100,
):
    df = data_loader.get("announcements")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="company_announcements not loaded")

    import pandas as pd
    sym = symbol.upper()
    df = df[df["symbol"].str.upper() == sym]
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No announcements for '{sym}'")

    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    df = df[df["date"] >= cutoff].sort_values("date", ascending=False).head(limit)
    return {
        "symbol": sym,
        "count": len(df),
        "days": days,
        "announcements": _clean(df.to_dict(orient="records")),
    }


@router.get("/announcement-signals")
def get_announcement_signals(
    min_score_30d: float = Query(0.0),
    ann_type: str = Query(None, description="Filter by dominant_type"),
    limit: int = 100,
):
    df = data_loader.get("announcement_signals")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="announcement_signals not loaded")

    if min_score_30d > 0:
        df = df[df["score_30d"].astype(float) >= min_score_30d]
    if ann_type:
        df = df[df["dominant_type"].str.upper() == ann_type.upper()]

    df = df.sort_values("score_30d", ascending=False).head(limit)
    return {
        "count": len(df),
        "signals": _clean(df.to_dict(orient="records")),
    }
