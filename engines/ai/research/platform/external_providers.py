from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from html import unescape
from typing import Any

import requests
from bs4 import BeautifulSoup

from engines.ai.research.platform.contracts import EvidenceType, ProviderStatus, ResearchMissionRecord, ResearchProviderDescriptor, ProviderType
from engines.ai.research.platform.providers import (
    BasePlatformResearchProvider,
    ProviderDocument,
    ProviderEvidenceHint,
    ProviderSearchBatch,
    ResearchProviderAuthError,
    ResearchProviderTemporaryError,
)
from engines.ai.research.platform.security import is_safe_uri, sanitize_external_text
from engines.common import config as cfg


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _mission_queries(mission: ResearchMissionRecord) -> list[str]:
    strategy = mission.query_strategy or {}
    values = strategy.get("queries") or []
    if isinstance(values, str):
        values = [values]
    cleaned = [str(item).strip() for item in values if str(item).strip()]
    if cleaned:
        return cleaned[: mission.research_budget.max_queries]
    fallback = " ".join(part for part in [mission.title, mission.objective] if part).strip()
    return [fallback[: cfg.VEDA_RESEARCH_MAX_QUERY_CHARS]] if fallback else []


class DDGSPlatformSearchProvider(BasePlatformResearchProvider):
    def descriptor(self) -> ResearchProviderDescriptor:
        enabled = bool(cfg.VEDA_RESEARCH_EXTERNAL_ENABLED and cfg.VEDA_RESEARCH_EXTERNAL_SEARCH_ENABLED)
        return ResearchProviderDescriptor(
            provider_id="ddgs-search",
            provider_type=ProviderType.WEB_SEARCH,
            capabilities=["search", "health_check"],
            rate_limits={"max_results": cfg.VEDA_RESEARCH_MAX_RESULTS},
            cost_model={"type": "unauthenticated_search", "estimated_cost": 0},
            auth_required=False,
            supports_search=True,
            supports_fetch=False,
            supports_documents=True,
            status=ProviderStatus.HEALTHY if enabled else ProviderStatus.DISABLED,
            allowed_uri_schemes=["https", "http"],
        )

    def is_available(self) -> bool:
        if not (cfg.VEDA_RESEARCH_EXTERNAL_ENABLED and cfg.VEDA_RESEARCH_EXTERNAL_SEARCH_ENABLED):
            return False
        try:
            import ddgs  # noqa: F401
            return True
        except ImportError:
            return False

    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        if not self.is_available():
            raise ResearchProviderTemporaryError("ddgs_search_disabled")
        try:
            from ddgs import DDGS
        except ImportError as exc:
            raise ResearchProviderTemporaryError("ddgs_not_installed") from exc

        queries = _mission_queries(mission)
        if not queries:
            return ProviderSearchBatch(documents=[], continuation_hint=None, query=None, search_metadata={"result_count": 0})

        query = queries[min(prior_run_count, len(queries) - 1)]
        try:
            client = DDGS(timeout=cfg.VEDA_RESEARCH_TIMEOUT_S)
            text_results = client.text(
                query,
                region=cfg.VEDA_RESEARCH_REGION,
                safesearch="moderate",
                max_results=cfg.VEDA_RESEARCH_MAX_RESULTS,
                backend="auto",
            ) or []
        except Exception as exc:
            raise ResearchProviderTemporaryError(f"ddgs_search_failed:{exc}") from exc

        documents: list[ProviderDocument] = []
        seen: set[str] = set()
        for item in text_results:
            url = str(item.get("href") or item.get("url") or "").strip()
            if not url or url in seen:
                continue
            safe, _ = is_safe_uri(url, allowed_schemes={"http", "https"})
            if not safe:
                continue
            seen.add(url)
            title = str(item.get("title") or item.get("source") or url).strip()[:240]
            snippet = str(item.get("body") or item.get("snippet") or "").strip()
            documents.append(
                ProviderDocument(
                    source_uri=url,
                    source_title=title,
                    source_type=EvidenceType.WEB_REFERENCE,
                    published_at=str(item.get("date") or "").strip() or None,
                    author=None,
                    publisher=str(item.get("source") or "").strip() or None,
                    content="",
                    metadata={
                        "snippet": snippet[: cfg.VEDA_RESEARCH_MAX_SNIPPET_CHARS],
                        "authority_score": 0.35,
                        "discovery_only": True,
                        "source_class": "FOLKLORE_OR_UNVERIFIED",
                        "verification_status": "UNVERIFIED",
                        "discovery_provider": "ddgs",
                        "search_query": query,
                        "retrieved_at": _utc_now(),
                    },
                    evidence_hints=[],
                )
            )

        continuation_hint = queries[prior_run_count + 1] if prior_run_count + 1 < len(queries) else None
        return ProviderSearchBatch(
            documents=documents,
            continuation_hint=continuation_hint,
            query=query,
            search_metadata={
                "provider": "ddgs-search",
                "result_count": len(documents),
                "selected_results": [item.source_uri for item in documents],
            },
        )

    def retrieve(self, document: ProviderDocument) -> str:
        return document.content

    def fetch_metadata(self, document: ProviderDocument) -> dict[str, Any]:
        return dict(document.metadata)

    def extract(self, document: ProviderDocument, *, content: str) -> list[ProviderEvidenceHint]:
        snippet = str(document.metadata.get("snippet") or "").strip()
        if not snippet:
            return []
        return [
            ProviderEvidenceHint(
                passage=snippet,
                claim_hint=document.source_title,
                normalized_text=sanitize_external_text(snippet.lower()),
                confidence=0.35,
                location=document.source_uri,
                metadata={
                    "title": document.source_title,
                    "discovery_only": True,
                    "source_class": "FOLKLORE_OR_UNVERIFIED",
                    "verification_status": "UNVERIFIED",
                },
            )
        ]

    def health_check(self) -> dict[str, Any]:
        return {
            "provider_id": "ddgs-search",
            "status": self.descriptor().status.value if hasattr(self.descriptor().status, "value") else str(self.descriptor().status),
            "external": True,
            "available": self.is_available(),
        }


