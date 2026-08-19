"""General Muhurta recommendation API for the activated RX1 contract scope."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from engines.ai.knowledge.muhurta_recommendation_engine_rx1 import MuhurtaEngineError, recommend


router = APIRouter(prefix="/api/muhurta", tags=["muhurta"])


class MuhurtaRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    activity_id: str
    candidate_start: str
    location: dict[str, Any]
    activity_subscope: str | None = None
    sun_sidereal_longitude: float | None = Field(default=None, ge=0, lt=360)
    moon_sidereal_longitude: float | None = Field(default=None, ge=0, lt=360)
    p032_facts: dict[str, Any] | None = None
    transition_boundaries: list[Any] | None = None


@router.post("/recommend")
def recommend_muhurta(request: MuhurtaRecommendationRequest):
    try:
        return recommend(request.model_dump(exclude_none=True))
    except MuhurtaEngineError as exc:
        raise HTTPException(status_code=422, detail={"error_type": "ENGINE_ERROR", "message": str(exc)}) from exc
