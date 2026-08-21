"""Bounded, read-only Intraday Market-data foundation routes."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query

from backend.services.intraday_foundation import (
    CONTRACT_VERSION,
    DhanIntradayProvider,
    IntradaySourceError,
    build_status,
)

router = APIRouter(prefix="/api/intraday", tags=["intraday-market-data"])
_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9&.\-]{0,31}$")


@router.get("/status")
def get_intraday_status():
    return build_status()


@router.get("/candles")
def get_intraday_candles(
    symbol: str = Query(..., min_length=1, max_length=32),
    interval: int = Query(5, ge=1, le=60),
    from_date: str | None = Query(None, alias="from", max_length=32),
    to_date: str | None = Query(None, alias="to", max_length=32),
    limit: int = Query(500, ge=1, le=5000),
):
    normalized = symbol.strip().upper()
    if not _SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Invalid canonical symbol")
    # The store is deliberately queried only with an exact provider ID.  A
    # symbol is not a provider identity and cannot be fuzzy-resolved here.
    raise HTTPException(
        status_code=503,
        detail={
            "code": "IDENTITY_REVIEW_REQUIRED",
            "contract_version": CONTRACT_VERSION,
            "message": "An exact provider security-id mapping is required before candle reads.",
        },
    )


@router.get("/quote/{symbol}")
def get_intraday_quote(symbol: str):
    normalized = symbol.strip().upper()
    if not _SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Invalid canonical symbol")
    provider = DhanIntradayProvider()
    try:
        provider._require_client()
    except IntradaySourceError as exc:
        raise HTTPException(status_code=503, detail={"code": str(exc), "contract_version": CONTRACT_VERSION}) from exc
    raise HTTPException(status_code=503, detail={"code": "IDENTITY_REVIEW_REQUIRED", "contract_version": CONTRACT_VERSION})


@router.get("/options/{underlying}")
def get_intraday_options(underlying: str, expiry: str = Query(..., max_length=16)):
    normalized = underlying.strip().upper()
    if not _SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Invalid canonical underlying")
    provider = DhanIntradayProvider()
    try:
        provider._require_client()
    except IntradaySourceError as exc:
        raise HTTPException(status_code=503, detail={"code": str(exc), "contract_version": CONTRACT_VERSION}) from exc
    raise HTTPException(status_code=503, detail={"code": "IDENTITY_REVIEW_REQUIRED", "contract_version": CONTRACT_VERSION})
