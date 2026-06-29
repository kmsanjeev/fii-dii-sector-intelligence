"""
Sectors Router — Phase 10
GET /api/sectors              — all 29 sectors snapshot (rotation_signal, scores)
GET /api/sectors/{sector}     — single sector detail + top stocks
GET /api/sectors/history      — time-series sector flow data
"""

import math
from fastapi import APIRouter, HTTPException
from backend.services import data_loader


def _clean_records(records: list) -> list:
    """Replace float NaN with None for JSON compliance."""
    cleaned = []
    for rec in records:
        cleaned.append({
            k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in rec.items()
        })
    return cleaned

router = APIRouter(prefix="/api/sectors", tags=["sectors"])


@router.get("")
def get_sectors():
    df = data_loader.get("sector_rotation")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="sector_rotation_intelligence not loaded")

    records = []
    for _, row in df.iterrows():
        records.append({
            "sector":           str(row.get("sector", "")),
            "rotation_signal":  str(row.get("rotation_signal", "")),
            "combined_score":   round(float(row.get("combined_score", 0) or 0), 2),
            "FII_flow_score":   round(float(row.get("FII_flow_score",  0) or 0), 2),
            "DII_flow_score":   round(float(row.get("DII_flow_score",  0) or 0), 2),
            "Smart_Money_Score":round(float(row.get("Smart_Money_Score",0) or 0), 2),
            "last_date":        str(row.get("last_date", "")),
        })

    records.sort(key=lambda r: (r["combined_score"] or 0), reverse=True)
    return {"sectors": _clean_records(records), "count": len(records)}


@router.get("/history")
def get_sector_history(sector: str = None, limit: int = 252):
    df = data_loader.get("sector_flows")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="sector_flow_scores not loaded")

    if sector:
        df = df[df["sector"].str.upper() == sector.upper()]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")

    df = df.sort_values("date").tail(limit)
    return {
        "sector": sector or "ALL",
        "rows": _clean_records(df.to_dict(orient="records")),
        "count": len(df),
    }


@router.get("/{sector}")
def get_sector_detail(sector: str):
    df = data_loader.get("sector_rotation")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="sector_rotation_intelligence not loaded")

    matched = df[df["sector"].str.upper() == sector.upper()]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")

    row = matched.iloc[0]

    # Top stocks in this sector from bull run
    bull_df = data_loader.get("bull_run")
    top_stocks = []
    if bull_df is not None:
        sector_stocks = bull_df[
            bull_df["sector"].str.upper() == sector.upper()
        ].nlargest(10, "bull_run_score")
        top_stocks = sector_stocks[["symbol", "bull_run_score", "label"]].to_dict(orient="records")

    return {
        "sector":           str(row.get("sector", "")),
        "rotation_signal":  str(row.get("rotation_signal", "")),
        "combined_score":   round(float(row.get("combined_score", 0) or 0), 2),
        "FII_flow_score":   round(float(row.get("FII_flow_score",  0) or 0), 2),
        "DII_flow_score":   round(float(row.get("DII_flow_score",  0) or 0), 2),
        "Smart_Money_Score":round(float(row.get("Smart_Money_Score",0) or 0), 2),
        "last_date":        str(row.get("last_date", "")),
        "top_stocks":       top_stocks,
    }
