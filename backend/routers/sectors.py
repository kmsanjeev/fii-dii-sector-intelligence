"""
Sectors Router — Phase 10
GET /api/sectors              — all sectors snapshot (rotation_signal, scores + FPI signals)
GET /api/sectors/fpi          — FPI-only snapshot sorted by signal_score (Phase FPI)
GET /api/sectors/history      — time-series sector flow data
GET /api/sectors/{sector}     — single sector detail + top stocks + FPI history
"""

import json
import math

from fastapi import APIRouter, HTTPException

from backend.services import data_loader


def _safe_float(val, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if math.isnan(f) or math.isinf(f) else round(f, 2)
    except (TypeError, ValueError):
        return default


def _nullable_float(val) -> float | None:
    """Return None for NaN/inf/missing — used where 0.0 would be a misleading default."""
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 2)
    except (TypeError, ValueError):
        return None


def _clean_records(records: list) -> list:
    return [
        {
            k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in rec.items()
        }
        for rec in records
    ]


def _json_field(row, key: str, default):
    value = row.get(key)
    if (
        value is None
        or (isinstance(value, float) and math.isnan(value))
        or str(value).strip() in {"", "nan"}
    ):
        return default
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return default


def _sector_contract_fields(row) -> dict:
    """Additive sector-rotation contract fields; legacy fields remain intact."""
    return {
        "contract_version": str(row.get("contract_version", "sector-rotation-1.0")),
        "as_of": str(row.get("last_date", row.get("date", ""))),
        "taxonomy": str(row.get("taxonomy", "platform sector taxonomy")),
        "constituent_universe": str(row.get("constituent_universe", "UNKNOWN")),
        "performance": {
            "windows": {
                str(w): _nullable_float(row.get(f"sector_return_{w.lower()}"))
                for w in ("1D", "3D", "5D", "10D", "20D")
            },
            "benchmark": str(row.get("benchmark", "")),
            "benchmark_windows": {
                str(w): _nullable_float(row.get(f"benchmark_return_{w.lower()}"))
                for w in ("5D", "20D")
            },
            "relative_strength_windows": {
                str(w): _nullable_float(row.get(f"relative_return_{w.lower()}"))
                for w in ("1D", "3D", "5D", "10D", "20D")
            },
            "relative_strength_score": _nullable_float(
                row.get("relative_strength_score")
            ),
        },
        "breadth": {
            "window": "5D",
            "positive_pct": _nullable_float(row.get("breadth_5d_positive_pct")),
            "expected_constituents": _nullable_float(row.get("breadth_5d_expected")),
            "usable_constituents": _nullable_float(row.get("breadth_5d_usable")),
            "coverage_pct": _nullable_float(row.get("breadth_5d_coverage_pct")),
            "positive_1d_pct": _nullable_float(row.get("breadth_1d_positive_pct")),
            "positive_20d_pct": _nullable_float(row.get("breadth_20d_positive_pct")),
        },
        "leadership": {
            "rank_5d": _nullable_float(row.get("relative_strength_rank_5d")),
            "score": _nullable_float(row.get("leadership_score")),
            "state": str(row.get("leadership_state", "INSUFFICIENT_HISTORY")),
            "persistence": str(row.get("persistence_state", "INSUFFICIENT_HISTORY")),
            "observations": _nullable_float(row.get("persistence_observations")),
        },
        "rotation": {
            "state": str(row.get("rotation_state", "INSUFFICIENT_HISTORY")),
            "rank_change_5d": _nullable_float(row.get("rank_change_5d")),
            "acceleration": str(row.get("acceleration_state", "UNAVAILABLE")),
        },
        "date_alignment": {
            "state": str(row.get("date_alignment_state", "UNKNOWN")),
            "sector_price_date": row.get("sector_price_as_of"),
            "benchmark_date": row.get("benchmark_price_as_of"),
            "institutional_date": row.get("institutional_as_of"),
            "fpi_date": row.get("fpi_as_of"),
        },
        "institutional_context": {
            "scope": str(row.get("institutional_context_scope", "NOT_SUPPORTED")),
            "evidence_type": str(row.get("institutional_evidence_type", "UNAVAILABLE")),
            "as_of": row.get("institutional_as_of"),
            "limitations": [
                "Broad participant positioning is context only; no sector-specific FII/DII attribution is claimed."
            ],
        },
        "evidence_quality": str(row.get("evidence_quality", "INSUFFICIENT")),
        "leaders": _json_field(row, "leaders_json", []),
        "laggards": _json_field(row, "laggards_json", []),
        "facts": _json_field(row, "facts_json", {}),
        "signals": _json_field(row, "signals_json", {}),
        "interpretation": str(row.get("interpretation", "")),
        "limitations": _json_field(row, "limitations_json", []),
    }


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
            "fpi_date": latest,
            "fpi_signal": str(row.get("fpi_signal", "NEUTRAL")),
            "fpi_score": _safe_float(row.get("signal_score")),
            "auc_equity_crore": _safe_float(row.get("auc_equity_crore")),
            "auc_pct_of_total": _safe_float(row.get("auc_pct_of_total")),
            "auc_z": _safe_float(row.get("auc_z52")),
            "net_z": _safe_float(row.get("net_z52")),
            "qoq_auc_delta_pct": _safe_float(row.get("qoq_auc_delta_pct")),
        }
    return result


