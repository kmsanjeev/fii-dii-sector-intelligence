from __future__ import annotations

import json
import sys
from pathlib import Path

from engines.ai.research.mcp_client import MCPServerConfig
from engines.ai.research.providers.mcp_provider import MCPResearchProvider
from engines.ai.research.schemas import ResearchResult, ResearchSource
from engines.ai.research.service import ResearchService
from engines.common import config as cfg


def _write_fake_mcp_server(path: Path) -> None:
    path.write_text(
        """
import json
import sys

TOOLS = [
    {
        "name": "search_repositories",
        "title": "Search Repositories",
        "description": "Search repository docs and examples by query",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["query"]
        }
    }
]

def send(payload):
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\\n")
    sys.stdout.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    msg = json.loads(line)
    method = msg.get("method")
    if method == "initialize":
        send({
            "jsonrpc": "2.0",
            "id": msg["id"],
            "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake-mcp", "version": "1.0.0"}
            }
        })
    elif method == "notifications/initialized":
        continue
    elif method == "tools/list":
        send({
            "jsonrpc": "2.0",
            "id": msg["id"],
            "result": {"tools": TOOLS}
        })
    elif method == "tools/call":
        query = msg.get("params", {}).get("arguments", {}).get("query", "")
        send({
            "jsonrpc": "2.0",
            "id": msg["id"],
            "result": {
                "content": [{"type": "text", "text": "Fake MCP search completed."}],
                "structuredContent": {
                    "results": [
                        {
                            "title": "Open MCP Repo",
                            "html_url": "https://github.com/example/open-mcp-repo",
                            "description": f"Result for {query}",
                            "updated_at": "2026-08-04T10:00:00Z",
                            "source": "GitHub"
                        }
                    ]
                },
                "isError": False
            }
        })
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_mcp_provider_uses_fake_server(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_MCP_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_MCP_MAX_RESULTS", 4)
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_MAX_SNIPPET_CHARS", 280)

    script = tmp_dir / "fake_mcp_server.py"
    _write_fake_mcp_server(script)
    provider = MCPResearchProvider(server_configs=[
        MCPServerConfig(
            name="github",
            command=sys.executable,
            args=[str(script)],
        )
    ])

    result = provider.search("repo prompts for research mode", reason="explicit_research_mode")

    assert result.used is True
    assert result.provider == "mcp:github"
    assert result.sources[0].url == "https://github.com/example/open-mcp-repo"
    assert result.sources[0].source == "GitHub"


def test_research_service_falls_back_to_mcp(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_PROVIDER", "ddgs")
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_CACHE_TTL_S", 900)
    monkeypatch.setattr(cfg, "VEDA_MCP_ENABLED", True)

    script = tmp_dir / "fake_mcp_server.py"
    _write_fake_mcp_server(script)
    mcp_provider = MCPResearchProvider(server_configs=[
        MCPServerConfig(
            name="github",
            command=sys.executable,
            args=[str(script)],
        )
    ])

    class EmptyPrimaryProvider:
        def is_available(self):
            return True

        def search(self, query: str, *, reason: str):
            return ResearchResult(provider="ddgs", query=query, reason=reason, used=False, error="no_results")

    service = ResearchService(
        providers={"ddgs": EmptyPrimaryProvider()},
        mcp_provider=mcp_provider,
    )

    result = service.search("find repo examples for prompt workflows", reason="explicit_research_mode")

    assert result.used is True
    assert result.provider == "mcp:github"
    assert result.sources[0].title == "Open MCP Repo"


def test_research_service_falls_back_to_mcp_when_primary_is_unavailable(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_PROVIDER", "ddgs")
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_CACHE_TTL_S", 900)
    monkeypatch.setattr(cfg, "VEDA_MCP_ENABLED", True)

    script = tmp_dir / "fake_mcp_server.py"
    _write_fake_mcp_server(script)
    mcp_provider = MCPResearchProvider(server_configs=[
        MCPServerConfig(
            name="github",
            command=sys.executable,
            args=[str(script)],
        )
    ])

    class UnavailablePrimaryProvider:
        def is_available(self):
            return False

        def search(self, query: str, *, reason: str):
            raise AssertionError("Primary provider should not be called when unavailable.")

    service = ResearchService(
        providers={"ddgs": UnavailablePrimaryProvider()},
        mcp_provider=mcp_provider,
    )

    result = service.search("find repo examples for prompt workflows", reason="explicit_research_mode")

    assert result.used is True
    assert result.provider == "mcp:github"
    assert result.sources[0].url == "https://github.com/example/open-mcp-repo"


def test_research_service_capabilities_report_mcp_servers(monkeypatch, tmp_dir):
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_MCP_ENABLED", True)

    script = tmp_dir / "fake_mcp_server.py"
    _write_fake_mcp_server(script)
    mcp_provider = MCPResearchProvider(server_configs=[
        MCPServerConfig(
            name="github",
            command=sys.executable,
            args=[str(script)],
        )
    ])

    class FakePrimaryProvider:
        def is_available(self):
            return True

        def search(self, query: str, *, reason: str):
            return ResearchResult(
                provider="ddgs",
                query=query,
                reason=reason,
                used=True,
                sources=[ResearchSource(title="One", url="https://example.com")],
            )

    service = ResearchService(
        providers={"ddgs": FakePrimaryProvider()},
        mcp_provider=mcp_provider,
    )

    caps = service.capabilities()

    assert caps["mcp_enabled"] is True
    assert caps["mcp_server_names"] == ["github"]
