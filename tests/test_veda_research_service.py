from __future__ import annotations

import sys
import types

from engines.ai.research.providers.ddgs_provider import DDGSResearchProvider
from engines.ai.research.service import ResearchService
from engines.common import config as cfg


def test_ddgs_provider_normalizes_text_and_news(monkeypatch):
    class FakeDDGS:
        def __init__(self, timeout=5):
            self.timeout = timeout

        def text(self, query, **kwargs):
            return [
                {
                    "title": "Text Result",
                    "href": "https://example.com/text",
                    "body": "Plain text result body",
                }
            ]

        def news(self, query, **kwargs):
            return [
                {
                    "title": "News Result",
                    "url": "https://example.com/news",
                    "body": "News result body",
                    "source": "Example News",
                    "date": "2026-08-04T10:00:00Z",
                }
            ]

    monkeypatch.setitem(sys.modules, "ddgs", types.SimpleNamespace(DDGS=FakeDDGS))

    provider = DDGSResearchProvider()
    result = provider.search("veda research mode", reason="test")

    assert result.used is True
    assert len(result.sources) == 2
    assert result.sources[0].url == "https://example.com/text"
    assert result.sources[1].source == "Example News"


def test_research_service_uses_cache(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_ENABLED", True)
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_PROVIDER", "ddgs")
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_CACHE_TTL_S", 900)

    service = ResearchService()
    calls = {"count": 0}

    class FakeProvider:
        def is_available(self):
            return True

        def search(self, query: str, *, reason: str):
            calls["count"] += 1
            from engines.ai.research.schemas import ResearchResult, ResearchSource

            return ResearchResult(
                provider="ddgs",
                query=query,
                reason=reason,
                used=True,
                sources=[ResearchSource(title="One", url="https://example.com", snippet="snippet")],
            )

    service._providers["ddgs"] = FakeProvider()

    first = service.search("what is veda", reason="explicit_research_mode")
    second = service.search("what is veda", reason="explicit_research_mode")

    assert first.used is True
    assert second.cached is True
    assert calls["count"] == 1


def test_research_service_reports_disabled(monkeypatch):
    monkeypatch.setattr(cfg, "VEDA_RESEARCH_ENABLED", False)
    service = ResearchService()
    result = service.search("unused", reason="explicit_research_mode")

    assert result.used is False
    assert result.error == "research_disabled"
