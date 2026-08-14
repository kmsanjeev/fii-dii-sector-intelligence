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
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.auth.middleware import require_auth
from backend.auth.store import User, is_auth_enabled
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
    temporary: bool = True
    save_requires_review: bool = True
    conflict_note: Optional[str] = None
    governance_note: Optional[str] = None


class ChatLocalEvidenceSource(BaseModel):
    source_id: str
    source_type: str
    source_label: str
    evidence_kind: str
    evidence_label: str
    knowledge_class: Optional[str] = None
    domain: str
    title: str
    entity: Optional[str] = None
    date: Optional[str] = None
    freshness_class: Optional[str] = None
    confidence: Optional[float] = None
    summary: Optional[str] = None
    attachment_name: Optional[str] = None
    repo_label: Optional[str] = None
    license_name: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    score_meaning: Optional[str] = None
    reliability_note: Optional[str] = None
    claim_ids: list[str] = Field(default_factory=list)
    passage_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    version: Optional[str] = None
    version_state: Optional[str] = None
    high_stakes: bool = False
    authority: dict[str, Any] = Field(default_factory=dict)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    citation_labels: list[str] = Field(default_factory=list)
    conflict_details: list[dict[str, Any]] = Field(default_factory=list)
    rank: int = 0


class ChatLocalEvidenceMeta(BaseModel):
    used: bool = False
    source_count: int = 0
    evidence_kinds: list[str] = Field(default_factory=list)
    knowledge_classes: list[str] = Field(default_factory=list)
    approved_core_count: int = 0
    reviewed_internal_count: int = 0
    local_platform_count: int = 0
    legacy_unsourced_count: int = 0
    predictive_ml_count: int = 0
    platform_snapshot_count: int = 0
    approved_memory_count: int = 0
    attachment_memory_count: int = 0
    repo_count: int = 0
    conflict_count: int = 0
    citation_count: int = 0
    high_stakes_count: int = 0
    top_date: Optional[str] = None
    sources: list[ChatLocalEvidenceSource] = Field(default_factory=list)
    conflict_note: Optional[str] = None
    freshness_note: Optional[str] = None
    known_conflicts: list[dict[str, Any]] = Field(default_factory=list)


class ChatRetrievalAudit(BaseModel):
    shadow_enabled: bool = False
    configured_primary_mode: str = "unified"
    resolved_primary_mode: str = "unified"
    primary_used: bool = False
    primary_source_count: int = 0
    primary_approved_core_hits: int = 0
    primary_reviewed_internal_hits: int = 0
    primary_local_platform_hits: int = 0
    primary_ml_hits: int = 0
    primary_conflict_count: int = 0
    primary_citation_count: int = 0
    primary_attribution_quality: float = 0.0
    primary_duplicate_noise: float = 0.0
    shadow_mode: Optional[str] = None
    shadow_used: bool = False
    shadow_source_count: int = 0
    shadow_approved_core_hits: int = 0
    shadow_reviewed_internal_hits: int = 0
    shadow_local_platform_hits: int = 0
    shadow_ml_hits: int = 0
    shadow_conflict_count: int = 0
    shadow_citation_count: int = 0
    shadow_attribution_quality: float = 0.0
    shadow_duplicate_noise: float = 0.0
    overlap_count: int = 0
    overlap_rate: float = 0.0
    only_in_primary: list[str] = Field(default_factory=list)
    only_in_shadow: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    primary_error: Optional[str] = None
    shadow_error: Optional[str] = None


class ChatCapabilities(BaseModel):
    research_enabled: bool
    research_provider_available: bool
    research_runtime_ready: bool
    default_research_provider: str
    auto_research_for_research_intent: bool
    attachments_enabled: bool
    save_to_knowledge_enabled: bool
    mit_repo_intake_enabled: bool
    mcp_enabled: bool
    mcp_server_names: list[str] = Field(default_factory=list)
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
    local_evidence: ChatLocalEvidenceMeta = Field(default_factory=ChatLocalEvidenceMeta)
    retrieval_audit: ChatRetrievalAudit = Field(default_factory=ChatRetrievalAudit)
    orchestration: dict[str, Any] = Field(default_factory=dict)
    conversational_context: dict[str, Any] = Field(default_factory=dict)


class ChatKnowledgeSource(BaseModel):
    kind: str
    title: str
    url: Optional[str] = None
    published_at: Optional[str] = None
    excerpt: Optional[str] = None
    storage_key: Optional[str] = None
    warning: Optional[str] = None


