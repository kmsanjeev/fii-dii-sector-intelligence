"""
Market Router — Phase 10
GET /api/market/regime  — current market regime + participant flow scores
GET /api/market/freshness — data load timestamps for all datasets
"""

import math

from fastapi import APIRouter, HTTPException

from backend.services import data_loader

router = APIRouter(prefix="/api/market", tags=["market"])


def _nullable_float(value, decimals: int = 2):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return round(number, decimals)


@router.get("/regime")
def get_market_regime():
    df = data_loader.get("participant_intel")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="participant_intelligence not loaded")

    df_sorted = df.sort_values("date")
    latest = df_sorted.iloc[-1]

    regime = str(latest.get("Market_Regime", "UNKNOWN"))
    smart_money = _nullable_float(latest.get("Smart_Money_Score"))
    fii_conviction = _nullable_float(latest.get("FII_conviction"), 1)
    data_date = str(latest.get("date", ""))

    flows_df = data_loader.get("participant_flows")
    flow_snapshot = {}
    if flows_df is not None and not flows_df.empty:
        flatest = flows_df.sort_values("date").iloc[-1]
        flow_snapshot = {
            "FII":    _nullable_float(flatest.get("FII_flow_score")),
            "DII":    _nullable_float(flatest.get("DII_flow_score")),
            "PRO":    _nullable_float(flatest.get("PRO_flow_score")),
            "CLIENT": _nullable_float(flatest.get("CLIENT_flow_score")),
        }

    data_status = data_loader.freshness_for(
        ("participant_intel",),
        ("participant_flows", "bull_run"),
    )

    return {
        "regime": regime,
        "smart_money_score": smart_money,
        "fii_conviction_pct": fii_conviction,
        "flow_scores": flow_snapshot,
        "data_date": data_date,
        "data_status": data_status,
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
            return _nullable_float(v, d)
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
            "bull_run":     int(vc.get("BULL_RUN",     0)),
            "emerging":     int(vc.get("EMERGING",     0)),
            "watchlist":    int(vc.get("WATCHLIST",    0)),
            "neutral":      int(vc.get("NEUTRAL",      0)),
            "accumulation": int(vc.get("ACCUMULATION", 0)),
            "markdown":     int(vc.get("MARKDOWN",     0)),
        }

    return {
        **regime_data,
        "pcr":        ctx.get("pcr"),
        "pcr_signal": ctx.get("pcr_signal", "UNKNOWN"),
        "pcr_date":   ctx.get("trade_date", ""),
        "cash_flows": cash,
        "breadth":    breadth,
        "data_status": data_loader.freshness_for(
            ("participant_intel",),
            ("participant_flows", "bull_run"),
        ),
    }


@router.get("/indices")
def get_indices_ticker():
    """Snapshot of key index 30D returns for the ticker tape."""
    df = data_loader.get("index_momentum")
    if df is None or df.empty:
        return {"indices": [], "count": 0}

    KEY = [
        "NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA",
        "NIFTY AUTO", "NIFTY FMCG", "NIFTY REALTY", "NIFTY METAL",
        "NIFTY MIDCAP 150", "NIFTY SMALLCAP 100", "NIFTY NEXT 50",
        "NIFTY INFRASTRUCTURE", "NIFTY MIDCAP 50",
    ]
    result = []
    for name in KEY:
        rows = df[df["INDEX_NAME"] == name]
        if rows.empty:
            continue
        r = rows.iloc[0]
        try:
            ret30  = round(float(r.get("RETURN_30D",  0) or 0), 2)
            ret365 = round(float(r.get("RETURN_365D", 0) or 0), 2)
            mom    = round(float(r.get("MOMENTUM_SCORE", 0) or 0), 2)
        except (TypeError, ValueError):
            ret30 = ret365 = mom = 0.0
        result.append({"name": name, "ret_30d": ret30, "ret_365d": ret365, "momentum_score": mom})

    return {"indices": result, "count": len(result)}


@router.get("/freshness")
def get_freshness():
    # Preserve the legacy load-timestamp keys while adding the governed
    # dataset-level freshness/provenance contract.
    return {
        **data_loader.freshness(),
        "metadata": data_loader.freshness_metadata(),
    }
