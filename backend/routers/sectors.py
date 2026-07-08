"""
Sectors Router — Phase 10
GET /api/sectors              — all sectors snapshot (rotation_signal, scores + FPI signals)
GET /api/sectors/fpi          — FPI-only snapshot sorted by signal_score (Phase FPI)
GET /api/sectors/history      — time-series sector flow data
GET /api/sectors/{sector}     — single sector detail + top stocks + FPI history
"""

import math
from fastapi import APIRouter, HTTPException
from backend.services import data_loader


def _safe_float(val, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if math.isnan(f) or math.isinf(f) else round(f, 2)
    except (TypeError, ValueError):
        return default


def _clean_records(records: list) -> list:
    return [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in rec.items()}
        for rec in records
    ]


def _fpi_snapshot() -> dict:
    """
    Return {sector_normalized: {...fpi fields...}} from the latest available FPI date.
    Returns empty dict if fpi_signals not loaded.
    """
    df = data_loader.get("fpi_signals")
    if df is None or df.empty:
        return {}
    latest = df["date"].max()
    snap = df[df["date"] == latest]
    result = {}
    for _, row in snap.iterrows():
        sector = str(row.get("sector_normalized", ""))
        if not sector:
            continue
        result[sector] = {
            "fpi_date":        latest,
            "fpi_signal":      str(row.get("fpi_signal", "NEUTRAL")),
            "fpi_score":       _safe_float(row.get("signal_score")),
            "auc_equity_crore": _safe_float(row.get("auc_equity_crore")),
            "auc_pct_of_total": _safe_float(row.get("auc_pct_of_total")),
            "auc_z":           _safe_float(row.get("auc_z52")),
            "net_z":           _safe_float(row.get("net_z52")),
            "qoq_auc_delta_pct": _safe_float(row.get("qoq_auc_delta_pct")),
        }
    return result


router = APIRouter(prefix="/api/sectors", tags=["sectors"])


@router.get("")
def get_sectors():
    df = data_loader.get("sector_rotation")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="sector_rotation_intelligence not loaded")

    fpi = _fpi_snapshot()

    records = []
    for _, row in df.iterrows():
        sector = str(row.get("sector", ""))
        fpi_data = fpi.get(sector, {})
        records.append({
            "sector":            sector,
            "rotation_signal":   str(row.get("rotation_signal", "")),
            "combined_score":    _safe_float(row.get("combined_score")),
            "FII_flow_score":    _safe_float(row.get("FII_flow_score")),
            "DII_flow_score":    _safe_float(row.get("DII_flow_score")),
            "Smart_Money_Score": _safe_float(row.get("Smart_Money_Score")),
            "fpi_score":         _safe_float(row.get("fpi_score")),
            "last_date":         str(row.get("last_date", "")),
            # FPI ownership fields
            "fpi_signal":        fpi_data.get("fpi_signal", ""),
            "fpi_date":          fpi_data.get("fpi_date", ""),
            "auc_equity_crore":  fpi_data.get("auc_equity_crore"),
            "auc_pct_of_total":  fpi_data.get("auc_pct_of_total"),
            "auc_z":             fpi_data.get("auc_z"),
            "net_z":             fpi_data.get("net_z"),
            "qoq_auc_delta_pct": fpi_data.get("qoq_auc_delta_pct"),
        })

    records.sort(key=lambda r: (r["combined_score"] or 0), reverse=True)
    return {
        "sectors":   _clean_records(records),
        "count":     len(records),
        "fpi_date":  list(fpi.values())[0]["fpi_date"] if fpi else None,
    }