class ChatKnowledgeDraftRequest(BaseModel):
    question: str
    answer: str
    intent: Optional[str] = None
    session_id: Optional[str] = None
    research: ChatResearchMeta = Field(default_factory=ChatResearchMeta)
    attachments: list[ChatAttachment] = Field(default_factory=list)


class ChatKnowledgeDraft(BaseModel):
    draft_id: str
    title: str
    summary: str
    facts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_question: str
    raw_answer: str
    intent: Optional[str] = None
    session_id: Optional[str] = None
    created_at: str
    sources: list[ChatKnowledgeSource] = Field(default_factory=list)
    existing_matches: list["ChatKnowledgeExistingMatch"] = Field(default_factory=list)
    suggested_action: str = "save"
    suggestion_reason: Optional[str] = None
    status: str = "draft"


class ChatKnowledgeExistingMatch(BaseModel):
    doc_id: str
    title: str
    summary: str
    saved_at: Optional[str] = None
    memory_type: str = "reviewed_note"
    overlap_score: int = 0
    semantic_score: int = 0
    reason: Optional[str] = None
    exact_duplicate: bool = False
    new_value_hint: Optional[str] = None


class ChatKnowledgeApproveRequest(BaseModel):
    title: str
    summary: str
    facts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    review_note: Optional[str] = None
    decision: Optional[str] = None


class ChatKnowledgeSaved(BaseModel):
    draft_id: str
    doc_id: str
    saved_at: str
    title: str
    status: str = "approved"
    duplicate: bool = False
    attachment_doc_count: int = 0
    attachment_chunk_count: int = 0
    decision: Optional[str] = None
    merged_into_doc_id: Optional[str] = None


class ChatKnowledgeDiscarded(BaseModel):
    draft_id: str
    status: str = "discarded"


class ChatSavedMessage(BaseModel):
    role: str
    content: str
    intent: Optional[str] = None
    ts: int
    research: Optional[ChatResearchMeta] = None
    localEvidence: Optional[ChatLocalEvidenceMeta] = None
    attachments: list[ChatAttachment] = Field(default_factory=list)
    knowledge: Optional[ChatKnowledgeSaved] = None


class ChatSavedSession(BaseModel):
    id: str
    title: str
    messages: list[ChatSavedMessage] = Field(default_factory=list)
    backendSessionId: Optional[str] = None
    createdAt: int
    updatedAt: int


class ChatSavedSessionList(BaseModel):
    sessions: list[ChatSavedSession] = Field(default_factory=list)


class ChatRepoCapabilityDraftRequest(BaseModel):
    repo_path: str
    repo_label: Optional[str] = None
    focus: Optional[str] = None


class ChatRepoCapabilityDraft(BaseModel):
    draft_id: str
    repo_path: str
    repo_label: str
    focus: Optional[str] = None
    title: str
    summary: str
    facts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    license_name: str
    license_path: str
    license_excerpt: str
    candidate_files: list[str] = Field(default_factory=list)
    created_at: str
    sources: list[ChatKnowledgeSource] = Field(default_factory=list)
    status: str = "draft"


class ChatRepoCapabilityApproveRequest(BaseModel):
    title: str
    summary: str
    facts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    review_note: Optional[str] = None


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


