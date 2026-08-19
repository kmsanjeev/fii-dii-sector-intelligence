from __future__ import annotations

import json
from urllib.parse import urlparse

from engines.ai.research.mcp_client import (
    MCPClientError,
    MCPServerConfig,
    MCPStdioClient,
    MCPToolDefinition,
    command_exists,
    load_mcp_server_configs,
)
from engines.ai.research.providers.base import BaseResearchProvider
from engines.ai.research.schemas import ResearchResult, ResearchSource
from engines.ai.capabilities import get_state
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

_QUERY_FIELDS = ("query", "q", "search_query", "keywords", "question", "prompt", "input", "text")
_LIMIT_FIELDS = ("limit", "max_results", "maxResults", "count", "top_k", "num_results", "numResults")
_RESULT_KEYS = ("results", "items", "sources", "data", "repositories", "documents", "hits", "entries")
_URL_FIELDS = ("url", "html_url", "href", "link", "web_url")
_TITLE_FIELDS = ("title", "name", "full_name", "headline", "path")
_SNIPPET_FIELDS = ("snippet", "description", "body", "text", "content", "summary", "excerpt")
_DATE_FIELDS = ("published_at", "date", "updated_at", "created_at")
_DEFAULT_SEARCH_TOOL_NAMES = {
    "github": ["search_repositories", "search_code", "search"],
    "ddgs": ["search", "text_search", "web_search"],
    "tavily": ["search", "tavily_search", "research"],
    "exa": ["search", "search_and_contents", "find_similar"],
    "firecrawl": ["search", "crawl", "map"],
    "fetch": ["fetch", "read_url", "get_page"],
}


