"""
Chat Router -- Phase 14D
FastAPI endpoints for the AI chatbot.

POST /api/chat        -- single-turn question (stateless, for simple queries)
POST /api/chat/session -- multi-turn session via session_id

Sessions are stored in-memory and expire after 2 hours of inactivity.
ANTHROPIC_API_KEY must be set in the environment before starting the server.
"""

from __future__ import annotations
import os
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engines.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory session store: {session_id: (ChatEngine, last_used_ts)}
_sessions: dict[str, tuple] = {}
SESSION_TTL_SECONDS = 7200  # 2 hours


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str


def _get_or_create_session(session_id: Optional[str]) -> tuple[str, "ChatEngine"]:
    """Get existing or create new ChatEngine session."""
    from engines.ai.chatbot.chat_engine import ChatEngine

    # Evict stale sessions
    now = time.time()
    stale = [sid for sid, (_, ts) in _sessions.items() if now - ts > SESSION_TTL_SECONDS]
    for sid in stale:
        del _sessions[sid]

    if session_id and session_id in _sessions:
        engine, _ = _sessions[session_id]
        _sessions[session_id] = (engine, now)
        return session_id, engine

    # Create new session
    import uuid
    new_id = str(uuid.uuid4())[:8]
    engine = ChatEngine()
    _sessions[new_id] = (engine, now)
    return new_id, engine


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    AI chat endpoint. Accepts a message and optional session_id.
    Returns the assistant reply and session_id for follow-up turns.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="AI chat unavailable: ANTHROPIC_API_KEY not configured."
        )

    from engines.ai.chatbot.intent_router import detect_intent
    intent = detect_intent(req.message)

    try:
        session_id, engine = _get_or_create_session(req.session_id)
        reply = engine.chat(req.message)
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[ChatRouter] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        intent=intent.intent_type,
    )


@router.delete("/chat/session/{session_id}")
async def reset_session(session_id: str):
    """Clear a chat session (reset conversation history)."""
    if session_id in _sessions:
        engine, _ = _sessions[session_id]
        engine.reset()
        return {"status": "reset", "session_id": session_id}
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
