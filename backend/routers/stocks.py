"""
Stocks Router — Phase 10
GET /api/stocks/watchlist             — EMERGING+ watchlist (sorted by score)
GET /api/stocks/{symbol}              — full bull run breakdown for one symbol
GET /api/stocks/{symbol}/momentum     — price momentum detail
GET /api/stocks                       — all 2441 symbols (paginated)
"""

import math
from fastapi import APIRouter, HTTPException, Query
from backend.services import data_loader


def _clean(records):
    cleaned = []
    for rec in records:
        cleaned.append({
            k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in rec.items()
        })
    return cleaned

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/watchlist")
def get_watchlist(label: str = "EMERGING", limit: int = 50):
    df = data_loader.get("bull_run_watchlist")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="bull_run_watchlist not loaded")

    filtered = df[df["label"] == label] if label != "ALL" else df
    filtered = filtered.nlargest(limit, "bull_run_score")
    return {
        "label": label,
        "count": len(filtered),
        "stocks": _clean(filtered.to_dict(orient="records")),
    }


@router.get("")
def get_all_stocks(
    label: str = Query(None, description="Filter by label (STRONG_CANDIDATE, EMERGING, etc.)"),
    sector: str = Query(None),
    page: int = 1,
    per_page: int = 100,
):
    df = data_loader.get("bull_run")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="bull_run_probability not loaded")

    if label:
        df = df[df["label"] == label]
    if sector:
        df = df[df["sector"].str.upper() == sector.upper()]

    df = df.sort_values("bull_run_score", ascending=False)
    total = len(df)
    start = (page - 1) * per_page
    page_df = df.iloc[start: start + per_page]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "stocks": _clean(page_df.to_dict(orient="records")),
    }


@router.get("/{symbol}")
def get_stock_detail(symbol: str):
    bull_df = data_loader.get("bull_run")
    if bull_df is None or bull_df.empty:
        raise HTTPException(status_code=503, detail="bull_run_probability not loaded")

    sym = symbol.upper()
    matched = bull_df[bull_df["symbol"].str.upper() == sym]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Symbol '{sym}' not found")

    row = matched.iloc[0]

    # Deal signals
    deal_df = data_loader.get("deal_signals")
    deal_info = {}
    if deal_df is not None:
        deal_row = deal_df[deal_df["symbol"].str.upper() == sym]
        if not deal_row.empty:
            deal_info = deal_row.iloc[0].to_dict()

    # Corporate confidence
    corp_df = data_loader.get("corporate_confidence")
    corp_info = {}
    if corp_df is not None:
        corp_row = corp_df[corp_df["symbol"].str.upper() == sym]
        if not corp_row.empty:
            corp_info = corp_row.iloc[0].to_dict()

    return {
        "symbol":             str(row.get("symbol", "")),
        "sector":             str(row.get("sector", "")),
        "bull_run_score":     round(float(row.get("bull_run_score", 0) or 0), 2),
        "label":              str(row.get("label", "")),
        "market_regime":      str(row.get("market_regime", "")),
        "regime_multiplier":  float(row.get("regime_multiplier", 1.0) or 1.0),
        "components": {
            "price_score":        round(float(row.get("price_score",        0) or 0), 2),
            "sector_flow_score":  round(float(row.get("sector_flow_score",  0) or 0), 2),
            "deal_score":         round(float(row.get("deal_score",         0) or 0), 2),
            "corporate_score":    round(float(row.get("corporate_score",    0) or 0), 2),
        },
        "price": {
            "ret_30d":   row.get("ret_30d"),
            "ret_90d":   row.get("ret_90d"),
            "ret_365d":  row.get("ret_365d"),
            "vol_ratio": row.get("vol_ratio"),
        },
        "as_of_date": str(row.get("as_of_date", "")),
        "deal_signals":         deal_info,
        "corporate_confidence": corp_info,
    }


@router.get("/{symbol}/momentum")
def get_stock_momentum(symbol: str):
    df = data_loader.get("price_momentum")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="price_momentum not loaded")

    sym = symbol.upper()
    matched = df[df["symbol"].str.upper() == sym]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Symbol '{sym}' not found in momentum data")

    return matched.iloc[0].to_dict()
