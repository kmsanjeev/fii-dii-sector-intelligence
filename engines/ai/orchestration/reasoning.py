"""Small, reversible helpers for convergence and predictive self-critique."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .contracts import ReasoningEvidence


@dataclass(frozen=True, slots=True)
class CounterHypothesis:
    description: str
    evidence_ids: tuple[str, ...] = ()
    status: str = "HYPOTHESIS"


@dataclass(frozen=True, slots=True)
class SelfCritique:
    supports: tuple[str, ...] = ()
    oppositions: tuple[str, ...] = ()
    weak_evidence: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    alternatives: tuple[CounterHypothesis, ...] = ()
    double_counting_risk: bool = False
    confidence_adjustment: str = "UNCHANGED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def convergence_summary(evidence: Iterable[ReasoningEvidence]) -> dict[str, Any]:
    rows = list(evidence)
    families = {item.evidence_family or item.underlying_fact or item.evidence_id for item in rows}
    underlying = [item.underlying_fact for item in rows if item.underlying_fact]
    duplicate_risk = len(underlying) != len(set(underlying))
    layers = {item.layer.value for item in rows}
    return {
        "signal_count": len(rows),
        "independent_family_count": len(families),
        "layers": sorted(layers),
        "classification": "CONFLICTING_CONVERGENCE" if any(item.evidence_type.value == "CONFLICT" for item in rows) else "CROSS_LAYER_CONVERGENCE" if len(layers) > 1 else "SINGLE_SIGNAL" if len(rows) == 1 else "MULTIPLE_SUPPORTING_SIGNALS",
        "double_counting_risk": duplicate_risk,
    }


__all__ = ["CounterHypothesis", "SelfCritique", "convergence_summary"]
