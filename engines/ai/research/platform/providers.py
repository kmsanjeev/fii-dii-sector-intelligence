from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engines.ai.research.platform.contracts import EvidenceType, ResearchMissionRecord, ResearchProviderDescriptor


class ResearchProviderError(RuntimeError):
    """Base provider error used for retry/cooldown classification."""


class ResearchProviderAuthError(ResearchProviderError):
    """Provider credentials or authentication are invalid."""


class ResearchProviderTemporaryError(ResearchProviderError):
    """Transient provider/network failure."""


@dataclass(slots=True)
class ProviderEvidenceHint:
    passage: str
    claim_hint: str
    normalized_text: str
    confidence: float
    location: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderDocument:
    source_uri: str
    source_title: str
    source_type: EvidenceType
    published_at: str | None = None
    author: str | None = None
    publisher: str | None = None
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence_hints: list[ProviderEvidenceHint] = field(default_factory=list)


@dataclass(slots=True)
class ProviderSearchBatch:
    documents: list[ProviderDocument]
    continuation_hint: str | None = None
    query: str | None = None
    search_metadata: dict[str, Any] = field(default_factory=dict)


class BasePlatformResearchProvider(ABC):
    @abstractmethod
    def descriptor(self) -> ResearchProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        raise NotImplementedError

    @abstractmethod
    def retrieve(self, document: ProviderDocument) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_metadata(self, document: ProviderDocument) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def extract(self, document: ProviderDocument, *, content: str) -> list[ProviderEvidenceHint]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return self.is_available()


class SyntheticFixtureProvider(BasePlatformResearchProvider):
    def __init__(self, fixture_path: Path):
        self._fixture_path = Path(fixture_path)
        self._fixture = json.loads(self._fixture_path.read_text(encoding="utf-8"))

    def descriptor(self) -> ResearchProviderDescriptor:
        return ResearchProviderDescriptor(
            provider_id="synthetic-fixture",
            provider_type="FIXTURE",
            capabilities=["search", "retrieve", "fetch_metadata", "extract", "health_check"],
            rate_limits={"max_batches": len(self._fixture.get("batches", []))},
            cost_model={"type": "fixture", "estimated_cost": 0},
            auth_required=False,
            supports_search=True,
            supports_fetch=True,
            supports_documents=True,
            status="ACTIVE",
            allowed_uri_schemes=["fixture", "https", "http", "file"],
        )

    def is_available(self) -> bool:
        return self._fixture_path.exists()

    def search(self, mission: ResearchMissionRecord, *, prior_run_count: int) -> ProviderSearchBatch:
        sequence = mission.query_strategy.get("batch_sequence") or []
        if not sequence:
            sequence = [batch.get("batch_id") for batch in self._fixture.get("batches", [])]
        if prior_run_count >= len(sequence):
            return ProviderSearchBatch(documents=[], continuation_hint=None)

        batch_id = sequence[prior_run_count]
        batches = {batch.get("batch_id"): batch for batch in self._fixture.get("batches", [])}
        batch = batches.get(batch_id) or {}
        documents = [self._load_document(item) for item in batch.get("sources", [])]
        next_hint = sequence[prior_run_count + 1] if prior_run_count + 1 < len(sequence) else None
        return ProviderSearchBatch(
            documents=documents,
            continuation_hint=next_hint,
            query=" | ".join(sequence[: prior_run_count + 1]),
            search_metadata={
                "batch_id": batch_id,
                "sequence": sequence,
                "selected_results": [item.source_uri for item in documents],
                "result_count": len(documents),
            },
        )

    def retrieve(self, document: ProviderDocument) -> str:
        return document.content

    def fetch_metadata(self, document: ProviderDocument) -> dict[str, Any]:
        return dict(document.metadata)

    def extract(self, document: ProviderDocument, *, content: str) -> list[ProviderEvidenceHint]:
        return list(document.evidence_hints)

    def health_check(self) -> dict[str, Any]:
        return {
            "provider_id": "synthetic-fixture",
            "status": "ACTIVE" if self.is_available() else "DISABLED",
            "fixture_path": str(self._fixture_path),
        }

    def _load_document(self, item: dict[str, Any]) -> ProviderDocument:
        hints = [
            ProviderEvidenceHint(
                passage=hint["passage"],
                claim_hint=hint["claim_hint"],
                normalized_text=hint["normalized_text"],
                confidence=float(hint.get("confidence", 0.5)),
                location=hint.get("location"),
                metadata=dict(hint.get("metadata", {})),
            )
            for hint in item.get("evidence_hints", [])
        ]
        return ProviderDocument(
            source_uri=item["source_uri"],
            source_title=item["source_title"],
            source_type=EvidenceType(item.get("source_type", "WEB_REFERENCE")),
            published_at=item.get("published_at"),
            author=item.get("author"),
            publisher=item.get("publisher"),
            content=item.get("content", ""),
            metadata=dict(item.get("metadata", {})),
            evidence_hints=hints,
        )