class MCPResearchProvider(BaseResearchProvider):
    name = "mcp"

    def __init__(self, server_configs: list[MCPServerConfig] | None = None):
        self._server_configs = server_configs

    def server_names(self) -> list[str]:
        return [server.name for server in self._ordered_servers()]

    def is_available(self) -> bool:
        if not cfg.VEDA_MCP_ENABLED or get_state("MCP").effective_access != "ENABLED":
            return False
        return any(command_exists(server.command) for server in self._ordered_servers())

    def search(self, query: str, *, reason: str) -> ResearchResult:
        result = ResearchResult(provider=self.name, query=query, reason=reason)
        if not cfg.VEDA_MCP_ENABLED or get_state("MCP").effective_access != "ENABLED":
            result.error = "mcp_disabled"
            return result

        errors: list[str] = []
        servers = self._ordered_servers()
        if not servers:
            result.error = "mcp_config_missing"
            return result

        for server in servers:
            if not command_exists(server.command):
                errors.append(f"{server.name}:command_not_found")
                continue
            try:
                with MCPStdioClient(server) as client:
                    client.initialize()
                    tools = client.list_tools()
                    tool = self._choose_search_tool(server, tools, query)
                    if tool is None:
                        errors.append(f"{server.name}:no_search_tool")
                        continue
                    arguments = self._build_call_args(tool, query)
                    if arguments is None:
                        errors.append(f"{server.name}:tool_args_unsupported")
                        continue
                    tool_result = client.call_tool(tool.name, arguments)
                sources = self._extract_sources(server, tool.name, tool_result)
            except MCPClientError as exc:
                errors.append(f"{server.name}:{exc}")
                continue
            except Exception as exc:
                errors.append(f"{server.name}:{exc}")
                continue

            if not sources:
                errors.append(f"{server.name}:no_results")
                continue

            result.provider = f"mcp:{server.name}"
            result.sources = sources[: cfg.VEDA_MCP_MAX_RESULTS]
            result.used = True
            return result

        result.error = "; ".join(errors[:4]) if errors else "mcp_no_results"
        return result

    def _ordered_servers(self) -> list[MCPServerConfig]:
        raw_servers = self._server_configs if self._server_configs is not None else load_mcp_server_configs()
        enabled = [server for server in raw_servers if server.enabled]
        order = [
            item.strip().lower()
            for item in cfg.VEDA_MCP_SERVER_ORDER.split(",")
            if item.strip()
        ]
        if not order:
            return enabled

        rank = {name: index for index, name in enumerate(order)}
        return sorted(
            enabled,
            key=lambda server: (rank.get(server.name.lower(), len(rank) + 1), server.name.lower()),
        )

    def _choose_search_tool(
        self,
        server: MCPServerConfig,
        tools: list[MCPToolDefinition],
        query: str,
    ) -> MCPToolDefinition | None:
        scored: list[tuple[int, MCPToolDefinition]] = []
        for tool in tools:
            args = self._build_call_args(tool, query)
            if args is None:
                continue
            score = self._score_tool(server, tool)
            if score > 0:
                scored.append((score, tool))
        if not scored:
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    def _score_tool(self, server: MCPServerConfig, tool: MCPToolDefinition) -> int:
        haystack = " ".join(filter(None, [
            tool.name.lower(),
            (tool.title or "").lower(),
            (tool.description or "").lower(),
        ]))
        score = 0
        preferred = server.search_tools or _DEFAULT_SEARCH_TOOL_NAMES.get(server.name.lower(), [])
        for pref in preferred:
            pref_lower = pref.lower()
            if tool.name.lower() == pref_lower:
                score += 15
            elif pref_lower in haystack:
                score += 8
        if "search" in haystack:
            score += 6
        if server.name.lower() == "github" and ("repo" in haystack or "code" in haystack):
            score += 4
        if any(field in (tool.input_schema.get("properties", {}) or {}) for field in _QUERY_FIELDS):
            score += 3
        return score

    def _build_call_args(self, tool: MCPToolDefinition, query: str) -> dict | None:
        schema = tool.input_schema or {}
        properties = schema.get("properties", {}) or {}
        required = set(schema.get("required", []) or [])
        arguments: dict[str, object] = {}

        for field in _QUERY_FIELDS:
            if field in properties:
                arguments[field] = query
                break
        for field in _LIMIT_FIELDS:
            if field in properties:
                arguments[field] = cfg.VEDA_MCP_MAX_RESULTS
                break

        unresolved = [name for name in required if name not in arguments]
        if unresolved:
            return None
        if not arguments and properties:
            return None
        return arguments

    def _extract_sources(self, server: MCPServerConfig, tool_name: str, result: dict) -> list[ResearchSource]:
        items = self._extract_items(result.get("structuredContent"))
        if not items:
            for block in result.get("content", []) or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "text":
                    continue
                text = str(block.get("text") or "").strip()
                if not text:
                    continue
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = None
                if parsed is not None:
                    items.extend(self._extract_items(parsed))
                if items:
                    break

        sources: list[ResearchSource] = []
        seen_urls: set[str] = set()
        for item in items:
            source = self._normalize_item(server, tool_name, item)
            if source is None:
                continue
            if source.url in seen_urls:
                continue
            seen_urls.add(source.url)
            sources.append(source)
            if len(sources) >= cfg.VEDA_RESEARCH_MAX_RESULTS:
                break
        return sources

    def _extract_items(self, payload: object) -> list[dict]:
        if payload is None:
            return []
        if isinstance(payload, list):
            items: list[dict] = []
            for value in payload:
                items.extend(self._extract_items(value))
            return items
        if not isinstance(payload, dict):
            return []

        items: list[dict] = []
        if any(field in payload for field in _URL_FIELDS):
            items.append(payload)
        for key in _RESULT_KEYS:
            value = payload.get(key)
            if value is not None:
                items.extend(self._extract_items(value))
        return items

    def _normalize_item(self, server: MCPServerConfig, tool_name: str, item: dict) -> ResearchSource | None:
        url = ""
        for field in _URL_FIELDS:
            candidate = str(item.get(field) or "").strip()
            if candidate.startswith(("http://", "https://")):
                url = candidate
                break
        if not url:
            return None

        title = ""
        for field in _TITLE_FIELDS:
            title = str(item.get(field) or "").strip()
            if title:
                break
        if not title:
            title = url

        snippet = ""
        for field in _SNIPPET_FIELDS:
            raw = item.get(field)
            if raw is None:
                continue
            if isinstance(raw, (dict, list)):
                snippet = json.dumps(raw, ensure_ascii=False)
            else:
                snippet = str(raw).strip()
            if snippet:
                break
        if len(snippet) > cfg.VEDA_RESEARCH_MAX_SNIPPET_CHARS:
            snippet = snippet[: cfg.VEDA_RESEARCH_MAX_SNIPPET_CHARS - 3].rstrip() + "..."

        published_at = None
        for field in _DATE_FIELDS:
            value = str(item.get(field) or "").strip()
            if value:
                published_at = value
                break

        source_name = str(item.get("source") or item.get("provider") or "").strip()
        if not source_name:
            host = urlparse(url).netloc
            source_name = host or f"MCP {server.name}"

        kind = str(item.get("kind") or item.get("type") or server.name or tool_name).strip() or "text"

        return ResearchSource(
            title=title[:240],
            url=url,
            snippet=snippet,
            source=source_name[:120],
            published_at=published_at,
            kind=kind[:40],
        )
