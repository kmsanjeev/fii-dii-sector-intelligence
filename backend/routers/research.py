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
from engines.ai.research.platform.runtime import get_research_platform_runtime
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
    cadence_type: str | None = None
    timezone: str | None = None
    next_run_at: str | None = None
    last_run_at: str | None = None
    misfire_policy: str | None = None
    overlap_policy: str | None = None
    priority: str | None = None


class MissionActionRequest(BaseModel):
    priority: str | None = None
    notes: str | None = None
    mode: str | None = None


class CandidateDecisionRequest(BaseModel):
    action: str
    reason: str
    conditions: list[str] = Field(default_factory=list)
    acknowledged_high_stakes: bool = False
    conflict_id: str | None = None
    conflict_resolution: str | None = None
    conflict_note: str | None = None


class CandidatePromotionRequest(BaseModel):
    promotion_notes: str | None = None


class PromotionRollbackRequest(BaseModel):
    reason: str


class RuntimeControlRequest(BaseModel):
    reason: str | None = None
    enabled: bool | None = None


class DomainStatusRequest(BaseModel):
    status: str


class DueRunRequest(BaseModel):
    as_of: str | None = None
    actor_id: str | None = None


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
def get_research_dashboard(domain_id: str | None = Query(None), current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return service.dashboard_bundle(domain_id=domain_id)


@router.get("/platform/health", tags=["research-admin"])
def get_research_platform_health(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    runtime = get_research_platform_runtime()
    return {
        **service.health(),
        "runtime": runtime.health(),
    }


@router.get("/platform/runtime", tags=["research-admin"])
def get_research_runtime_status(current_user=Depends(require_admin)):
    runtime = get_research_platform_runtime()
    service = get_research_platform_service()
    return {
        "runtime": runtime.health(),
        "controls": service.platform_runtime_state(),
        "digests": service.list_digests(limit=10),
    }


@router.get("/platform/provider-audit", tags=["research-admin"])
def get_research_provider_audit(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return {"providers": service.provider_capability_matrix()}


@router.post("/platform/pause", tags=["research-admin"])
def pause_research_runtime(req: RuntimeControlRequest | None = None, current_user=Depends(require_admin)):
    runtime = get_research_platform_runtime()
    return runtime.pause(actor_id=current_user.email, reason=req.reason if req else None)


@router.post("/platform/resume", tags=["research-admin"])
def resume_research_runtime(req: RuntimeControlRequest | None = None, current_user=Depends(require_admin)):
    runtime = get_research_platform_runtime()
    return runtime.resume(actor_id=current_user.email, reason=req.reason if req else None)


@router.post("/platform/kill-switch", tags=["research-admin"])
def toggle_research_kill_switch(req: RuntimeControlRequest, current_user=Depends(require_admin)):
    runtime = get_research_platform_runtime()
    return runtime.set_kill_switch(bool(req.enabled), actor_id=current_user.email, reason=req.reason)


@router.post("/platform/run-due", tags=["research-admin"])
def run_due_research_schedules(req: DueRunRequest | None = None, current_user=Depends(require_admin)):
    runtime = get_research_platform_runtime()
    return runtime.run_due_tasks(
        as_of=req.as_of if req else None,
        actor_id=req.actor_id if req and req.actor_id else current_user.email,
    )


@router.post("/platform/seed-astrology-external-pilot", tags=["research-admin"])
def seed_astrology_external_pilot(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return service.seed_vedic_astrology_external_program(actor_id=current_user.email)


@router.get("/domains", tags=["research-admin"])
def list_research_domains(current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return {"domains": [item.model_dump(mode="json") for item in service.list_domains()]}


@router.post("/domains/{domain_id}/status", tags=["research-admin"])
def set_research_domain_status(domain_id: str, req: DomainStatusRequest, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        domain = service.set_domain_status(domain_id, req.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return domain.model_dump(mode="json")


@router.get("/missions", tags=["research-admin"])
def list_research_missions(
    domain_id: str | None = Query(None),
    status: str | None = Query(None),
    research_type: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    current_user=Depends(require_admin),
):
    service = get_research_platform_service()
    return service.list_mission_rows(
        domain_id=domain_id,
        status=status,
        research_type=research_type,
        search=search,
        page=page,
        per_page=per_page,
    )


@router.post("/missions", tags=["research-admin"])
def create_research_mission(req: MissionCreateRequest, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    mission = service.create_mission(req.model_dump())
    return mission.model_dump(mode="json")


@router.get("/missions/{mission_id}", tags=["research-admin"])
def get_research_mission(mission_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        return service.get_mission_detail(mission_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/missions/{mission_id}/pause", tags=["research-admin"])
def pause_research_mission(mission_id: str, req: MissionActionRequest | None = None, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        if req and (req.mode or "").upper() == "ARCHIVE":
            mission = service.archive_mission(mission_id, actor_id=current_user.email, notes=req.notes)
        else:
            mission = service.pause_mission(mission_id, actor_id=current_user.email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return mission.model_dump(mode="json")


@router.post("/missions/{mission_id}/resume", tags=["research-admin"])
def resume_research_mission(mission_id: str, req: MissionActionRequest | None = None, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        mission = service.resume_mission(
            mission_id,
            actor_id=current_user.email,
            priority=req.priority if req else None,
            notes=req.notes if req else None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
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
def list_research_runs(
    domain_id: str | None = Query(None),
    mission_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    include_sources: bool = Query(False),
    current_user=Depends(require_admin),
):
    service = get_research_platform_service()
    return service.list_run_rows(
        domain_id=domain_id,
        mission_id=mission_id,
        status=status,
        page=page,
        per_page=per_page,
        include_sources=include_sources,
    )


@router.get("/runs/{run_id}", tags=["research-admin"])
def get_research_run(run_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        return service.get_run_detail(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/candidates", tags=["research-admin"])
def list_research_candidates(
    domain_id: str | None = Query(None),
    approval_status: str | None = Query(None),
    priority: str | None = Query(None),
    search: str | None = Query(None),
    contradiction_only: bool = Query(False),
    high_stakes_only: bool = Query(False),
    promotion_state: str | None = Query(None),
    sort_by: str = Query("updated_at"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    current_user=Depends(require_admin),
):
    service = get_research_platform_service()
    return service.list_candidate_rows(
        domain_id=domain_id,
        approval_status=approval_status,
        priority=priority,
        search=search,
        contradiction_only=contradiction_only,
        high_stakes_only=high_stakes_only,
        promotion_state=promotion_state,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        per_page=per_page,
    )


@router.get("/candidates/{candidate_id}", tags=["research-admin"])
def get_research_candidate(candidate_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        review = service.get_candidate_review_bundle(candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return review


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
            acknowledged_high_stakes=req.acknowledged_high_stakes,
            conflict_id=req.conflict_id,
            conflict_resolution=req.conflict_resolution,
            conflict_note=req.conflict_note,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {req.action}")
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return approval.model_dump(mode="json")


@router.get("/candidates/{candidate_id}/promotion-preflight", tags=["research-admin"])
def preview_candidate_promotion(candidate_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        preflight = service.run_promotion_preflight(candidate_id, actor_id=current_user.email)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return preflight.model_dump(mode="json")


@router.post("/candidates/{candidate_id}/promote", tags=["research-admin"])
def promote_research_candidate(candidate_id: str, req: CandidatePromotionRequest | None = None, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        return service.promote_candidate(
            candidate_id,
            actor_id=current_user.email,
            promotion_notes=req.promotion_notes if req else None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/promotions/{promotion_id}/rollback", tags=["research-admin"])
def rollback_promoted_candidate(promotion_id: str, req: PromotionRollbackRequest, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        return service.rollback_promotion(promotion_id, actor_id=current_user.email, reason=req.reason)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/ledger", tags=["research-admin"])
def list_research_ledger(
    limit: int = Query(200, ge=1, le=1000),
    page: int = Query(1, ge=1),
    domain_id: str | None = Query(None),
    mission_id: str | None = Query(None),
    run_id: str | None = Query(None),
    candidate_id: str | None = Query(None),
    event_type: str | None = Query(None),
    actor_type: str | None = Query(None),
    search: str | None = Query(None),
    current_user=Depends(require_admin),
):
    service = get_research_platform_service()
    return service.list_ledger_rows(
        limit=limit,
        page=page,
        domain_id=domain_id,
        mission_id=mission_id,
        run_id=run_id,
        candidate_id=candidate_id,
        event_type=event_type,
        actor_type=actor_type,
        search=search,
    )


@router.get("/schedules", tags=["research-admin"])
def list_research_schedules(domain_id: str | None = Query(None), current_user=Depends(require_admin)):
    service = get_research_platform_service()
    return service.list_schedule_rows(domain_id=domain_id)


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


@router.post("/providers/{provider_id}/enable", tags=["research-admin"])
def enable_research_provider(provider_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        return service.set_provider_enabled(provider_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/providers/{provider_id}/disable", tags=["research-admin"])
def disable_research_provider(provider_id: str, current_user=Depends(require_admin)):
    service = get_research_platform_service()
    try:
        return service.set_provider_enabled(provider_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/digests", tags=["research-admin"])
def list_research_digests(
    digest_type: str | None = Query(None),
    domain_id: str | None = Query(None),
    limit: int = Query(30, ge=1, le=200),
    current_user=Depends(require_admin),
):
    service = get_research_platform_service()
    return {
        "digests": service.list_digests(digest_type=digest_type, domain_id=domain_id, limit=limit),
        "limit": limit,
    }
