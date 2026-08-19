"""Canonical BPHS-primary Ashtakavarga V2 source table.

This module contains only the governed source-contract representation.  It is
not an interpretation or reduction engine.  Each target/contributor entry is
the set of relative sign positions (1-12) that contributes a normalized
bindu.  The table is intentionally explicit so production calculation cannot
fall back to a shared target-only vector.
"""

from __future__ import annotations

import hashlib
import json
from typing import Final

CONTRACT_ID: Final = "ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2"
CONTRACT_VERSION: Final = "2.0.0"
CONTRACT_HASH: Final = "084E19B2D61880066A503E1CED38810CA9D51962354A9520DD2E5E5946279A62"
SOURCE_MATRIX_HASH: Final = "0B7A869F3A3682A3BFFADA28E82AC23DC96EFE7E6FF3763997317C5050EE159D"

PLANETARY_TARGETS: Final = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
TARGETS: Final = PLANETARY_TARGETS + ("Lagna",)
CONTRIBUTORS: Final = TARGETS

# BPHS Ch.66 source-derived relative-position sets.  Position 1 is the
# target's own sign; position 12 is the preceding sign.  Lagna is both an
# explicit contributor and a separate target.
QUALIFYING_RELATIVE_POSITIONS: Final[dict[str, dict[str, tuple[int, ...]]]] = {
    "Sun": {
        "Sun": (1, 2, 4, 7, 8, 9, 10, 11),
        "Moon": (3, 6, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (5, 6, 9, 11),
        "Venus": (6, 7, 11, 12),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "Lagna": (3, 4, 6, 10, 11, 12),
    },
    "Moon": {
        "Sun": (3, 6, 7, 8, 10, 11),
        "Moon": (1, 3, 6, 7, 9, 10, 11),
        "Mars": (2, 3, 5, 6, 10, 11),
        "Mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "Jupiter": (1, 2, 4, 7, 8, 10, 11),
        "Venus": (3, 4, 5, 7, 9, 10, 11),
        "Saturn": (3, 5, 6, 11),
        "Lagna": (3, 6, 10, 11),
    },
    "Mars": {
        "Sun": (3, 5, 6, 10, 11),
        "Moon": (3, 6, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11),
        "Mercury": (3, 5, 6, 11),
        "Jupiter": (6, 10, 11, 12),
        "Venus": (6, 8, 11, 12),
        "Saturn": (1, 4, 7, 8, 9, 10, 11),
        "Lagna": (1, 3, 6, 10, 11),
    },
    "Mercury": {
        "Sun": (6, 9, 11, 12),
        "Moon": (2, 4, 6, 8, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (6, 8, 11, 12),
        "Venus": (1, 2, 3, 4, 5, 8, 9, 11),
        "Saturn": (1, 2, 4, 5, 7, 8, 9, 10, 11),
        "Lagna": (1, 2, 4, 6, 8, 10, 11),
    },
    "Jupiter": {
        "Sun": (1, 2, 3, 4, 7, 8, 9, 10, 11),
        "Moon": (2, 5, 7, 9, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11),
        "Mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "Jupiter": (2, 3, 7, 8, 10, 11),
        "Venus": (2, 5, 6, 9, 10, 11),
        "Saturn": (3, 5, 6, 12),
        "Lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11),
    },
    "Venus": {
        "Sun": (8, 11, 12),
        "Moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "Mars": (3, 4, 6, 9, 11, 12),
        "Mercury": (3, 5, 6, 9, 11),
        "Jupiter": (5, 8, 9, 10, 11),
        "Venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "Saturn": (3, 4, 5, 8, 9, 10, 11),
        "Lagna": (1, 2, 3, 4, 5, 8, 9, 11),
    },
    "Saturn": {
        "Sun": (1, 2, 4, 7, 8, 10, 11),
        "Moon": (3, 6, 11),
        "Mars": (3, 5, 6, 10, 11, 12),
        "Mercury": (6, 8, 9, 10, 11, 12),
        "Jupiter": (5, 6, 11, 12),
        "Venus": (6, 11, 12),
        "Saturn": (3, 5, 6, 11),
        "Lagna": (1, 3, 4, 6, 10, 11),
    },
    "Lagna": {
        "Sun": (3, 4, 6, 10, 11, 12),
        "Moon": (3, 6, 10, 11, 12),
        "Mars": (1, 3, 6, 10, 11),
        "Mercury": (1, 2, 4, 6, 8, 10, 11),
        "Jupiter": (1, 2, 4, 5, 6, 7, 9, 10, 11),
        "Venus": (1, 2, 3, 4, 5, 8, 9),
        "Saturn": (1, 3, 4, 6, 10, 11),
        "Lagna": (3, 6, 10, 11),
    },
}


def normalized_cells() -> list[dict[str, int | str]]:
    """Return the deterministic normalized 768-cell contract representation."""
    return [
        {
            "target": target,
            "contributor": contributor,
            "relative_position": position,
            "bindu": int(position in QUALIFYING_RELATIVE_POSITIONS[target][contributor]),
        }
        for target in TARGETS
        for contributor in CONTRIBUTORS
        for position in range(1, 13)
    ]


def normalized_table_hash() -> str:
    """Hash the production-normalized table, independent of source metadata."""
    payload = json.dumps(normalized_cells(), separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "CONTRACT_HASH",
    "SOURCE_MATRIX_HASH",
    "PLANETARY_TARGETS",
    "TARGETS",
    "CONTRIBUTORS",
    "QUALIFYING_RELATIVE_POSITIONS",
    "normalized_cells",
    "normalized_table_hash",
]
