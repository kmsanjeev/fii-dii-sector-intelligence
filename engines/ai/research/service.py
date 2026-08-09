from __future__ import annotations

from copy import deepcopy
from time import time

from engines.ai.research.providers import DDGSResearchProvider, MCPResearchProvider
from engines.ai.research.schemas import ResearchResult
from engines.common import config as cfg


class ResearchService:
    def __init__(self, *, providers: dict | None = None, mcp_provider=None):
        self._mcp_provider = mcp_provider or MCPResearchProvider()
        self._providers = {
            "ddgs": DDGSResearchProvider(),
            "mcp": self._mcp_provider,
        }
        if providers:
            self._providers.update(providers)
        self._cache: dict[tuple[str, str], tuple[float, ResearchResult]] = {}

    def capabilities(self) -> dict:
        provider = self._providers.get(cfg.VEDA_RESEARCH_PROVIDER)
        mcp_provider = self._providers.get("mcp")
        provider_available = bool(provider and provider.is_available())
        mcp_available = bool(cfg.VEDA_MCP_ENABLED and mcp_provider and mcp_provider.is_available())
        return {
            "research_enabled": cfg.VEDA_RESEARCH_ENABLED,
            "default_provider": cfg.VEDA_RESEARCH_PROVIDER,
            "provider_available": provider_available,
            "research_runtime_ready": bool(cfg.VEDA_RESEARCH_ENABLED and (provider_available or mcp_available)),
            "attachments_enabled": cfg.VEDA_ATTACHMENTS_ENABLED,
            "save_to_knowledge_enabled": cfg.VEDA_SAVE_TO_KNOWLEDGE_ENABLED,
            "mcp_enabled": mcp_available,
            "mcp_server_names": mcp_provider.server_names() if mcp_provider else [],
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

        cache_key = (provider_name, normalized)
        cached = self._cache.get(cache_key)
        if cached and (time() - cached[0]) < cfg.VEDA_RESEARCH_CACHE_TTL_S:
            cached_result = deepcopy(cached[1])
            cached_result.cached = True
            return cached_result

        provider = self._providers.get(provider_name)
        if provider is None:
            result.error = f"unknown_provider:{provider_name}"
            final = self._apply_mcp_fallback(normalized, reason=reason, primary=result)
            self._cache[cache_key] = (time(), deepcopy(final))
            return final
        if not provider.is_available():
            result.error = "provider_unavailable"
            final = self._apply_mcp_fallback(normalized, reason=reason, primary=result)
            self._cache[cache_key] = (time(), deepcopy(final))
            return final

        fresh = provider.search(normalized, reason=reason)
        final = self._apply_mcp_fallback(normalized, reason=reason, primary=fresh)

        self._cache[cache_key] = (time(), deepcopy(final))
        return final

    def _apply_mcp_fallback(self, query: str, *, reason: str, primary: ResearchResult) -> ResearchResult:
        mcp_provider = self._providers.get("mcp")
        should_try_mcp = (
            primary.provider != "mcp"
            and bool(mcp_provider)
            and cfg.VEDA_MCP_ENABLED
            and mcp_provider.is_available()
            and not primary.used
        )
        if not should_try_mcp:
            return primary

        final = deepcopy(primary)
        fallback = mcp_provider.search(query, reason=reason)
        if fallback.used:
            return fallback
        if fallback.error:
            if final.error and final.error != fallback.error:
                final.error = f"{final.error}; {fallback.error}"
            else:
                final.error = fallback.error
        return final


_SERVICE: ResearchService | None = None


def get_research_service() -> ResearchService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ResearchService()
    return _SERVICE
