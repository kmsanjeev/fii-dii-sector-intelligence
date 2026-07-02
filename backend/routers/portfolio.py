"""
Portfolio Router -- Phase 20
REST API for portfolio tracking + intelligence overlay.

GET    /api/portfolio                   -- positions + intelligence + analytics
POST   /api/portfolio/buy               -- record a buy transaction
POST   /api/portfolio/sell              -- record a sell transaction
GET    /api/portfolio/transactions      -- full transaction history
DELETE /api/portfolio/positions/{symbol} -- remove all lots for a symbol
"""

from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engines.portfolio.portfolio_engine import (
    add_transaction,
    compute_analytics,
    delete_symbol,
    load_intelligence,
    load_transactions,
)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# ── Request / response models ─────────────────────────────────────────────────

class TransactionRequest(BaseModel):
    symbol: str
    qty:    float = Field(gt=0)
    price:  float = Field(gt=0)
    date:   Optional[str] = None
    notes:  Optional[str] = ""


class ActionResponse(BaseModel):
    ok:      bool
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def get_portfolio():
    intel     = load_intelligence()
    analytics = compute_analytics(intel)
    positions = (
        intel.where(pd.notnull(intel), None).to_dict(orient="records")
        if not intel.empty else []
    )
    return {"analytics": analytics, "positions": positions}


@router.post("/buy", response_model=ActionResponse)
def record_buy(req: TransactionRequest):
    try:
        add_transaction(req.symbol, "BUY", req.qty, req.price,
                        req.date or "", req.notes or "")
        return ActionResponse(
            ok=True,
            message=f"BUY {req.symbol.upper()} x{req.qty} @ {req.price} recorded",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sell", response_model=ActionResponse)
def record_sell(req: TransactionRequest):
    try:
        add_transaction(req.symbol, "SELL", req.qty, req.price,
                        req.date or "", req.notes or "")
        return ActionResponse(
            ok=True,
            message=f"SELL {req.symbol.upper()} x{req.qty} @ {req.price} recorded",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions")
def get_transactions():
    txns = load_transactions()
    if txns.empty:
        return {"transactions": [], "count": 0}
    out = txns.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return {
        "transactions": out.where(pd.notnull(out), None).to_dict(orient="records"),
        "count":        len(out),
    }


@router.delete("/positions/{symbol}", response_model=ActionResponse)
def remove_position(symbol: str):
    removed = delete_symbol(symbol)
    if removed == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No transactions found for {symbol.upper()}",
        )
    return ActionResponse(
        ok=True,
        message=f"Removed {removed} transaction(s) for {symbol.upper()}",
    )
