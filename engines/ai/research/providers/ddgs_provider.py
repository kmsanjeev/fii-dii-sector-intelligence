from __future__ import annotations

from engines.ai.research.providers.base import BaseResearchProvider
from engines.ai.research.schemas import ResearchResult, ResearchSource
from engines.common import config as cfg


class DDGSResearchProvider(BaseResearchProvider):
    name = "ddgs"

    def is_available(self) -> bool:
        try:
            import ddgs  # noqa: F401
            return True
        except ImportError:
            return False

    def search(self, query: str, *, reason: str) -> ResearchResult:
        result = ResearchResult(provider=self.name, query=query, reason=reason)
        try:
            from ddgs import DDGS
        except ImportError:
            result.error = "ddgs_not_installed"
            return result

        sources: list[ResearchSource] = []
        seen_urls: set[str] = set()

        def add_source(item: dict, *, kind: str) -> None:
            url = str(item.get("href") or item.get("url") or "").strip()
            if not url.startswith(("http://", "https://")):
                return
            if url in seen_urls:
                return
            seen_urls.add(url)
            title = str(item.get("title") or item.get("source") or url).strip()
            snippet = str(item.get("body") or item.get("snippet") or "").strip()
            if len(snippet) > cfg.VEDA_RESEARCH_MAX_SNIPPET_CHARS:
                snippet = snippet[: cfg.VEDA_RESEARCH_MAX_SNIPPET_CHARS - 3].rstrip() + "..."
            sources.append(
                ResearchSource(
                    title=title[:240],
                    url=url,
                    snippet=snippet,
                    source=str(item.get("source") or "").strip() or None,
                    published_at=str(item.get("date") or "").strip() or None,
                    kind=kind,
                )
            )

        try:
            client = DDGS(timeout=cfg.VEDA_RESEARCH_TIMEOUT_S)
            text_results = client.text(
                query,
                region=cfg.VEDA_RESEARCH_REGION,
                safesearch="moderate",
                max_results=cfg.VEDA_RESEARCH_MAX_RESULTS,
                backend="auto",
            ) or []
            for item in text_results:
                if len(sources) >= cfg.VEDA_RESEARCH_MAX_RESULTS:
                    break
                add_source(item, kind="text")

            if len(sources) < cfg.VEDA_RESEARCH_MAX_RESULTS and cfg.VEDA_RESEARCH_NEWS_RESULTS > 0:
                news_results = client.news(
                    query,
                    region=cfg.VEDA_RESEARCH_REGION,
                    safesearch="moderate",
                    max_results=cfg.VEDA_RESEARCH_NEWS_RESULTS,
                    backend="auto",
                ) or []
                for item in news_results:
                    if len(sources) >= cfg.VEDA_RESEARCH_MAX_RESULTS:
                        break
                    add_source(item, kind="news")
        except Exception as exc:
            result.error = f"ddgs_error: {exc}"
            return result

        result.sources = sources[: cfg.VEDA_RESEARCH_MAX_RESULTS]
        result.used = bool(result.sources)
        if not result.sources and not result.error:
            result.error = "no_results"
        return result
