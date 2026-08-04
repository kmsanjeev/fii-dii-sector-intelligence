"""
Chat Router -- Phase 14D
FastAPI endpoints for the AI chatbot.

POST /api/chat        -- single-turn question (stateless, for simple queries)
POST /api/chat/session -- multi-turn session via session_id

Sessions are stored in-memory and expire after 2 hours of inactivity.
"""

from __future__ import annotations
import os
import time
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api")

# In-memory session store: {session_id: (ChatEngine, last_used_ts)}
_sessions: dict[str, tuple] = {}
SESSION_TTL_SECONDS = 7200  # 2 hours


class ChatAttachment(BaseModel):
    name: str
    mime_type: str
    size_bytes: Optional[int] = None
    storage_key: Optional[str] = None
    excerpt: Optional[str] = None
    kind: Optional[str] = None
    warning: Optional[str] = None


class ChatResearchSource(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None
    kind: str = "text"


class ChatResearchMeta(BaseModel):
    requested: bool = False
    used: bool = False
    provider: Optional[str] = None
    reason: Optional[str] = None
    source_count: int = 0
    cached: bool = False
    error: Optional[str] = None
    sources: list[ChatResearchSource] = Field(default_factory=list)


class ChatCapabilities(BaseModel):
    research_enabled: bool
    default_research_provider: str
    auto_research_for_research_intent: bool
    attachments_enabled: bool
    save_to_knowledge_enabled: bool
    mcp_enabled: bool
    supported_attachment_mime_prefixes: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: str = "text"          # "voice" -> spoken-style replies (Phase V2)
    research_mode: bool = False
    attachments: list[ChatAttachment] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str
    symbols_discussed: list[str] = Field(default_factory=list)   # Phase V-DATA-3 -- language-agnostic
                                                                 # (from actual tool calls, not text regex)
    flagged: bool = False               # output-side safety classification
    flag_reason: Optional[str] = None   # "refused" | "prompt_leak" | None
    research: ChatResearchMeta = Field(default_factory=ChatResearchMeta)


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
    # Any one configured provider is enough -- the engine rotates through all
    _PROVIDER_KEYS = ("GROQ_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY",
                      "GITHUB_MODELS_TOKEN", "SAMBANOVA_API_KEY",
                      "OPENROUTER_API_KEY", "CEREBRAS_API_KEY")
    if not any(os.getenv(k) for k in _PROVIDER_KEYS):
        raise HTTPException(
            status_code=503,
            detail="AI chat unavailable: no LLM provider key configured. "
                   "Add at least one of GROQ/GEMINI/MISTRAL/GITHUB_MODELS/"
                   "SAMBANOVA/OPENROUTER/CEREBRAS keys to .env"
        )

    from engines.ai.chatbot.intent_router import detect_intent
    intent = detect_intent(req.message)
    if req.attachments and not cfg.VEDA_ATTACHMENTS_ENABLED:
        raise HTTPException(status_code=503, detail="Veda attachments are disabled.")

    try:
        session_id, engine = _get_or_create_session(req.session_id)
        attachment_context = ""
        if req.attachments:
            from engines.ai.attachments import get_attachment_service
            attachment_context = get_attachment_service().build_prompt_context(req.attachments)
        reply = engine.chat(
            req.message,
            voice_mode=(req.mode == "voice"),
            research_mode=req.research_mode,
            attachment_context=attachment_context,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ChatRouter] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

    symbols_discussed = sorted(set(getattr(engine, "last_symbols", [])))
    last_flag = getattr(engine, "last_flag", {"flagged": False, "reason": None})
    last_research = getattr(engine, "last_research", {})
    return ChatResponse(
        reply=reply,
        session_id=session_id,
        intent=intent.intent_type,
        symbols_discussed=symbols_discussed,
        flagged=last_flag.get("flagged", False),
        flag_reason=last_flag.get("reason"),
        research=ChatResearchMeta(**last_research),
    )


@router.get("/chat/capabilities", response_model=ChatCapabilities)
async def chat_capabilities():
    return ChatCapabilities(
        research_enabled=cfg.VEDA_RESEARCH_ENABLED,
        default_research_provider=cfg.VEDA_RESEARCH_PROVIDER,
        auto_research_for_research_intent=cfg.VEDA_RESEARCH_AUTO_FOR_RESEARCH_INTENT,
        attachments_enabled=cfg.VEDA_ATTACHMENTS_ENABLED,
        save_to_knowledge_enabled=cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED,
        mcp_enabled=cfg.VEDA_MCP_ENABLED,
        supported_attachment_mime_prefixes=[
            "application/pdf",
            "image/",
            "text/",
            "application/json",
        ],
    )


@router.post("/chat/attachments", response_model=ChatAttachment)
async def upload_chat_attachment(file: UploadFile = File(...)):
    if not cfg.VEDA_ATTACHMENTS_ENABLED:
        raise HTTPException(status_code=503, detail="Veda attachments are disabled.")

    raw = await file.read()
    try:
        from engines.ai.attachments import get_attachment_service

        prepared = get_attachment_service().save_upload(
            filename=file.filename or "attachment",
            content_type=file.content_type or "",
            content=raw,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("[ChatRouter] Attachment upload failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Attachment upload failed: {exc}")

    return ChatAttachment(**prepared.to_chat_stub())


@router.delete("/chat/session/{session_id}")
async def reset_session(session_id: str):
    """Clear a chat session (reset conversation history)."""
    if session_id in _sessions:
        engine, _ = _sessions[session_id]
        engine.reset()
        return {"status": "reset", "session_id": session_id}
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
