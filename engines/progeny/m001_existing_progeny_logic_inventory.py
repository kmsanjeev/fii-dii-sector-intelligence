"""P025-M001 inventory of children, progeny, and fertility logic."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "docs" / "current-state" / "p025" / "m001_inventory.json"
PATTERNS = {
    "children": re.compile(r"\bchildren?\b", re.I),
    "progeny": re.compile(r"\bprogeny\b|\bputra\b|\bputrakaraka\b", re.I),
    "fertility": re.compile(r"\bfertility\b|\binfertility\b", re.I),
    "pregnancy": re.compile(r"\bpregnan(?:cy|t)\b|\bconception\b", re.I),
    "offspring": re.compile(r"\boffspring\b|\bchildbirth\b", re.I),
    "fifth_bhava": re.compile(r"\b5th\s+(?:house|lord)\b|\bfifth\s+(?:house|lord)\b", re.I),
    "d7": re.compile(r"\bD7\b|\bsaptamsha\b|\bsaptamsa\b", re.I),
    "family_expansion": re.compile(r"family\s+expansion|progeny\s+timing", re.I),
}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".vscode"}
HINTS = {
    "engines/ai/knowledge/varga_governance.py": "GOVERNED",
    "engines/ai/knowledge/astrology_ontology.py": "GOVERNED",
    "engines/ai/knowledge/astrology_capability_framework.py": "GOVERNED",
    "engines/ai/research/domains/vedic_astrology/plugin.py": "GOVERNED",
    "engines/ai/chatbot/tools/kundli_interpreter.py": "LEGACY",
    "engines/ai/chatbot/tools/kundli_life_guide.py": "LEGACY",
    "engines/intelligence/kundli_engine.py": "PRODUCTION_ACTIVE",
    "engines/ai/knowledge/progeny_governance.py": "RESEARCH_ONLY",
    "engines/intelligence/progeny_evidence_aggregation.py": "SHADOW",
    "engines/intelligence/progeny_synthesis_engine.py": "SHADOW",
}


@dataclass(slots=True)
class ProgenyInventoryRecord:
    file_path: str
    classification: str
    matched_patterns: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    line_hits: list[int] = field(default_factory=list)


def _classify(path: str, content: str, matches: list[str]) -> tuple[str, list[str]]:
    if path in HINTS:
        return HINTS[path], [f"path-hint:{HINTS[path]}"]
    lower = path.lower()
    if lower.startswith("tests/"):
        return "SHADOW", ["test-surface"]
    if lower.startswith("data/veda/research/astrology"):
        return "RESEARCH_ONLY", ["research-store"]
    if lower.startswith("data/veda/validation"):
        return "SHADOW", ["validation-artifact"]
    if "p025" in lower:
        return "RESEARCH_ONLY", ["p025-artifact"]
    if "kundli_interpreter" in lower or "life_guide" in lower:
        return "LEGACY", ["legacy-interpretation"]
    if "kundli_engine" in lower:
        return "PRODUCTION_ACTIVE", ["legacy-runtime"]
    if "governance" in lower or "ontology" in lower or "rag" in lower:
        return "GOVERNED", ["governed-infrastructure"]
    if "D7" in content or "fertility" in content.lower():
        return "HEURISTIC", ["keyword-heuristic"]
    return "DISCONNECTED", ["keyword-only"]


def inventory_repository(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    records: list[ProgenyInventoryRecord] = []
    files_scanned = 0
    for path in sorted(root.rglob("*")):
        if path.is_dir() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".json", ".md", ".ts", ".tsx", ".txt"}:
            continue
        files_scanned += 1
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        matches = [name for name, pattern in PATTERNS.items() if pattern.search(content)]
        if not matches:
            continue
        relative = path.relative_to(root).as_posix()
        classification, reasons = _classify(relative, content, matches)
        hits = [i + 1 for i, line in enumerate(content.splitlines()) if any(pattern.search(line) for pattern in PATTERNS.values())]
        records.append(ProgenyInventoryRecord(relative, classification, matches, reasons, hits[:12]))
    counts = Counter(item.classification for item in records)
    return {
        "timestamp": "2026-08-14T00:00:00+05:30",
        "repo_root": str(root),
        "files_scanned": files_scanned,
        "files_with_matches": len(records),
        "classification_counts": dict(sorted(counts.items())),
        "summary": {key.lower(): counts.get(key, 0) for key in ("GOVERNED", "LEGACY", "HEURISTIC", "UNSOURCED", "RESEARCH_ONLY", "SHADOW", "PRODUCTION_ACTIVE", "DUPLICATE", "DISCONNECTED", "NOT_IMPLEMENTED")},
        "records": [asdict(item) for item in records],
        "recommendation": "REVIEW_REQUIRED" if any(item.classification in {"LEGACY", "HEURISTIC", "UNSOURCED"} for item in records) else "SAFE_TO_PROCEED",
    }


def write_inventory(root: Path | None = None, output_path: Path | None = None) -> Path:
    payload = inventory_repository(root)
    path = output_path or OUTPUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = ["inventory_repository", "write_inventory"]
