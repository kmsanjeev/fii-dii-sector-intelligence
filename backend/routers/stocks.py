"""
Stocks Router — Phase 10
GET /api/stocks/watchlist             — EMERGING+ watchlist (sorted by score)
GET /api/stocks/{symbol}              — full bull run breakdown for one symbol
GET /api/stocks/{symbol}/momentum     — price momentum detail
GET /api/stocks                       — all 2441 symbols (paginated)
"""

import math
import pandas as pd
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


def _safe(v):
    """Return None for NaN floats so JSON serialization never fails."""
    if isinstance(v, float) and math.isnan(v):
        return None
    return v

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

    # Phase 15B — Valuation
    fundamentals: dict = {}
    val_df = data_loader.get("valuation_scores")
    if val_df is not None:
        val_row = val_df[val_df["symbol"].str.upper() == sym]
        if not val_row.empty:
            r = val_row.iloc[0]
            fundamentals = {
                "pe_ratio":         _safe(r.get("pe_ratio")),
                "roe_pct":          _safe(r.get("roe_pct")),
                "valuation_score":  _safe(r.get("valuation_score")),
                "valuation_label":  str(r.get("valuation_label", "")),
                "revenue_ttm_cr":   _safe(r.get("revenue_ttm_cr")),
                "profit_ttm_cr":    _safe(r.get("profit_ttm_cr")),
                "yoy_revenue_pct":  _safe(r.get("yoy_revenue_pct")),
                "yoy_profit_pct":   _safe(r.get("yoy_profit_pct")),
                "as_of_date":       str(r.get("as_of_date", "")),
            }

    # Phase 15C — Shareholding (latest quarter per symbol)
    shareholding: dict = {}
    shp_df = data_loader.get("shareholding")
    if shp_df is not None:
        shp_rows = shp_df[shp_df["symbol"].str.upper() == sym]
        if not shp_rows.empty:
            shp_rows = shp_rows.sort_values("quarter_end_date")
            r = shp_rows.iloc[-1]
            shareholding = {
                "promoter_pct":     _safe(r.get("promoter_pct")),
                "fii_pct":          _safe(r.get("fii_pct")),
                "dii_pct":          _safe(r.get("dii_pct")),
                "public_pct":       _safe(r.get("public_pct")),
                "quarter_end_date": str(r.get("quarter_end_date", "")),
                "window_label":     str(r.get("window_label", "")),
            }

    # Phase 16 — Holding Trends (all quarters, sorted oldest first)
    holding_trends: list = []
    ht_df = data_loader.get("holding_trends")
    if ht_df is not None:
        ht_rows = ht_df[ht_df["symbol"].str.upper() == sym].copy()
        if not ht_rows.empty:
            ht_rows["_sort"] = pd.to_datetime(ht_rows["quarter_end_date"], format="%d-%b-%Y", errors="coerce")
            ht_rows = ht_rows.sort_values("_sort").drop(columns=["_sort"])
            for _, r in ht_rows.iterrows():
                holding_trends.append({
                    "period":           str(r.get("period", "")),
                    "quarter_end_date": str(r.get("quarter_end_date", "")),
                    "promoter_pct":     _safe(r.get("promoter_pct")),
                    "fii_pct":          _safe(r.get("fii_pct")),
                    "dii_pct":          _safe(r.get("dii_pct")),
                    "public_pct":       _safe(r.get("public_pct")),
                    "promoter_delta":   _safe(r.get("promoter_delta")),
                    "fii_delta":        _safe(r.get("fii_delta")),
                    "dii_delta":        _safe(r.get("dii_delta")),
                    "conviction_signal": str(r.get("conviction_signal", "")),
                })

    # Phase 16 — Management Sentiment
    management: dict = {}
    ms_df = data_loader.get("management_sentiment")
    if ms_df is not None:
        ms_row = ms_df[ms_df["symbol"].str.upper() == sym]
        if not ms_row.empty:
            r = ms_row.iloc[0]
            management = {
                "holding_signal":      str(r.get("holding_signal", "")),
                "holding_score":       _safe(r.get("holding_score")),
                "announcement_score":  _safe(r.get("announcement_score")),
                "ai_tone_score":       _safe(r.get("ai_tone_score")),
                "management_score":    _safe(r.get("management_score")),
                "management_label":    str(r.get("management_label", "")),
                "announcement_types":  str(r.get("announcement_types", "")),
                "as_of_date":          str(r.get("as_of_date", "")),
            }

    # ML scores
    ml_scores: dict = {}
    ml_df = data_loader.get("ml_scores")
    if ml_df is not None:
        ml_row = ml_df[ml_df["symbol"].str.upper() == sym]
        if not ml_row.empty:
            r = ml_row.iloc[0]
            ml_scores = {
                "accumulation_score": _safe(r.get("accumulation_score")),
                "ml_bull_run_score":  _safe(r.get("ml_bull_run_score")),
            }

    # Technical indicators
    technical: dict = {}
    tech_df = data_loader.get("technical")
    if tech_df is not None:
        tech_row = tech_df[tech_df["symbol"].str.upper() == sym]
        if not tech_row.empty:
            r = tech_row.iloc[0]
            technical = {
                "close_now":      _safe(r.get("close_now")),
                "high_52w":       _safe(r.get("high_52w")),
                "low_52w":        _safe(r.get("low_52w")),
                "prox_52w_high":  _safe(r.get("prox_52w_high")),
                "prox_52w_low":   _safe(r.get("prox_52w_low")),
                "dma_20":         _safe(r.get("dma_20")),
                "dma_50":         _safe(r.get("dma_50")),
                "dma_200":        _safe(r.get("dma_200")),
                "vs_dma_20":      _safe(r.get("vs_dma_20")),
                "vs_dma_50":      _safe(r.get("vs_dma_50")),
                "vs_dma_200":     _safe(r.get("vs_dma_200")),
                "trend_signal":   str(r.get("trend_signal", "")),
                "vol_20d_avg":    _safe(r.get("vol_20d_avg")),
                "as_of_date":     str(r.get("as_of_date", "")),
            }

    # F&O intelligence
    fno: dict = {}
    fno_df = data_loader.get("fno_intel")
    if fno_df is not None:
        fno_row = fno_df[fno_df["symbol"].str.upper() == sym]
        if not fno_row.empty:
            r = fno_row.iloc[0]
            fno = {
                "futures_oi":  _safe(r.get("futures_oi")),
                "oi_1d":       _safe(r.get("oi_1d")),
                "oi_5d":       _safe(r.get("oi_5d")),
                "oi_signal":   str(r.get("oi_signal", "")),
                "fut_close":   _safe(r.get("fut_close")),
                "expiry":      str(r.get("expiry", "")),
                "as_of_date":  str(r.get("as_of_date", "")),
            }

    # Next catalyst
    catalyst: dict = {}
    cat_df = data_loader.get("upcoming_catalysts")
    if cat_df is not None:
        cat_row = cat_df[cat_df["symbol"].str.upper() == sym] if "symbol" in cat_df.columns else pd.DataFrame()
        if not cat_row.empty:
            r = cat_row.iloc[0]
            catalyst = {
                "event_date":    str(r.get("event_date", "")),
                "purpose_type":  str(r.get("purpose_type", "")),
                "catalyst_score": _safe(r.get("catalyst_score")),
            }

    return {
        "symbol":             str(row.get("symbol", "")),
        "sector":             str(row.get("sector", "")),
        "close_now":          _safe(row.get("close_now")),
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
            "ret_30d":   _safe(row.get("ret_30d")),
            "ret_90d":   _safe(row.get("ret_90d")),
            "ret_365d":  _safe(row.get("ret_365d")),
            "vol_ratio": _safe(row.get("vol_ratio")),
        },
        "as_of_date":           str(row.get("as_of_date", "")),
        "deal_signals":         deal_info,
        "corporate_confidence": corp_info,
        "fundamentals":         fundamentals,
        "shareholding":         shareholding,
        "holding_trends":       holding_trends,
        "management":           management,
        "ml_scores":            ml_scores,
        "technical":            technical,
        "fno":                  fno,
        "catalyst":             catalyst,
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
