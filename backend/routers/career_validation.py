"""Career profession validation router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
import pandas as pd

from engines.career.veda_p021_engine import load_validated_profiles


router = APIRouter(prefix="/api/career", tags=["career"])


def _json_safe(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        return value
    return value


@router.get("/validated")
def get_validated_profiles(
    limit: int = 20,
    offset: int = 0,
    symbol: str | None = None,
    industry: str | None = None,
    domain_id: str | None = None,
):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be non-negative")
    try:
        records, summary = load_validated_profiles(
            limit=limit,
            offset=offset,
            symbol=symbol,
            industry=industry,
            domain_id=domain_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    response_records = [
        {key: _json_safe(value) for key, value in row.items()}
        for row in records.to_dict(orient="records")
    ]
    return {
        "records": response_records,
        "total": summary["profiles_total"],
        "returned": len(response_records),
        "summary": summary,
    }
