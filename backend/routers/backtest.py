"""
Backtest Router -- Phase 21

POST /api/backtest/label-screen        Label screen strategy
POST /api/backtest/momentum-screen     Momentum scan strategy
POST /api/backtest/portfolio-trades    Portfolio trade replay
GET  /api/backtest/results             Last saved results + summary
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engines.backtest.backtest_engine import (
    run_label_screen,
    run_momentum_screen,
    run_portfolio_trades,
    load_results,
)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


class LabelScreenRequest(BaseModel):
    label:        str = "EMERGING"
    lookback_days: int = Field(default=180, ge=30, le=730)


class MomentumScreenRequest(BaseModel):
    min_ret_30d:  float = Field(default=15.0)
    min_ret_365d: float = Field(default=30.0)
    hold_days:    int   = Field(default=60, ge=10, le=365)
    start_date:   Optional[str] = None
    end_date:     Optional[str] = None
    max_symbols:  int   = Field(default=1000, ge=50, le=2500)


@router.post("/label-screen")
def backtest_label_screen(req: LabelScreenRequest):
    result = run_label_screen(req.label, req.lookback_days)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    trades = result.get("trades", [])
    return {
        "strategy":    result["strategy"],
        "metrics":     result["metrics"],
        "trades":      trades[:200],
        "total_trades": len(trades),
    }


@router.post("/momentum-screen")
def backtest_momentum_screen(req: MomentumScreenRequest):
    result = run_momentum_screen(
        min_ret_30d  = req.min_ret_30d,
        min_ret_365d = req.min_ret_365d,
        hold_days    = req.hold_days,
        start_date   = req.start_date or "",
        end_date     = req.end_date or "",
        max_symbols  = req.max_symbols,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    trades = result.get("trades", [])
    return {
        "strategy":    result["strategy"],
        "metrics":     result["metrics"],
        "trades":      trades[:200],
        "total_trades": len(trades),
    }


@router.post("/portfolio-trades")
def backtest_portfolio_trades():
    result = run_portfolio_trades()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/results")
def get_last_results():
    trades, summary = load_results()
    return {
        "summary":     summary,
        "trades":      trades[:200],
        "total_trades": len(trades),
    }
