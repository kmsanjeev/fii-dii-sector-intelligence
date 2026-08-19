"""P024-M001: Existing Marriage Logic Inventory.

This inventory scans the repository for marriage and relationship logic,
classifies the findings into governed, legacy, heuristic, research-only, and
shadow surfaces, and emits a canonical JSON artifact for the P024 docs bundle.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from engines.common.repository_inventory import iter_inventory_files

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = ROOT / "docs" / "current-state" / "p024" / "m001_inventory.json"

SEARCH_PATTERNS: dict[str, re.Pattern[str]] = {
    "marriage": re.compile(r"\bmarriage\b", re.IGNORECASE),
    "relationship": re.compile(r"\brelationship\b", re.IGNORECASE),
    "spouse": re.compile(r"\bspouse\b", re.IGNORECASE),
    "partner": re.compile(r"\bpartner(ship)?\b", re.IGNORECASE),
    "7th_house": re.compile(r"\b7th\s+house\b|\bseventh\s+house\b", re.IGNORECASE),
    "7th_lord": re.compile(r"\b7th\s+lord\b|\bseventh\s+lord\b", re.IGNORECASE),
    "navamsha": re.compile(r"\bnavamsha\b|\bnavamsa\b|\bD9\b", re.IGNORECASE),
    "manglik": re.compile(r"\bmanglik\b|\bkuja\s+dosha\b|\bmangal\s+dosha\b", re.IGNORECASE),
    "timing": re.compile(r"\btiming\b|\bwindow\b", re.IGNORECASE),
    "divorce_separation": re.compile(r"\bdivorce\b|\bseparation\b", re.IGNORECASE),
}

SOURCE_HINTS = {
    "engines/ai/knowledge/astrology_capability_framework.py": "GOVERNED",
    "engines/ai/knowledge/astrology_ontology.py": "GOVERNED",
    "engines/ai/knowledge/approved_core_rag.py": "GOVERNED",
    "engines/ai/knowledge/dasha_governance.py": "GOVERNED",
    "engines/ai/knowledge/varga_governance.py": "GOVERNED",
    "engines/ai/knowledge/yoga_dosha_governance.py": "GOVERNED",
    "engines/ai/knowledge/strength_governance.py": "GOVERNED",
    "engines/ai/chatbot/tools/kundli_calculator.py": "HEURISTIC",
    "engines/ai/chatbot/tools/kundli_interpreter.py": "LEGACY",
    "engines/ai/chatbot/tools/kundli_life_guide.py": "LEGACY",
    "engines/intelligence/kundli_engine.py": "PRODUCTION_ACTIVE",
    "engines/intelligence/kundli_interpretator.py": "LEGACY",
    "engines/marriage/m001_existing_marriage_logic_inventory.py": "GOVERNED",
    "engines/intelligence/marriage_evidence_aggregation.py": "SHADOW",
    "engines/intelligence/marriage_synthesis_engine.py": "SHADOW",
    "engines/ai/knowledge/marriage_governance.py": "RESEARCH_ONLY",
    "tests/test_veda_p024_marriage.py": "SHADOW",
}


@dataclass(slots=True)
class MarriageInventoryRecord:
    file_path: str
    classification: str
    matched_patterns: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    line_hits: list[int] = field(default_factory=list)


@dataclass(slots=True)
class MarriageInventory:
    timestamp: str
    repo_root: str
    files_scanned: int = 0
    files_with_matches: int = 0
    records: list[MarriageInventoryRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        summary = Counter(record.classification for record in self.records)
        pattern_counts = Counter(pattern for record in self.records for pattern in record.matched_patterns)
        return {
            "timestamp": self.timestamp,
            "repo_root": self.repo_root,
            "files_scanned": self.files_scanned,
            "files_with_matches": self.files_with_matches,
            "classification_counts": dict(sorted(summary.items())),
            "pattern_counts": dict(sorted(pattern_counts.items())),
            "records": [asdict(record) for record in self.records],
            "recommendation": "REVIEW_REQUIRED" if any(item.classification in {"LEGACY", "HEURISTIC", "UNSOURCED"} for item in self.records) else "SAFE_TO_PROCEED",
        }


def _classify_file(rel_path: str, content: str, patterns: list[str]) -> tuple[str, list[str]]:
    lowered = content.lower()
    path_lower = rel_path.lower()

    if rel_path in SOURCE_HINTS:
        return SOURCE_HINTS[rel_path], [f"path-hint:{SOURCE_HINTS[rel_path]}"]

    if "docs/current-state/p024" in path_lower:
        return "RESEARCH_ONLY", ["p024-docs"]
    if path_lower.startswith("data/veda/research/astrology"):
        return "RESEARCH_ONLY", ["research-store"]
    if path_lower.startswith("data/veda/validation"):
        return "SHADOW", ["validation-artifact"]
    if path_lower.startswith("tests/"):
        return "SHADOW", ["test-surface"]
    if path_lower.startswith("engines/marriage"):
        return "GOVERNED", ["p024-source"]
    if "kundli_engine.py" in path_lower:
        return "PRODUCTION_ACTIVE", ["legacy-runtime"]
    if "kundli_interpretator" in path_lower or "kundli_interpreter" in path_lower:
        return "LEGACY", ["legacy-interpretation"]
    if "life_guide" in path_lower or "chat_engine" in path_lower:
        return "LEGACY", ["legacy-chat"]
    if "governance" in path_lower or "ontology" in path_lower or "rag" in path_lower:
        return "GOVERNED", ["governed-infra"]
    if "placeholder" in lowered or "todo" in lowered:
        return "NOT_IMPLEMENTED", ["placeholder"]
    if any(token in patterns for token in ("manglik", "7th_house", "navamsha")):
        return "HEURISTIC", ["keyword-heuristic"]
    return "DISCONNECTED", ["keyword-only"]


def inventory_repository(root: Path | None = None) -> dict[str, Any]:
    """Scan the repository and classify marriage-related implementation surfaces."""

    root = root or ROOT
    records: list[MarriageInventoryRecord] = []
    files_scanned = 0

    for path in iter_inventory_files(root):
        files_scanned += 1
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        matched_patterns = [name for name, pattern in SEARCH_PATTERNS.items() if pattern.search(content)]
        if not matched_patterns:
            continue

        rel_path = path.relative_to(root).as_posix()
        classification, reasons = _classify_file(rel_path, content, matched_patterns)
        line_hits = [index + 1 for index, line in enumerate(content.splitlines()) if any(pattern.search(line) for pattern in SEARCH_PATTERNS.values())]
        records.append(
            MarriageInventoryRecord(
                file_path=rel_path,
                classification=classification,
                matched_patterns=matched_patterns,
                reasons=reasons,
                line_hits=line_hits[:12],
            )
        )

    files_with_matches = len(records)
    summary = Counter(record.classification for record in records)
    result = MarriageInventory(
        timestamp="2026-08-14T00:00:00+05:30",
        repo_root=str(root),
        files_scanned=files_scanned,
        files_with_matches=files_with_matches,
        records=records,
    )
    payload = result.to_dict()
    payload["summary"] = {
        "governed": summary.get("GOVERNED", 0),
        "legacy": summary.get("LEGACY", 0),
        "heuristic": summary.get("HEURISTIC", 0),
        "unsourced": summary.get("UNSOURCED", 0),
        "research_only": summary.get("RESEARCH_ONLY", 0),
        "shadow": summary.get("SHADOW", 0),
        "production_active": summary.get("PRODUCTION_ACTIVE", 0),
        "duplicate": summary.get("DUPLICATE", 0),
        "disconnected": summary.get("DISCONNECTED", 0),
        "not_implemented": summary.get("NOT_IMPLEMENTED", 0),
    }
    return payload


def write_inventory(root: Path | None = None, output_path: Path | None = None) -> Path:
    """Write the inventory JSON to the canonical P024 docs location."""

    inventory = inventory_repository(root=root)
    path = output_path or OUTPUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    payload = inventory_repository()
    path = write_inventory()
    print(json.dumps({"output_path": str(path), "summary": payload["summary"], "files_with_matches": payload["files_with_matches"]}, indent=2))


if __name__ == "__main__":
    main()
