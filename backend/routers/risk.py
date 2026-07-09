"""
Risk Router -- Phase R1
GET  /api/risk/portfolio  -- latest VaR/ES snapshot + per-position components
POST /api/risk/refresh    -- recompute risk from current positions (synchronous)
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
from fastapi import APIRouter, HTTPException

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/risk", tags=["risk"])

RISK_CSV       = cfg.INTELLIGENCE_DIR / "portfolio_risk.csv"
COMPONENTS_CSV = cfg.INTELLIGENCE_DIR / "portfolio_risk_components.csv"


def _nan_to_none(d: dict) -> dict:
    return {k: (None if pd.isna(v) else v) for k, v in d.items()}


def _read_latest() -> dict:
    if not RISK_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail="No risk snapshot yet. Run POST /api/risk/refresh or wait for the daily pipeline.",
        )
    hist = pd.read_csv(RISK_CSV)
    if hist.empty:
        raise HTTPException(status_code=404, detail="Risk history is empty")

    latest = _nan_to_none(hist.sort_values("run_date").iloc[-1].to_dict())

    components: list[dict] = []
    if COMPONENTS_CSV.exists():
        comp = pd.read_csv(COMPONENTS_CSV)
        components = [_nan_to_none(r) for r in comp.to_dict(orient="records")]

    # Trailing VaR history for a small trend chart (last 90 runs)
    trend_cols = ["run_date", "portfolio_value", "var_hist_95_1d", "es_hist_975_1d"]
    trend = hist.sort_values("run_date").tail(90)[trend_cols]
    trend_records = [_nan_to_none(r) for r in trend.to_dict(orient="records")]

    return {"snapshot": latest, "components": components, "history": trend_records}


@router.get("/portfolio")
def get_portfolio_risk():
    """Latest portfolio risk snapshot, per-position components, and VaR trend."""
    return _read_latest()


@router.post("/refresh")
def refresh_portfolio_risk():
    """Recompute risk from current positions. Fast (seconds) — runs in-process."""
    from engines.risk.portfolio_risk_engine import PortfolioRiskEngine

    try:
        engine = PortfolioRiskEngine()
        ok = engine.run()
    except Exception as e:
        logger.error("[RiskRouter] Refresh failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Risk computation failed: {e}")

    if not ok:
        raise HTTPException(
            status_code=422,
            detail="Insufficient data: need >= 2 positions with >= 60 aligned trading days",
        )
    if not RISK_CSV.exists():
        # Engine ran fine but had nothing to compute (empty portfolio is a valid state)
        raise HTTPException(
            status_code=422,
            detail="Portfolio is empty or has < 2 positions -- add transactions first",
        )
    return _read_latest()
