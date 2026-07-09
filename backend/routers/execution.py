"""
Execution Router -- Phase 24
Signal-to-order pipeline with risk management and Dhan order placement.
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.execution.risk_engine import load_config, save_config
from engines.execution.order_manager import (
    place_order as _place,
    cancel_order as _cancel,
    get_blotter,
    get_order_status as _get_status,
)
from engines.execution.signal_recommender import recommend

router = APIRouter(prefix="/api/execution", tags=["execution"])


# ── Request models ─────────────────────────────────────────────────────────────

class ConfigUpdate(BaseModel):
    paper_mode:                Optional[bool]  = None
    portfolio_value:           Optional[float] = None
    max_position_pct:          Optional[float] = None
    max_sector_pct:            Optional[float] = None
    min_cash_pct:              Optional[float] = None
    allow_duplicate_orders:    Optional[bool]  = None
    max_adv_participation_pct: Optional[float] = None   # Phase R4


class RecommendRequest(BaseModel):
    portfolio_value: Optional[float]      = None
    top_n:           int                  = 10
    min_score:       float                = 50.0
    labels:          Optional[list[str]]  = None
    action:          str                  = "BUY"


class OrderRequest(BaseModel):
    symbol:          str
    sector:          str    = ""
    action:          str    = "BUY"
    qty:             int
    price:           float  = 0.0
    order_type:      str    = "MARKET"
    exchange:        str    = "NSE"
    notes:           str    = ""
    portfolio_value: Optional[float] = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/config")
def get_config():
    return load_config()


@router.put("/config")
def update_config(req: ConfigUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    return save_config(updates)


@router.post("/recommend")
def get_recommendations(req: RecommendRequest):
    try:
        recs = recommend(
            portfolio_value = req.portfolio_value or 0.0,
            top_n           = req.top_n,
            min_score       = req.min_score,
            labels          = req.labels,
            action          = req.action,
        )
        return {"recommendations": recs, "count": len(recs)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/order")
def place_order_endpoint(req: OrderRequest):
    try:
        result = _place(
            symbol          = req.symbol,
            sector          = req.sector,
            action          = req.action,
            qty             = req.qty,
            price           = req.price,
            order_type      = req.order_type,
            exchange        = req.exchange,
            notes           = req.notes,
            portfolio_value = req.portfolio_value or 0.0,
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/order/{order_id}")
def cancel_order_endpoint(order_id: str):
    result = _cancel(order_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/orders")
def list_orders(status: Optional[str] = None, limit: int = 200):
    try:
        return {"orders": get_blotter(status_filter=status, limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/order/{order_id}")
def order_status(order_id: str):
    data = _get_status(order_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return data


@router.post("/security-master/refresh")
def refresh_security_master():
    """Download Dhan scrip master and rebuild security_id lookup. Requires Dhan credentials."""
    try:
        from engines.broker.sync_engine import load_credentials
        creds = load_credentials()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No broker credentials: {exc}")

    if creds.get("broker") != "dhan":
        raise HTTPException(status_code=400, detail="Security master refresh requires Dhan broker")

    from engines.execution.dhan_order_adapter import DhanOrderAdapter
    try:
        mapping = DhanOrderAdapter.refresh_security_master()
        return {"success": True, "symbols_loaded": len(mapping)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── TCA + order slicing (Phase R4) ────────────────────────────────────────────

@router.get("/tca")
def get_tca():
    """Latest TCA report: per-fill slippage vs arrival/VWAP/close + aggregates."""
    import pandas as pd
    from engines.common import config as cfg

    report_csv  = cfg.INTELLIGENCE_DIR / "tca_report.csv"
    summary_csv = cfg.INTELLIGENCE_DIR / "tca_summary.csv"
    if not report_csv.exists():
        raise HTTPException(
            status_code=404,
            detail="No TCA report yet. Run POST /api/execution/tca/refresh.",
        )

    def _clean(d: dict) -> dict:
        return {k: (None if pd.isna(v) else v) for k, v in d.items()}

    report = pd.read_csv(report_csv)
    summary = {}
    if summary_csv.exists():
        s = pd.read_csv(summary_csv)
        if not s.empty:
            summary = _clean(s.sort_values("run_date").iloc[-1].to_dict())
    return {
        "summary": summary,
        "fills":   [_clean(r) for r in report.to_dict(orient="records")],
    }


@router.post("/tca/refresh")
def refresh_tca():
    """Recompute slippage for every filled order in the blotter."""
    from engines.common import config as cfg
    from engines.execution.tca_engine import TCAEngine

    try:
        ok = TCAEngine().run()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TCA failed: {exc}")
    if not ok or not (cfg.INTELLIGENCE_DIR / "tca_report.csv").exists():
        raise HTTPException(status_code=422, detail="No filled orders in blotter yet")
    return get_tca()


@router.get("/slice_plan")
def get_slice_plan(
    symbol: str,
    qty: int,
):
    """TWAP slice plan for an order: ADV participation check + child slices."""
    if qty <= 0:
        raise HTTPException(status_code=400, detail="qty must be positive")
    from engines.execution.order_slicer import build_twap_plan

    plan = build_twap_plan(symbol, qty)
    if "error" in plan:
        raise HTTPException(status_code=404, detail=plan["error"])
    return plan
