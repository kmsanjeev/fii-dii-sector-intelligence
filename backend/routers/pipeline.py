"""
Pipeline Router -- Phase 19
REST endpoints for daily intelligence refresh control.

GET  /api/pipeline/status   -- current run state + per-stage breakdown
POST /api/pipeline/run      -- trigger a manual run (409 if already running)
POST /api/pipeline/stop     -- send kill signal (aborts after current stage)
GET  /api/pipeline/log      -- last N rows from refresh_log.csv
GET  /api/pipeline/next     -- next scheduled run time (IST)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engines.orchestration.daily_refresh import (
    start_pipeline,
    stop_pipeline,
    read_status,
    read_log,
    is_running,
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


# ── Response models ───────────────────────────────────────────────────────────

class PipelineStatusResponse(BaseModel):
    state: str                      # IDLE | RUNNING | DONE | FAILED | STOPPED
    run_id: str | None
    started_at: str | None
    last_run_at: str | None
    current_stage: str | None
    current_label: str | None
    next_run_ist: str | None
    stages: dict


class ActionResponse(BaseModel):
    ok: bool
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status", response_model=PipelineStatusResponse)
def get_status() -> PipelineStatusResponse:
    from engines.orchestration.refresh_scheduler import next_run_ist
    status = read_status()
    return PipelineStatusResponse(
        state         = status.get("state", "IDLE"),
        run_id        = status.get("run_id"),
        started_at    = status.get("started_at"),
        last_run_at   = status.get("last_run_at"),
        current_stage = status.get("current_stage"),
        current_label = status.get("current_label"),
        next_run_ist  = next_run_ist(),
        stages        = status.get("stages", {}),
    )


@router.post("/run", response_model=ActionResponse)
def run_pipeline() -> ActionResponse:
    if is_running():
        raise HTTPException(status_code=409, detail="Pipeline already running")
    ok, msg = start_pipeline()
    if not ok:
        raise HTTPException(status_code=409, detail=msg)
    return ActionResponse(ok=True, message=msg)


@router.post("/stop", response_model=ActionResponse)
def stop_pipeline_endpoint() -> ActionResponse:
    ok, msg = stop_pipeline()
    return ActionResponse(ok=ok, message=msg)


@router.get("/log")
def get_log(n: int = 100) -> list[dict]:
    return read_log(n)


@router.get("/next")
def get_next_run() -> dict:
    from engines.orchestration.refresh_scheduler import next_run_ist
    return {"next_run_ist": next_run_ist()}
