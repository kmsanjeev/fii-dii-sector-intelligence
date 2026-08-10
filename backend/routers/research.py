"""
Research Router -- Phase 23

POST   /api/research/screen               screener with filter body
GET    /api/research/universe/stats       label/sector counts for filter dropdowns
GET    /api/research/compare              multi-symbol comparison (?symbols=A,B,C)
GET    /api/research/notes                list all noted symbols
GET    /api/research/notes/{symbol}       get note
PUT    /api/research/notes/{symbol}       upsert note
DELETE /api/research/notes/{symbol}       delete note
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from engines.research.screener_engine import screen, compare, universe_stats
from engines.research import notes_engine
from engines.ai.research.platform.contracts import AdminAction
from engines.ai.research.platform.service import get_research_platform_service
from backend.auth.middleware import require_admin

router = APIRouter(prefix="/api/research", tags=["research"])


# ── Request models ─────────────────────────────────────────────────────────────

class ScreenRequest(BaseModel):
    labels:           Optional[list[str]] = None
    sectors:          Optional[list[str]] = None
    indices:          Optional[list[str]] = None
    conviction_signal: Optional[str]      = None   # BUYING | SELLING | STABLE
    fii_delta_dir:    Optional[str]       = None   # positive | negative
    min_score:        Optional[float]     = None
    max_score:        Optional[float]     = None
    min_ml:           Optional[float]     = None
    max_ml:           Optional[float]     = None
    min_ret_30d:      Optional[float]     = None
    max_ret_30d:      Optional[float]     = None
    min_ret_90d:      Optional[float]     = None
    max_ret_90d:      Optional[float]     = None
    min_ret_365d:     Optional[float]     = None
    max_ret_365d:     Optional[float]     = None
    min_confidence:   Optional[float]     = None
    max_confidence:   Optional[float]     = None
    min_promoter_pct: Optional[float]     = None
    sort_by:          str = "bull_run_score"
    sort_dir:         str = "desc"
    limit:            int = 200


class NoteRequest(BaseModel):
    content: str
    tags:    list[str] = []
    rating:  int = 0


class MissionCreateRequest(BaseModel):
    domain_id: str
    title: str
    objective: str
    research_type: str
    priority: str = "P2"
    status: str = "QUEUED"
    created_by: str = "admin"
    query_strategy: dict[str, Any] = Field(default_factory=dict)
    required_source_classes: list[str] = Field(default_factory=list)
    minimum_independent_sources: int = 1
    known_claim_ids: list[str] = Field(default_factory=list)
    known_conflict_ids: list[str] = Field(default_factory=list)
    known_gap_ids: list[str] = Field(default_factory=list)
    safety_class: str = "LOW"
    completion_policy: dict[str, Any] = Field(default_factory=dict)
    research_budget: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    follow_up_depth: int = 0
    parent_candidate_id: str | None = None
    parent_mission_id: str | None = None


class ScheduleCreateRequest(BaseModel):
    domain_id: str
    mission_id: str
    cadence_type: str = "MANUAL_ONLY"
    timezone: str = "Asia/Calcutta"
    enabled: bool = True
    next_run_at: str | None = None
    last_run_at: str | None = None
    misfire_policy: str = "RUN_ONCE"
    overlap_policy: str = "SKIP"
    priority: str = "P2"


class ScheduleUpdateRequest(BaseModel):
    enabled: bool | None = None
    next_run_at: str | None = None
    last_run_at: str | None = None
    misfire_policy: str | None = None
    overlap_policy: str | None = None
    priority: str | None = None


class CandidateDecisionRequest(BaseModel):
    action: str
    reason: str
    conditions: list[str] = Field(default_factory=list)


# ── Screener ───────────────────────────────────────────────────────────────────

@router.post("/screen")
def run_screen(req: ScreenRequest):
    try:
        records, total = screen(req.model_dump(exclude_none=False))
        return {"results": records, "total": total, "returned": len(records)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/universe/stats")
def get_universe_stats():
    try:
        return universe_stats()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ── Conviction Screener (Phase SA-1) ──────────────────────────────────────────

@router.get("/conviction")
def get_conviction_screener(
    tier:  Optional[str] = Query(None, description="HIGH | MEDIUM | WATCH"),
    limit: int = Query(50, ge=1, le=500),
):
    """Efficacy-weighted, liquidity-gated investment candidates with evidence."""
    import pandas as pd
    from engines.common import config as cfg

    path = cfg.INTELLIGENCE_DIR / "conviction_screener.csv"
    if not path.exists():
        raise HTTPException(status_code=404,
                            detail="No conviction screen yet -- run POST /api/research/conviction/refresh")
    df = pd.read_csv(path)
    if tier:
        df = df[df["tier"] == tier.upper()]
    df = df.head(limit)
    recs = [{k: (None if pd.isna(v) else v) for k, v in r.items()}
            for r in df.to_dict(orient="records")]
    return {"candidates": recs, "total": len(recs),
            "as_of": recs[0]["as_of_date"] if recs else None,
            "regime": recs[0]["regime"] if recs else None}


@router.post("/conviction/refresh")
def refresh_conviction_screener():
    """Recompute the conviction screen from the latest intelligence files."""
    from engines.research.conviction_screener_engine import ConvictionScreenerEngine
    try:
        ok = ConvictionScreenerEngine().run()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Screener failed: {exc}")
    if not ok:
        raise HTTPException(status_code=422, detail="Universe too small after gates -- check intelligence files")
    return get_conviction_screener(tier=None, limit=50)


@router.get("/efficacy")
def get_signal_efficacy():
    """The signal accuracy report card: IC / decile spread / hit rate per factor."""
    import pandas as pd
    from engines.common import config as cfg

    path = cfg.INTELLIGENCE_DIR / "signal_efficacy.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No efficacy report yet")
    df = pd.read_csv(path)
    recs = [{k: (None if pd.isna(v) else v) for k, v in r.items()}
            for r in df.to_dict(orient="records")]
    return {"factors": recs}


# ── Comparator ─────────────────────────────────────────────────────────────────

@router.get("/compare")
def compare_symbols(symbols: str = Query(..., description="Comma-separated symbols e.g. RELIANCE,TCS")):
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise HTTPException(status_code=400, detail="Provide at least one symbol")
    if len(sym_list) > 8:
        raise HTTPException(status_code=400, detail="Maximum 8 symbols for comparison")
    try:
        data = compare(sym_list)
        not_found = [s for s, v in data.items() if v is None]
        return {"data": data, "symbols": sym_list, "not_found": not_found}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ── Notes ──────────────────────────────────────────────────────────────────────

@router.get("/notes")
def list_notes():
    return {"notes": notes_engine.list_index()}


@router.get("/notes/{symbol}")
def get_note(symbol: str):
    note = notes_engine.get(symbol.upper())
    if note is None:
        raise HTTPException(status_code=404, detail=f"No note for {symbol.upper()}")
    return note


@router.put("/notes/{symbol}")
def upsert_note(symbol: str, req: NoteRequest):
    note = notes_engine.save(symbol.upper(), req.content, req.tags, req.rating)
    return note


@router.delete("/notes/{symbol}")
def delete_note(symbol: str):
    deleted = notes_engine.delete(symbol.upper())
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No note for {symbol.upper()}")
    return {"status": "deleted", "symbol": symbol.upper()}


# ── P006 Research Platform Admin Surface ───────────────────────────────────────

@router.get("/dashboard", tags=["research-admin"])
def get_research_dashboard(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return service.dashboard().model_dump(mode="json")


@router.get("/platform/health", tags=["research-admin"])
def get_research_platform_health(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return service.health()


@router.get("/domains", tags=["research-admin"])
def list_research_domains(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return {"domains": [item.model_dump(mode="json") for item in service.list_domains()]}


@router.get("/missions", tags=["research-admin"])
def list_research_missions(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return {"missions": [item.model_dump(mode="json") for item in service.list_missions()]}


@router.post("/missions", tags=["research-admin"])
def create_research_mission(req: MissionCreateRequest, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    mission = service.create_mission(req.model_dump())
    return mission.model_dump(mode="json")


@router.get("/missions/{mission_id}", tags=["research-admin"])
def get_research_mission(mission_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    mission = service.get_mission(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail=f"Unknown mission: {mission_id}")
    return mission.model_dump(mode="json")


@router.post("/missions/{mission_id}/pause", tags=["research-admin"])
def pause_research_mission(mission_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        mission = service.pause_mission(mission_id, actor_id=current_user.email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return mission.model_dump(mode="json")


@router.post("/missions/{mission_id}/resume", tags=["research-admin"])
def resume_research_mission(mission_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        mission = service.resume_mission(mission_id, actor_id=current_user.email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return mission.model_dump(mode="json")


@router.post("/missions/{mission_id}/trigger", tags=["research-admin"])
def trigger_research_mission(mission_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        run = service.trigger_manual_run(mission_id, actor_id=current_user.email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return run.model_dump(mode="json")


@router.get("/runs", tags=["research-admin"])
def list_research_runs(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return {"runs": [item.model_dump(mode="json") for item in service.list_runs()]}


@router.get("/runs/{run_id}", tags=["research-admin"])
def get_research_run(run_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run: {run_id}")
    return run.model_dump(mode="json")


@router.get("/candidates", tags=["research-admin"])
def list_research_candidates(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return {"candidates": [item.model_dump(mode="json") for item in service.list_candidates()]}


@router.get("/candidates/{candidate_id}", tags=["research-admin"])
def get_research_candidate(candidate_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        review = service.get_candidate_review(candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return review.model_dump(mode="json")


@router.post("/candidates/{candidate_id}/decision", tags=["research-admin"])
def decide_research_candidate(candidate_id: str, req: CandidateDecisionRequest, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        approval = service.decide_candidate(
            candidate_id,
            action=AdminAction(req.action),
            actor_id=current_user.email,
            reason=req.reason,
            conditions=req.conditions,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {req.action}")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return approval.model_dump(mode="json")


@router.get("/ledger", tags=["research-admin"])
def list_research_ledger(limit: int = Query(200, ge=1, le=1000), current_user=Depends(require_admin)):
    service = get_research_platform_service()
    rows = service.list_ledger_events()[-limit:]
    return {"events": [item.model_dump(mode="json") for item in rows], "returned": len(rows)}


@router.get("/schedules", tags=["research-admin"])
def list_research_schedules(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return {"schedules": [item.model_dump(mode="json") for item in service.list_schedules()]}


@router.post("/schedules", tags=["research-admin"])
def create_research_schedule(req: ScheduleCreateRequest, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    schedule = service.create_schedule(req.model_dump())
    return schedule.model_dump(mode="json")


@router.put("/schedules/{schedule_id}", tags=["research-admin"])
def update_research_schedule(schedule_id: str, req: ScheduleUpdateRequest, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        schedule = service.update_schedule(schedule_id, req.model_dump(exclude_none=True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return schedule.model_dump(mode="json")
