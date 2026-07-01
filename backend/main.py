"""
FastAPI Backend — Phase 10
Capital Flow Intelligence Platform API

Start:  py -3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
Docs:   http://localhost:8001/docs
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path when run from any location
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.services import data_loader
from backend.routers import market, sectors, stocks, participant, corporate, chat, data_ops, charts
from backend.ws.live_ticker import live_ticker_endpoint

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Capital Flow Intelligence Platform",
    description=(
        "REST API for institutional market intelligence — "
        "participant flows, sector rotation, bull run probability, corporate signals."
    ),
    version="1.0.0",
)

# Allow React frontend on any localhost port during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    data_loader.startup()


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(market.router)
app.include_router(sectors.router)
app.include_router(stocks.router)
app.include_router(participant.router)
app.include_router(corporate.router)
app.include_router(chat.router)
app.include_router(data_ops.router)
app.include_router(charts.router)


# ── WebSocket ─────────────────────────────────────────────────────────────────

from fastapi import WebSocket

@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    await live_ticker_endpoint(websocket)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    freshness = data_loader.freshness()
    loaded = sum(1 for v in freshness.values() if v is not None)
    return {
        "status": "ok",
        "datasets_loaded": loaded,
        "datasets_total": len(freshness),
    }


@app.get("/")
def root():
    return {"name": "Capital Flow Intelligence Platform", "version": "1.0.0"}
