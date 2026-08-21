"""Public descriptive F&O routes backed by the governed F&O contract."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query

from backend.services.governed_fno_intelligence import build_governed_fno_intelligence

router = APIRouter(prefix="/api/fno", tags=["fno"])
_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9&.\-]{0,31}$")


def _validate_symbol(value: str) -> str:
    normalized = value.strip().upper()
    if not _SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid F&O symbol")
    return normalized


@router.get("/summary")
def get_fno_summary(symbol: str | None = Query(None, max_length=32)):
    return build_governed_fno_intelligence(symbol=_validate_symbol(symbol) if symbol else None)


@router.get("/stocks/{symbol}")
def get_stock_fno(symbol: str):
    return build_governed_fno_intelligence(symbol=_validate_symbol(symbol))


@router.get("/indices/{index}")
def get_index_fno(index: str):
    normalized = _validate_symbol(index)
    result = build_governed_fno_intelligence(symbol=normalized)
    result["futures"] = [item for item in result.get("futures", []) if item.get("underlying_type") == "INDEX"]
    result["query"] = {"underlying_type": "INDEX", "symbol": normalized}
    return result
