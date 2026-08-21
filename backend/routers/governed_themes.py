"""Formal governed Theme Intelligence HTTP surface.

Legacy ``/api/themes`` remains unchanged.  VEDA consumes this read-only
provider-owned contract under ``/api/themes/governed``.
"""

from fastapi import APIRouter, HTTPException, Query

from backend.services import governed_theme_intelligence as service

router = APIRouter(prefix="/api/themes/governed", tags=["governed-theme-intelligence"])


@router.get("")
def get_theme_registry():
    return service.registry()


@router.get("/summary")
def get_theme_summary():
    try:
        return service.summary()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"governed theme registry unavailable: {exc}") from exc


@router.get("/stocks/{symbol}")
def get_stock_themes(symbol: str):
    memberships = service.memberships_for(symbol=symbol.strip().upper())
    if not memberships:
        raise HTTPException(status_code=404, detail=f"No governed theme membership for '{symbol}'")
    return {"contract_version": service.CONTRACT_VERSION, "symbol": symbol.strip().upper(), "memberships": memberships, "data_status": {"state": "AVAILABLE", "limitations": ["Current membership only; historical membership snapshots unavailable."]}}


@router.get("/{theme_id}")
def get_theme(theme_id: str, include_members: bool = False, member_limit: int = Query(50, ge=1, le=500)):
    try:
        return service.intelligence(theme_id, include_members=include_members, member_limit=member_limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found") from exc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"governed theme provider unavailable: {exc}") from exc


@router.get("/{theme_id}/intelligence")
def get_theme_intelligence(theme_id: str, member_limit: int = Query(50, ge=1, le=500)):
    return get_theme(theme_id, include_members=True, member_limit=member_limit)