class RequestsDirectRetrievalProvider(BasePlatformResearchProvider):
    def descriptor(self) -> ResearchProviderDescriptor:
        enabled = bool(cfg.VEDA_RESEARCH_EXTERNAL_ENABLED and cfg.VEDA_RESEARCH_EXTERNAL_RETRIEVAL_ENABLED)
        return ResearchProviderDescriptor(
            provider_id="requests-fetch",
            provider_type=ProviderType.DIRECT_WEB,
            capabilities=["retrieve", "fetch_metadata", "extract", "health_check"],
            rate_limits={
                "timeout_seconds": cfg.VEDA_RESEARCH_FETCH_TIMEOUT_S,
                "max_bytes": cfg.VEDA_RESEARCH_FETCH_MAX_BYTES,
                "max_redirects": cfg.VEDA_RESEARCH_FETCH_MAX_REDIRECTS,
            },
            cost_model={"type": "http_fetch", "estimated_cost": 0},
            auth_required=False,
            supports_search=False,
            supports_fetch=True,
            supports_documents=True,
            status=ProviderStatus.HEALTHY if enabled else ProviderStatus.DISABLED,
            allowed_uri_schemes=["https", "http"],
        )

    def is_available(self) -> bool:
        return bool(cfg.VEDA_RESEARCH_EXTERNAL_ENABLED and cfg.VEDA_RESEARCH_EXTERNAL_RETRIEVAL_ENABLED)

    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        raise ResearchProviderTemporaryError("requests_fetch_does_not_support_search")

    def retrieve(self, document: ProviderDocument) -> str:
        if not self.is_available():
            raise ResearchProviderTemporaryError("requests_fetch_disabled")
        safe, unsafe_reason = is_safe_uri(document.source_uri, allowed_schemes={"http", "https"})
        if not safe:
            raise ResearchProviderTemporaryError(unsafe_reason or "unsafe_uri")
        session = requests.Session()
        session.max_redirects = cfg.VEDA_RESEARCH_FETCH_MAX_REDIRECTS
        try:
            response = session.get(
                document.source_uri,
                timeout=cfg.VEDA_RESEARCH_FETCH_TIMEOUT_S,
                allow_redirects=True,
                headers={"User-Agent": "VEDA-Research/2026-08-11"},
            )
        except requests.TooManyRedirects as exc:
            raise ResearchProviderTemporaryError("redirect_limit_exceeded") from exc
        except requests.RequestException as exc:
            raise ResearchProviderTemporaryError(f"http_fetch_failed:{exc}") from exc
        if response.status_code in {401, 403}:
            raise ResearchProviderAuthError(f"http_auth_failed:{response.status_code}")
        if response.status_code >= 500:
            raise ResearchProviderTemporaryError(f"http_server_error:{response.status_code}")
        if response.status_code >= 400:
            raise ResearchProviderTemporaryError(f"http_client_error:{response.status_code}")

        body = response.content[: cfg.VEDA_RESEARCH_FETCH_MAX_BYTES + 1]
        if len(body) > cfg.VEDA_RESEARCH_FETCH_MAX_BYTES:
            raise ResearchProviderTemporaryError("response_too_large")
        content_type = str(response.headers.get("content-type") or "").lower()
        text = self._extract_text(body, content_type)
        text = text[: cfg.VEDA_RESEARCH_FETCH_MAX_TEXT_CHARS]
        return text

    def fetch_metadata(self, document: ProviderDocument) -> dict[str, Any]:
        return dict(document.metadata)

    def extract(self, document: ProviderDocument, *, content: str) -> list[ProviderEvidenceHint]:
        text = sanitize_external_text(content or "")
        snippet = text[: cfg.VEDA_RESEARCH_MAX_SNIPPET_CHARS]
        if not snippet:
            snippet = sanitize_external_text(str(document.metadata.get("snippet") or ""))
        if not snippet:
            return []
        return [
            ProviderEvidenceHint(
                passage=snippet,
                claim_hint=document.source_title,
                normalized_text=sanitize_external_text(document.source_title.lower()),
                confidence=0.45,
                location=document.source_uri,
                metadata={
                    "title": document.source_title,
                    "discovery_only": True,
                    "source_class": "FOLKLORE_OR_UNVERIFIED",
                    "verification_status": "REFERENCE_NOT_VERIFIED",
                    "search_query": document.metadata.get("search_query"),
                },
            )
        ]

    def health_check(self) -> dict[str, Any]:
        return {
            "provider_id": "requests-fetch",
            "status": self.descriptor().status.value if hasattr(self.descriptor().status, "value") else str(self.descriptor().status),
            "external": True,
            "available": self.is_available(),
        }

    def _extract_text(self, body: bytes, content_type: str) -> str:
        if "html" in content_type or not content_type:
            return self._extract_html_text(body.decode("utf-8", errors="ignore"))
        return body.decode("utf-8", errors="ignore")

    def _extract_html_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for node in soup(["script", "style", "noscript"]):
            node.decompose()
        lines = [unescape(line.strip()) for line in soup.get_text("\n").splitlines()]
        return "\n".join(line for line in lines if line)

