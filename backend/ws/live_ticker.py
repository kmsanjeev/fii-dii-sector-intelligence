"""
Live Ticker — Phase 10
WebSocket endpoint: ws://host/ws/live
Pushes market regime + top sector scores every 30 seconds during market hours.
Outside market hours: sends a single snapshot then keeps alive with heartbeat.
"""

import asyncio
import json
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from engines.common.logger import get_logger
from backend.services import data_loader

logger = get_logger(__name__)

HEARTBEAT_INTERVAL = 30   # seconds between pushes


def _is_market_hours() -> bool:
    now = datetime.now()
    t = now.hour * 60 + now.minute
    return (9 * 60 + 15) <= t <= (15 * 60 + 30)


def _build_tick() -> dict:
    tick: dict = {"ts": datetime.now().isoformat(), "market_hours": _is_market_hours()}

    # Regime
    df = data_loader.get("participant_intel")
    if df is not None and not df.empty:
        latest = df.sort_values("date").iloc[-1]
        tick["regime"] = str(latest.get("Market_Regime", "UNKNOWN"))
        tick["smart_money"] = round(float(latest.get("Smart_Money_Score", 0) or 0), 2)

    # Top 3 sectors
    sdf = data_loader.get("sector_rotation")
    if sdf is not None and not sdf.empty:
        top3 = sdf.nlargest(3, "combined_score")[["sector", "rotation_signal", "combined_score"]]
        tick["top_sectors"] = top3.to_dict(orient="records")

    return tick


async def live_ticker_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"[LiveTicker] Client connected: {websocket.client}")

    try:
        while True:
            tick = _build_tick()
            await websocket.send_text(json.dumps(tick))
            await asyncio.sleep(HEARTBEAT_INTERVAL)
    except WebSocketDisconnect:
        logger.info(f"[LiveTicker] Client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"[LiveTicker] Error: {e}")
        await websocket.close()
