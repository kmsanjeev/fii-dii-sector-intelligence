"""General Muhurta recommendation API for the activated RX1 contract scope."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from engines.ai.knowledge.muhurta_recommendation_engine_rx1 import MuhurtaEngineError, recommend
from engines.ai.knowledge.muhurta_window_search import MuhurtaWindowSearchError, search


router = APIRouter(prefix="/api/muhurta", tags=["muhurta"])


class MuhurtaRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    activity_id: str
    candidate_start: str
    location: dict[str, Any]
    activity_subscope: str | None = None
    ceremony_subtype: str | None = None
    sun_sidereal_longitude: float | None = Field(default=None, ge=0, lt=360)
    moon_sidereal_longitude: float | None = Field(default=None, ge=0, lt=360)
    p032_facts: dict[str, Any] | None = None
    transition_boundaries: list[Any] | None = None


class MuhurtaWindowSearchRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    activity_id: str
    location: dict[str, Any]
    start_datetime: str
    end_datetime: str
    daily_earliest_time: str | None = None
    daily_latest_time: str | None = None
    max_results: int = Field(default=5, ge=1, le=20)
    activity_subscope: str | None = None
    ceremony_subtype: str | None = None
    transition_boundaries: list[Any] | None = None
    p032_fact_segments: list[dict[str, Any]] | None = None
    p032_facts: dict[str, Any] | None = None


@router.post("/recommend")
def recommend_muhurta(request: MuhurtaRecommendationRequest):
    try:
        return recommend(request.model_dump(exclude_none=True))
    except MuhurtaEngineError as exc:
        raise HTTPException(status_code=422, detail={"error_type": "ENGINE_ERROR", "message": str(exc)}) from exc


@router.post("/search")
def search_muhurta_windows(request: MuhurtaWindowSearchRequest):
    try:
        return search(request.model_dump(exclude_none=True))
    except (MuhurtaWindowSearchError, MuhurtaEngineError) as exc:
        raise HTTPException(status_code=422, detail={"error_type": "WINDOW_SEARCH_ERROR", "message": str(exc)}) from exc
