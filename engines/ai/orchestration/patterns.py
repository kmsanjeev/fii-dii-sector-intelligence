"""Governed expert and empirical pattern records on the shared knowledge plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ExpertReasoningPattern:
    pattern_id: str
    author: str
    source_id: str | None
    passage_reference: str = "REFERENCE_NOT_VERIFIED"
    domain: str | None = None
    factors: tuple[str, ...] = ()
    reasoning_sequence: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    exceptions: tuple[str, ...] = ()
    trust_zone: str = "RESEARCH_CANDIDATE"
    validation_state: str = "RESEARCH_REQUIRED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EmpiricalPattern:
    pattern_id: str
    dataset_source: str
    sample_size: int
    features: tuple[str, ...] = ()
    outcome: str = ""
    support_count: int = 0
    failure_count: int = 0
    calibration_state: str = "INSUFFICIENT_SAMPLE"
    version: str = "EMPIRICAL-1"
    limitations: tuple[str, ...] = ()
    trust_zone: str = "EMPIRICAL"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PatternRegistry:
    """In-process registry; persistence remains the existing shared stores."""

    def __init__(self) -> None:
        self._expert: dict[str, ExpertReasoningPattern] = {}
        self._empirical: dict[str, EmpiricalPattern] = {}

    def add_expert(self, pattern: ExpertReasoningPattern) -> ExpertReasoningPattern:
        self._expert[pattern.pattern_id] = pattern
        return pattern

    def add_empirical(self, pattern: EmpiricalPattern) -> EmpiricalPattern:
        self._empirical[pattern.pattern_id] = pattern
        return pattern

    def find(self, *, domain: str | None = None, factors: set[str] | None = None) -> list[dict[str, Any]]:
        terms = {item.lower() for item in (factors or set())}
        rows: list[dict[str, Any]] = []
        for pattern in (*self._expert.values(), *self._empirical.values()):
            if domain and getattr(pattern, "domain", None) not in {None, domain}:
                continue
            pattern_factors = {item.lower() for item in getattr(pattern, "factors", getattr(pattern, "features", ()))}
            if terms and not terms.intersection(pattern_factors):
                continue
            rows.append(pattern.to_dict())
        return rows

    def counts(self) -> dict[str, int]:
        return {"EXPERT_REASONING_PATTERN": len(self._expert), "EMPIRICAL_PATTERN": len(self._empirical)}


__all__ = ["EmpiricalPattern", "ExpertReasoningPattern", "PatternRegistry"]
