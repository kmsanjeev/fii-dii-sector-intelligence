"""P026-M001 inventory of health, disease, vitality, and longevity logic."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "docs" / "current-state" / "p026" / "m001_inventory.json"
PATTERNS = {
    "health": re.compile(r"\bhealth\b|\billness\b|\bdisease\b|\bmedical\b|\bvitality\b", re.I),
    "bhava_6": re.compile(r"\b6th\s+(?:house|lord)\b|\bsixth\s+(?:house|lord)\b", re.I),
    "bhava_8": re.compile(r"\b8th\s+(?:house|lord)\b|\beighth\s+(?:house|lord)\b", re.I),
    "bhava_12": re.compile(r"\b12th\s+(?:house|lord)\b|\btwelfth\s+(?:house|lord)\b", re.I),
    "vitality": re.compile(r"\bvitality\b|\bconstitution\b|\blagnesha\b", re.I),
    "hospital": re.compile(r"\bhospital(?:ization)?\b|\bchronic\b|\bacute\b", re.I),
    "varga": re.compile(r"\bD6\b|\bD30\b|\bshashtamsha\b|\btrimsamsha\b|\btrimshamsa\b", re.I),
    "longevity": re.compile(r"\blongevity\b|\blifespan\b|\bayur\b|\barogya\b|\broga\b", re.I),
}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".vscode"}
HINTS = {
    "engines/ai/knowledge/astrology_capability_framework.py": "GOVERNED",
    "engines/ai/knowledge/varga_governance.py": "GOVERNED",
    "engines/ai/knowledge/astrology_interpretation_validation.py": "GOVERNED",
    "engines/ai/research/domains/vedic_astrology/plugin.py": "HIGH_STAKES",
    "engines/ai/chatbot/tools/kundli_interpreter.py": "LEGACY",
    "engines/ai/chatbot/tools/kundli_life_guide.py": "LEGACY",
    "engines/intelligence/kundli_engine.py": "PRODUCTION_ACTIVE",
    "engines/ai/knowledge/health_governance.py": "RESEARCH_ONLY",
    "engines/intelligence/health_evidence_aggregation.py": "SHADOW",
    "engines/intelligence/health_synthesis_engine.py": "SHADOW",
}


@dataclass(slots=True)
class HealthInventoryRecord:
    file_path: str
    classification: str
    matched_patterns: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    line_hits: list[int] = field(default_factory=list)


def _classify(path: str, content: str) -> tuple[str, list[str]]:
    if path in HINTS:
        return HINTS[path], [f"path-hint:{HINTS[path]}"]
    lower = path.lower()
    if lower.startswith("tests/"):
        return "SHADOW", ["test-surface"]
    if lower.startswith("data/veda/research/astrology"):
        return "RESEARCH_ONLY", ["research-store"]
    if lower.startswith("data/veda/validation"):
        return "SHADOW", ["validation-artifact"]
    if "p026" in lower:
        return "RESEARCH_ONLY", ["p026-artifact"]
    if "kundli_interpreter" in lower or "life_guide" in lower:
        return "LEGACY", ["legacy-interpretation"]
    if "kundli_engine" in lower:
        return "PRODUCTION_ACTIVE", ["legacy-runtime"]
    if "governance" in lower or "ontology" in lower or "rag" in lower:
        return "GOVERNED", ["governed-infrastructure"]
    if "medical" in content.lower() or "disease" in content.lower():
        return "HIGH_STAKES", ["medical-safety-surface"]
    return "HEURISTIC", ["keyword-heuristic"]


def inventory_repository(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    records: list[HealthInventoryRecord] = []
    scanned = 0
    for path in sorted(root.rglob("*")):
        if path.is_dir() or any(part in SKIP_DIRS for part in path.parts) or path.suffix.lower() not in {".py", ".json", ".md", ".ts", ".tsx", ".txt"}:
            continue
        scanned += 1
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        matches = [name for name, pattern in PATTERNS.items() if pattern.search(content)]
        if not matches:
            continue
        relative = path.relative_to(root).as_posix()
        classification, reasons = _classify(relative, content)
        hits = [i + 1 for i, line in enumerate(content.splitlines()) if any(pattern.search(line) for pattern in PATTERNS.values())]
        records.append(HealthInventoryRecord(relative, classification, matches, reasons, hits[:12]))
    counts = Counter(row.classification for row in records)
    return {"timestamp": "2026-08-14T00:00:00+05:30", "repo_root": str(root), "files_scanned": scanned, "files_with_matches": len(records), "classification_counts": dict(sorted(counts.items())), "summary": {key.lower(): counts.get(key, 0) for key in ("GOVERNED", "LEGACY", "HEURISTIC", "UNSOURCED", "RESEARCH_ONLY", "SHADOW", "PRODUCTION_ACTIVE", "DUPLICATE", "DISCONNECTED", "NOT_IMPLEMENTED", "HIGH_STAKES")}, "records": [asdict(row) for row in records], "recommendation": "REVIEW_REQUIRED"}


def write_inventory(root: Path | None = None, output_path: Path | None = None) -> Path:
    payload = inventory_repository(root)
    path = output_path or OUTPUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = ["inventory_repository", "write_inventory"]
