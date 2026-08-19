"""Shared bounded file selection for governed repository inventories.

Domain inventories classify source and governance surfaces.  Scanning every
operational payload in the repository (NSE history, generated AI artifacts,
raw evidence, and logs) makes those audits depend on data volume rather than
the code being audited.  The canonical repository uses a bounded set of
source/governance roots; small temporary roots used by tests retain a full
recursive fallback so classification fixtures remain faithful.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


INVENTORY_SUFFIXES = frozenset({".py", ".json", ".md", ".ts", ".tsx", ".txt"})
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }
)

# These roots contain implementation, tests, governed documentation, and the
# small source/validation stores.  Large operational data and generated model
# artifacts are deliberately outside an existing-logic inventory's scope.
GOVERNED_INVENTORY_ROOTS = (
    "engines",
    "scripts",
    "tests",
    "docs/current-state",
    "docs/roadmap/veda",
    "data/veda/research/astrology",
    "data/veda/validation",
)


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def iter_inventory_files(root: Path, *, suffixes: Iterable[str] = INVENTORY_SUFFIXES):
    """Yield bounded inventory files in deterministic relative-path order.

    A real VEDA checkout is identified by its ``engines`` and ``tests`` roots
    and uses the governed scope above.  Synthetic fixture roots do not have
    that shape and use the historical recursive behavior.
    """

    suffixes = frozenset(suffixes)
    is_repository = (root / "engines").is_dir() and (root / "tests").is_dir()
    scan_roots = (
        [root / relative for relative in GOVERNED_INVENTORY_ROOTS]
        if is_repository
        else [root]
    )

    seen: set[Path] = set()
    candidates: list[Path] = []
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if path.is_dir() or _is_skipped(path):
                continue
            if path.suffix.lower() not in suffixes or path in seen:
                continue
            seen.add(path)
            candidates.append(path)

    yield from sorted(candidates, key=lambda path: path.relative_to(root).as_posix())


__all__ = ["GOVERNED_INVENTORY_ROOTS", "INVENTORY_SUFFIXES", "SKIP_DIR_NAMES", "iter_inventory_files"]
