"""Gochar / Transit router for P019.

Read-only endpoints that expose transit comparison facts on top of the existing
Kundli runtime. The router intentionally stays separate from the legacy kundli
and AstroFinance endpoints so transit/gochar scope remains explicit.
"""

from __future__ import annotations

import threading
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engines.common import config as cfg
from engines.common.astrology_safety import present_kundli_chart
from engines.intelligence.jyotisha_runtime import get_jyotisha_runtime_service
from engines.transit_gochar import TransitGocharEngine, TransitReferenceType

router = APIRouter(prefix="/api/gochar", tags=["gochar"])

_engine: TransitGocharEngine | None = None
_engine_lock = threading.Lock()


def _get_engine() -> TransitGocharEngine:
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = TransitGocharEngine()
    return _engine


def _load_equity_master() -> pd.DataFrame:
    path = cfg.NSE_DIR / "equity_master" / "equity_master.csv"
    if not path.exists():
        raise HTTPException(status_code=503, detail="equity_master.csv not found")
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    return df[df["series"] == "EQ"].set_index("symbol")


class TransitHumanRequest(BaseModel):
    name: str
    date_str: str
    time_str: str
    lat: float
    lon: float
    tz_offset: float
    transit_time: Optional[str] = None
    timezone_name: Optional[str] = None
    reference_bases: list[str] = Field(default_factory=lambda: ["LAGNA", "MOON"])


def _parse_reference_bases(values: list[str]) -> list[TransitReferenceType]:
    resolved: list[TransitReferenceType] = []
    for value in values:
        try:
            resolved.append(TransitReferenceType(value.upper()))
        except Exception:
            continue
    return resolved or [TransitReferenceType.LAGNA, TransitReferenceType.MOON]


def _parse_transit_time(value: Optional[str]):
    if not value:
        return None
    return pd.Timestamp(value).to_pydatetime()


@router.get("/stock/{symbol}")
async def stock_gochar(
    symbol: str,
    exchange: str = "NSE",
    transit_time: Optional[str] = None,
    timezone_name: Optional[str] = None,
):
    symbol = symbol.upper()
    em = _load_equity_master()
    if symbol not in em.index:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    listing_date = str(em.loc[symbol, "listing_date"])[:10]
    if listing_date in ("nan", "NaT", "None", ""):
        raise HTTPException(status_code=422, detail=f"No listing date for {symbol}")

    natal = get_jyotisha_runtime_service().compute_stock_chart(symbol, listing_date, exchange).legacy_payload
    if natal is None:
        raise HTTPException(status_code=500, detail="Kundli computation failed")

    snapshot = _get_engine().build_snapshot(
        natal_chart=natal,
        transit_time=_parse_transit_time(transit_time),
        timezone_name=timezone_name,
    )
    return {
        "symbol": symbol,
        "exchange": exchange,
        "kundli": present_kundli_chart(natal),
        "gochar": snapshot.model_dump(mode="json"),
    }


@router.post("/human")
async def human_gochar(req: TransitHumanRequest):
    natal = get_jyotisha_runtime_service().compute_rest_human_chart(
        name=req.name,
        date_str=req.date_str,
        time_str=req.time_str,
        lat=req.lat,
        lon=req.lon,
        tz_offset=req.tz_offset,
    ).legacy_payload
    if natal is None:
        raise HTTPException(status_code=500, detail="Kundli computation failed")

    snapshot = _get_engine().build_snapshot(
        natal_chart=natal,
        transit_time=_parse_transit_time(req.transit_time),
        timezone_name=req.timezone_name,
        reference_bases=_parse_reference_bases(req.reference_bases),
    )
    return {
        "kundli": present_kundli_chart(natal),
        "gochar": snapshot.model_dump(mode="json"),
    }


@router.get("/country/{name}")
async def country_gochar(
    name: str,
    transit_time: Optional[str] = None,
    timezone_name: Optional[str] = None,
):
    natal = get_jyotisha_runtime_service().compute_country_chart(name).legacy_payload
    if natal is None or "error" in natal:
        raise HTTPException(
            status_code=404,
            detail=natal.get("error", "Country not found") if natal else "Computation failed",
        )

    snapshot = _get_engine().build_snapshot(
        natal_chart=natal,
        transit_time=_parse_transit_time(transit_time),
        timezone_name=timezone_name,
    )
    return {
        "country": name,
        "kundli": present_kundli_chart(natal),
        "gochar": snapshot.model_dump(mode="json"),
    }
