from __future__ import annotations

from copy import deepcopy
from time import time

from engines.ai.research.providers import DDGSResearchProvider
from engines.ai.research.schemas import ResearchResult
from engines.common import config as cfg


class ResearchService:
    def __init__(self):
        self._providers = {
            "ddgs": DDGSResearchProvider(),
        }
        self._cache: dict[tuple[str, str], tuple[float, ResearchResult]] = {}

    def capabilities(self) -> dict:
        provider = self._providers.get(cfg.VEDA_RESEARCH_PROVIDER)
        return {
            "research_enabled": cfg.VEDA_RESEARCH_ENABLED,
            "default_provider": cfg.VEDA_RESEARCH_PROVIDER,
            "provider_available": bool(provider and provider.is_available()),
            "attachments_enabled": cfg.VEDA_ATTACHMENTS_ENABLED,
            "save_to_knowledge_enabled": cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED,
            "mcp_enabled": cfg.VEDA_MCP_ENABLED,
        }

    def search(self, query: str, *, reason: str) -> ResearchResult:
        normalized = " ".join((query or "").split())[: cfg.VEDA_RESEARCH_MAX_QUERY_CHARS].strip()
        provider_name = cfg.VEDA_RESEARCH_PROVIDER
        result = ResearchResult(provider=provider_name, query=normalized, reason=reason)

        if not cfg.VEDA_RESEARCH_ENABLED:
            result.error = "research_disabled"
            return result
        if not normalized:
            result.error = "empty_query"
            return result

        provider = self._providers.get(provider_name)
        if provider is None:
            result.error = f"unknown_provider:{provider_name}"
            return result
        if not provider.is_available():
            result.error = "provider_unavailable"
            return result

        cache_key = (provider_name, normalized)
        cached = self._cache.get(cache_key)
        if cached and (time() - cached[0]) < cfg.VEDA_RESEARCH_CACHE_TTL_S:
            cached_result = deepcopy(cached[1])
            cached_result.cached = True
            return cached_result

        fresh = provider.search(normalized, reason=reason)
        self._cache[cache_key] = (time(), deepcopy(fresh))
        return fresh


_SERVICE: ResearchService | None = None


def get_research_service() -> ResearchService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ResearchService()
    return _SERVICE