router = APIRouter(prefix="/api/sectors", tags=["sectors"])


@router.get("")
def get_sectors():
    df = data_loader.get("sector_rotation")
    if df is None or df.empty:
        raise HTTPException(
            status_code=503, detail="sector_rotation_intelligence not loaded"
        )

    fpi = _fpi_snapshot()

    records = []
    for _, row in df.iterrows():
        sector = str(row.get("sector", ""))
        fpi_data = fpi.get(sector, {})
        records.append(
            {
                "sector": sector,
                "rotation_signal": str(row.get("rotation_signal", "")),
                "combined_score": _nullable_float(row.get("combined_score")),
                "FII_flow_score": _nullable_float(row.get("FII_flow_score")),
                "DII_flow_score": _nullable_float(row.get("DII_flow_score")),
                "Smart_Money_Score": _nullable_float(row.get("Smart_Money_Score")),
                "fpi_score": _nullable_float(row.get("fpi_score")),
                "last_date": str(row.get("last_date", "")),
                # FPI ownership fields
                "fpi_signal": fpi_data.get("fpi_signal", ""),
                "fpi_date": fpi_data.get("fpi_date", ""),
                "auc_equity_crore": fpi_data.get("auc_equity_crore"),
                "auc_pct_of_total": fpi_data.get("auc_pct_of_total"),
                "auc_z": fpi_data.get("auc_z"),
                "net_z": fpi_data.get("net_z"),
                "qoq_auc_delta_pct": fpi_data.get("qoq_auc_delta_pct"),
                **_sector_contract_fields(row),
            }
        )

    # Cross-sectional relative score: rank sectors by combined_score today → rescale to ±100.
    # Best sector = +100, worst = -100, regime-neutral — always readable regardless of
    # whether FII is net buying or net selling across the board.
    valid = [(i, r) for i, r in enumerate(records) if r["combined_score"] is not None]
    valid.sort(key=lambda x: x[1]["combined_score"])  # ascending: worst → best
    n = len(valid)
    for rank_idx, (orig_idx, _) in enumerate(valid):
        rel = round((rank_idx / (n - 1)) * 200 - 100, 1) if n > 1 else 0.0
        records[orig_idx]["relative_score"] = rel
    for r in records:
        if "relative_score" not in r:
            r["relative_score"] = None

    records.sort(key=lambda r: r["relative_score"] or -200, reverse=True)

    # FII regime: fraction of sectors with negative FII_flow_score → context for UI
    fii_scores = [
        r["FII_flow_score"] for r in records if r["FII_flow_score"] is not None
    ]
    fii_neg_pct = (
        round(sum(1 for s in fii_scores if s < 0) / len(fii_scores) * 100)
        if fii_scores
        else 0
    )
    fii_regime = (
        "NET_SELLER"
        if fii_neg_pct >= 70
        else "NET_BUYER"
        if fii_neg_pct <= 30
        else "MIXED"
    )

    return {
        "contract_version": "sector-rotation-1.1",
        "institutional_context_scope": "MARKET_LEVEL_CONTEXT_ONLY",
        "sectors": _clean_records(records),
        "count": len(records),
        "fpi_date": next(iter(fpi.values()))["fpi_date"] if fpi else None,
        "fii_regime": fii_regime,
        "fii_neg_pct": fii_neg_pct,
        "data_status": data_loader.freshness_for(
            ("sector_rotation",), ("fpi_signals",)
        ),
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
        records.append(
            {
                "sector": str(row.get("sector_normalized", "")),
                "fpi_signal": str(row.get("fpi_signal", "NEUTRAL")),
                "fpi_score": _safe_float(row.get("signal_score")),
                "auc_equity_crore": _safe_float(row.get("auc_equity_crore")),
                "auc_pct_of_total": _safe_float(row.get("auc_pct_of_total")),
                "auc_z": _safe_float(row.get("auc_z52")),
                "net_z": _safe_float(row.get("net_z52")),
                "qoq_auc_delta_pct": _safe_float(row.get("qoq_auc_delta_pct")),
                "source": str(row.get("source", "")),
            }
        )

    records.sort(key=lambda r: r["fpi_score"] or 0, reverse=True)
    return {
        "sectors": _clean_records(records),
        "count": len(records),
        "date": str(latest),
        "data_status": data_loader.freshness_for(("fpi_signals",)),
    }


@router.get("/history")
def get_sector_history(sector: str | None = None, limit: int = 252):
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
        "data_status": data_loader.freshness_for(("sector_flows",)),
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
        raise HTTPException(
            status_code=404, detail=f"Sector '{sector}' not found in FPI data"
        )

    matched = matched.sort_values("date").tail(limit)
    records = []
    for _, row in matched.iterrows():
        records.append(
            {
                "date": str(row.get("date", "")),
                "auc_equity_crore": _safe_float(row.get("auc_equity_crore")),
                "net_inv_equity_crore": _safe_float(row.get("net_inv_equity_crore")),
                "auc_pct_of_total": _safe_float(row.get("auc_pct_of_total")),
                "auc_z": _safe_float(row.get("auc_z52")),
                "net_z": _safe_float(row.get("net_z52")),
                "fpi_signal": str(row.get("fpi_signal", "NEUTRAL")),
                "signal_score": _safe_float(row.get("signal_score")),
            }
        )
    return {
        "sector": sector.upper(),
        "rows": _clean_records(records),
        "count": len(records),
        "data_status": data_loader.freshness_for(("fpi_signals",)),
    }


@router.get("/{sector}")
def get_sector_detail(sector: str):
    df = data_loader.get("sector_rotation")
    if df is None or df.empty:
        raise HTTPException(
            status_code=503, detail="sector_rotation_intelligence not loaded"
        )

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
        top_stocks = sector_stocks[["symbol", "bull_run_score", "label"]].to_dict(
            orient="records"
        )

    return {
        "sector": str(row.get("sector", "")),
        "rotation_signal": str(row.get("rotation_signal", "")),
        "combined_score": _nullable_float(row.get("combined_score")),
        "FII_flow_score": _nullable_float(row.get("FII_flow_score")),
        "DII_flow_score": _nullable_float(row.get("DII_flow_score")),
        "Smart_Money_Score": _nullable_float(row.get("Smart_Money_Score")),
        "fpi_score": _nullable_float(row.get("fpi_score")),
        "price_momentum_score": _nullable_float(row.get("price_momentum_score")),
        "last_date": str(row.get("last_date", "")),
        # FPI ownership block
        "fpi_signal": fpi.get("fpi_signal", ""),
        "fpi_date": fpi.get("fpi_date", ""),
        "auc_equity_crore": fpi.get("auc_equity_crore"),
        "auc_pct_of_total": fpi.get("auc_pct_of_total"),
        "auc_z": fpi.get("auc_z"),
        "net_z": fpi.get("net_z"),
        "qoq_auc_delta_pct": fpi.get("qoq_auc_delta_pct"),
        "top_stocks": top_stocks,
        **_sector_contract_fields(row),
        "data_status": data_loader.freshness_for(
            ("sector_rotation",), ("bull_run", "fpi_signals")
        ),
    }
