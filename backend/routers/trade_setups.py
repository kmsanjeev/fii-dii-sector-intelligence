"""Read-only governed Swing and Positional setup routes."""

from fastapi import APIRouter, HTTPException, Query

from backend.services.governed_trade_setup_intelligence import (
    CONTRACT_VERSION,
    HORIZONS,
    build_trade_setup_intelligence,
    screen_trade_setups,
)

router = APIRouter(prefix="/api/trade-setups", tags=["trade-setup-intelligence"])


def _horizon(value: str) -> str:
    normalized = str(value or "SWING").strip().upper()
    if normalized not in HORIZONS:
        raise HTTPException(
            status_code=422, detail="horizon must be SWING or POSITIONAL"
        )
    return normalized


@router.get("/screen")
def get_setup_screen(
    horizon: str = Query("SWING", max_length=16),
    limit: int = Query(20, ge=1, le=50),
    fno_only: bool = Query(False),
):
    try:
        return screen_trade_setups(
            horizon=_horizon(horizon), limit=limit, fno_only=fno_only
        )
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=503, detail=f"trade setup screen unavailable: {exc}"
        ) from exc


@router.get("/{symbol}")
def get_trade_setup(
    symbol: str,
    horizon: str = Query("SWING", max_length=16),
):
    try:
        result = build_trade_setup_intelligence(symbol, horizon=_horizon(horizon))
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"Unknown or unsupported symbol '{symbol.upper()}'"
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OSError, ImportError) as exc:
        raise HTTPException(
            status_code=503, detail=f"trade setup provider unavailable: {exc}"
        ) from exc
    result["route_contract_version"] = CONTRACT_VERSION
    return result
