"""Versioned experimental weighting profiles; never authoritative doctrine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class WeightProfile:
    weight_profile_id: str
    version: str
    domain: str
    evidence_basis: tuple[str, ...] = ()
    sample_size: int = 0
    changes: dict[str, Any] = field(default_factory=dict)
    previous_version: str | None = None
    state: str = "EXPERIMENTAL"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["WeightProfile"]
