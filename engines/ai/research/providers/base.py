from __future__ import annotations

from abc import ABC, abstractmethod

from engines.ai.research.schemas import ResearchResult


class BaseResearchProvider(ABC):
    name = "base"

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, *, reason: str) -> ResearchResult:
        raise NotImplementedError
