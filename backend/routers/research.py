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

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from engines.research.screener_engine import screen, compare, universe_stats
from engines.research import notes_engine

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