def _resolve_history_owner(current_user: User, client_id: Optional[str]) -> str:
    if is_auth_enabled():
        return f"user::{current_user.id}"
    cleaned = "".join(
        char if char.isalnum() or char in "._-" else "_"
        for char in (client_id or "").strip()
    )[:80].strip("._-")
    return f"client::{cleaned or 'browser'}"


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    AI chat endpoint. Accepts a message and optional session_id.
    Returns the assistant reply and session_id for follow-up turns.
    """
    # Any one configured provider is enough -- the engine rotates through all
    _PROVIDER_KEYS = ("GROQ_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY",
                      "GITHUB_MODELS_TOKEN", "SAMBANOVA_API_KEY",
                      "OPENROUTER_API_KEY", "CEREBRAS_API_KEY", "OPENAI_API_KEY")
    if not any(os.getenv(k) for k in _PROVIDER_KEYS):
        raise HTTPException(
            status_code=503,
            detail="AI chat unavailable: no LLM provider key configured. "
                   "Add at least one of GROQ/GEMINI/MISTRAL/GITHUB_MODELS/"
                   "SAMBANOVA/OPENROUTER/CEREBRAS/OPENAI keys to .env"
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
    last_local_evidence = getattr(engine, "last_local_evidence", {})
    last_retrieval_audit = getattr(engine, "last_retrieval_audit", {})
    last_orchestration = getattr(engine, "last_orchestration", {})
    conversational_context = getattr(engine, "last_conversational_context", {})
    return ChatResponse(
        reply=reply,
        session_id=session_id,
        intent=intent.intent_type,
        symbols_discussed=symbols_discussed,
        flagged=last_flag.get("flagged", False),
        flag_reason=last_flag.get("reason"),
        research=ChatResearchMeta(**last_research),
        local_evidence=ChatLocalEvidenceMeta(**last_local_evidence),
        retrieval_audit=ChatRetrievalAudit(**last_retrieval_audit),
        orchestration=last_orchestration,
        conversational_context=conversational_context,
    )


@router.get("/chat/capabilities", response_model=ChatCapabilities)
async def chat_capabilities():
    capabilities = {
        "research_enabled": cfg.VEDA_RESEARCH_ENABLED,
        "provider_available": False,
        "research_runtime_ready": False,
        "default_provider": cfg.VEDA_RESEARCH_PROVIDER,
        "attachments_enabled": cfg.VEDA_ATTACHMENTS_ENABLED,
        "save_to_knowledge_enabled": cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED,
        "mcp_enabled": cfg.VEDA_MCP_ENABLED,
        "mcp_server_names": [],
    }
    try:
        from engines.ai.research import get_research_service

        capabilities = get_research_service().capabilities()
    except Exception as exc:
        logger.debug("[ChatRouter] Research capabilities fallback used: %s", exc)
    return ChatCapabilities(
        research_enabled=bool(capabilities.get("research_enabled", cfg.VEDA_RESEARCH_ENABLED)),
        research_provider_available=bool(capabilities.get("provider_available", False)),
        research_runtime_ready=bool(capabilities.get("research_runtime_ready", False)),
        default_research_provider=str(capabilities.get("default_provider", cfg.VEDA_RESEARCH_PROVIDER)),
        auto_research_for_research_intent=cfg.VEDA_RESEARCH_AUTO_FOR_RESEARCH_INTENT,
        attachments_enabled=bool(capabilities.get("attachments_enabled", cfg.VEDA_ATTACHMENTS_ENABLED)),
        save_to_knowledge_enabled=bool(capabilities.get("save_to_knowledge_enabled", cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED)),
        mit_repo_intake_enabled=cfg.VEDA_MIT_REPO_INTAKE_ENABLED,
        mcp_enabled=bool(capabilities.get("mcp_enabled", cfg.VEDA_MCP_ENABLED)),
        mcp_server_names=[str(name) for name in capabilities.get("mcp_server_names", []) or []],
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


@router.post("/chat/knowledge/draft", response_model=ChatKnowledgeDraft)
async def create_chat_knowledge_draft(req: ChatKnowledgeDraftRequest):
    if not cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED:
        raise HTTPException(status_code=503, detail="Save to knowledge is disabled.")
    try:
        from engines.ai.knowledge.review_service import get_knowledge_review_service

        draft = get_knowledge_review_service().create_draft(
            question=req.question,
            answer=req.answer,
            intent=req.intent,
            session_id=req.session_id,
            research=req.research.model_dump(),
            attachments=[attachment.model_dump() for attachment in req.attachments],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("[ChatRouter] Knowledge draft creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Knowledge draft creation failed: {exc}")

    return ChatKnowledgeDraft(**draft.to_dict())


@router.post("/chat/knowledge/draft/{draft_id}/approve", response_model=ChatKnowledgeSaved)
async def approve_chat_knowledge_draft(draft_id: str, req: ChatKnowledgeApproveRequest):
    if not cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED:
        raise HTTPException(status_code=503, detail="Save to knowledge is disabled.")
    try:
        from engines.ai.knowledge.review_service import get_knowledge_review_service

        result = get_knowledge_review_service().approve(
            draft_id,
            title=req.title,
            summary=req.summary,
            facts=req.facts,
            tags=req.tags,
            review_note=req.review_note,
            decision=req.decision,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Knowledge draft '{draft_id}' was not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("[ChatRouter] Knowledge approval failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Knowledge approval failed: {exc}")

    return ChatKnowledgeSaved(**result)


@router.delete("/chat/knowledge/draft/{draft_id}", response_model=ChatKnowledgeDiscarded)
async def discard_chat_knowledge_draft(draft_id: str):
    if not cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED:
        raise HTTPException(status_code=503, detail="Save to knowledge is disabled.")
    try:
        from engines.ai.knowledge.review_service import get_knowledge_review_service

        result = get_knowledge_review_service().discard(draft_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Knowledge draft '{draft_id}' was not found.")
    except Exception as exc:
        logger.error("[ChatRouter] Knowledge discard failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Knowledge discard failed: {exc}")

    return ChatKnowledgeDiscarded(**result)


@router.post("/chat/capabilities/repo/draft", response_model=ChatRepoCapabilityDraft)
async def create_repo_capability_draft(req: ChatRepoCapabilityDraftRequest):
    if not cfg.VEDA_MIT_REPO_INTAKE_ENABLED:
        raise HTTPException(status_code=503, detail="MIT repo capability intake is disabled.")
    try:
        from engines.ai.capabilities import get_repo_capability_service

        draft = get_repo_capability_service().create_draft(
            repo_path=req.repo_path,
            repo_label=req.repo_label,
            focus=req.focus,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("[ChatRouter] Repo capability draft creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Repo capability draft creation failed: {exc}")

    return ChatRepoCapabilityDraft(**draft.to_dict())


@router.post("/chat/capabilities/repo/draft/{draft_id}/approve", response_model=ChatKnowledgeSaved)
async def approve_repo_capability_draft(draft_id: str, req: ChatRepoCapabilityApproveRequest):
    if not cfg.VEDA_MIT_REPO_INTAKE_ENABLED:
        raise HTTPException(status_code=503, detail="MIT repo capability intake is disabled.")
    try:
        from engines.ai.capabilities import get_repo_capability_service

        result = get_repo_capability_service().approve(
            draft_id,
            title=req.title,
            summary=req.summary,
            facts=req.facts,
            tags=req.tags,
            review_note=req.review_note,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Repo capability draft '{draft_id}' was not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("[ChatRouter] Repo capability approval failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Repo capability approval failed: {exc}")

    return ChatKnowledgeSaved(**result)


@router.get("/chat/sessions", response_model=ChatSavedSessionList)
async def list_saved_chat_sessions(
    current_user: User = Depends(require_auth),
    x_veda_client_id: Optional[str] = Header(None),
):
    from engines.ai.chat_history import get_chat_history_service

    owner_key = _resolve_history_owner(current_user, x_veda_client_id)
    sessions = get_chat_history_service().list_sessions(owner_key)
    return ChatSavedSessionList(sessions=[ChatSavedSession(**session) for session in sessions])


@router.put("/chat/sessions/{session_id}", response_model=ChatSavedSession)
async def upsert_saved_chat_session(
    session_id: str,
    req: ChatSavedSession,
    current_user: User = Depends(require_auth),
    x_veda_client_id: Optional[str] = Header(None),
):
    if req.id != session_id:
        raise HTTPException(status_code=400, detail="Session id in path and body must match.")

    from engines.ai.chat_history import get_chat_history_service

    owner_key = _resolve_history_owner(current_user, x_veda_client_id)
    saved = get_chat_history_service().upsert_session(owner_key, req.model_dump())
    return ChatSavedSession(**saved)


@router.delete("/chat/sessions/{session_id}")
async def delete_saved_chat_session(
    session_id: str,
    current_user: User = Depends(require_auth),
    x_veda_client_id: Optional[str] = Header(None),
):
    from engines.ai.chat_history import get_chat_history_service

    owner_key = _resolve_history_owner(current_user, x_veda_client_id)
    deleted = get_chat_history_service().delete_session(owner_key, session_id)
    return {"status": "deleted" if deleted else "not_found", "session_id": session_id}


@router.delete("/chat/sessions")
async def delete_all_saved_chat_sessions(
    current_user: User = Depends(require_auth),
    x_veda_client_id: Optional[str] = Header(None),
):
    from engines.ai.chat_history import get_chat_history_service

    owner_key = _resolve_history_owner(current_user, x_veda_client_id)
    deleted = get_chat_history_service().delete_all_sessions(owner_key)
    return {"status": "deleted", "count": deleted}


@router.delete("/chat/session/{session_id}")
async def reset_session(session_id: str):
    """Clear a chat session (reset conversation history)."""
    if session_id in _sessions:
        engine, _ = _sessions[session_id]
        engine.reset()
        return {"status": "reset", "session_id": session_id}
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
