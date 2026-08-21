"""
Portfolio Router -- Phase 20
REST API for portfolio tracking + intelligence overlay.

GET    /api/portfolio                   -- positions + intelligence + analytics
POST   /api/portfolio/buy               -- record a buy transaction
POST   /api/portfolio/sell              -- record a sell transaction
GET    /api/portfolio/transactions      -- full transaction history
DELETE /api/portfolio/positions/{symbol} -- remove all lots for a symbol
GET    /api/portfolio/import/template   -- Phase PF-1: downloadable CSV import template
POST   /api/portfolio/import            -- Phase PF-1: bulk-import transactions from CSV
"""

import io
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.services.governed_portfolio_intelligence import (
    build_governed_portfolio_intelligence,
)
from engines.portfolio.portfolio_engine import (
    add_transaction,
    compute_analytics,
    delete_symbol,
    import_transactions,
    load_intelligence,
    load_transactions,
)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

IMPORT_TEMPLATE_CSV = (
    "date,symbol,action,qty,price,notes\n"
    "2026-01-15,RELIANCE,BUY,10,1350.50,Initial position\n"
    "2026-03-02,TCS,BUY,5,3800,\n"
    "2026-04-10,RELIANCE,SELL,4,1420.75,Partial profit booking\n"
)


# ── Request / response models ─────────────────────────────────────────────────

class TransactionRequest(BaseModel):
    symbol: str
    qty:    float = Field(gt=0)
    price:  float = Field(gt=0)
    date:   str | None = None
    notes:  str | None = ""


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


@router.get("/governed")
def get_governed_portfolio():
    """Read-only Portfolio Intelligence 1.0 provider contract.

    The existing mutation endpoints remain local Phase-20 functionality.  This
    endpoint composes their factual positions with the governed Market stack;
    it never places orders, changes broker state, or emits BUY/SELL advice.
    """
    return build_governed_portfolio_intelligence()


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


@router.get("/import/template")
def download_import_template():
    """Downloadable CSV template with the exact columns import_transactions()
    expects, pre-filled with example rows so the format is unambiguous."""
    return Response(
        content=IMPORT_TEMPLATE_CSV,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=portfolio_import_template.csv"},
    )


@router.post("/import")
async def import_csv(file: Annotated[UploadFile, File(...)]):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    try:
        df = pd.read_csv(io.BytesIO(raw), dtype=str)
    except (OSError, ValueError, pd.errors.ParserError) as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")
    if df.empty:
        raise HTTPException(status_code=400, detail="CSV has no data rows")
    try:
        result = import_transactions(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


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