@router.get("/fpi")
def get_fpi_snapshot():
    """
    FPI sector ownership snapshot — latest fortnightly data from NSDL/CDSL.
    Sorted by signal_score descending (strongest accumulation first).
    """
    df = data_loader.get("fpi_signals")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="fpi_signals not loaded")

    latest = df["date"].max()
    snap = df[df["date"] == latest].copy()

    records = []
    for _, row in snap.iterrows():
        records.append({
            "sector":            str(row.get("sector_normalized", "")),
            "fpi_signal":        str(row.get("fpi_signal", "NEUTRAL")),
            "fpi_score":         _safe_float(row.get("signal_score")),
            "auc_equity_crore":  _safe_float(row.get("auc_equity_crore")),
            "auc_pct_of_total":  _safe_float(row.get("auc_pct_of_total")),
            "auc_z":             _safe_float(row.get("auc_z52")),
            "net_z":             _safe_float(row.get("net_z52")),
            "qoq_auc_delta_pct": _safe_float(row.get("qoq_auc_delta_pct")),
            "source":            str(row.get("source", "")),
        })

    records.sort(key=lambda r: (r["fpi_score"] or 0), reverse=True)
    return {
        "sectors": _clean_records(records),
        "count":   len(records),
        "date":    str(latest),
    }


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
        "rows":   _clean_records(df.to_dict(orient="records")),
        "count":  len(df),
    }


@router.get("/{sector}/fpi-history")
def get_sector_fpi_history(sector: str, limit: int = 52):
    """
    FPI AUC + net investment time-series for a single sector.
    Returns up to `limit` most recent fortnightly data points.
    """
    df = data_loader.get("fpi_signals")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="fpi_signals not loaded")

    matched = df[df["sector_normalized"].str.upper() == sector.upper()]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found in FPI data")

    matched = matched.sort_values("date").tail(limit)
    records = []
    for _, row in matched.iterrows():
        records.append({
            "date":              str(row.get("date", "")),
            "auc_equity_crore":  _safe_float(row.get("auc_equity_crore")),
            "net_inv_equity_crore": _safe_float(row.get("net_inv_equity_crore")),
            "auc_pct_of_total":  _safe_float(row.get("auc_pct_of_total")),
            "auc_z":             _safe_float(row.get("auc_z52")),
            "net_z":             _safe_float(row.get("net_z52")),
            "fpi_signal":        str(row.get("fpi_signal", "NEUTRAL")),
            "signal_score":      _safe_float(row.get("signal_score")),
        })
    return {
        "sector": sector.upper(),
        "rows":   _clean_records(records),
        "count":  len(records),
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
    fpi = _fpi_snapshot().get(sector.upper(), {})

    # Top stocks in this sector from bull run
    bull_df = data_loader.get("bull_run")
    top_stocks = []
    if bull_df is not None:
        sector_stocks = bull_df[
            bull_df["sector"].str.upper() == sector.upper()
        ].nlargest(10, "bull_run_score")
        top_stocks = sector_stocks[["symbol", "bull_run_score", "label"]].to_dict(orient="records")

    return {
        "sector":            str(row.get("sector", "")),
        "rotation_signal":   str(row.get("rotation_signal", "")),
        "combined_score":    _safe_float(row.get("combined_score")),
        "FII_flow_score":    _safe_float(row.get("FII_flow_score")),
        "DII_flow_score":    _safe_float(row.get("DII_flow_score")),
        "Smart_Money_Score": _safe_float(row.get("Smart_Money_Score")),
        "fpi_score":         _safe_float(row.get("fpi_score")),
        "price_momentum_score": _safe_float(row.get("price_momentum_score")),
        "last_date":         str(row.get("last_date", "")),
        # FPI ownership block
        "fpi_signal":        fpi.get("fpi_signal", ""),
        "fpi_date":          fpi.get("fpi_date", ""),
        "auc_equity_crore":  fpi.get("auc_equity_crore"),
        "auc_pct_of_total":  fpi.get("auc_pct_of_total"),
        "auc_z":             fpi.get("auc_z"),
        "net_z":             fpi.get("net_z"),
        "qoq_auc_delta_pct": fpi.get("qoq_auc_delta_pct"),
        "top_stocks":        top_stocks,
    }
