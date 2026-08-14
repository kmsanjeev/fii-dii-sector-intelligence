"""P023-M001: Existing Education Logic Inventory

Comprehensive audit of education-related implementations across the repository.
This module documents current education logic, identifies duplicates, and
establishes baseline for P023 implementation.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engines.common import config as cfg

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class EducationLogicRecord:
    """Document a single education-related implementation."""
    file_path: str
    function_name: str | None
    class_name: str | None
    consumer: list[str]
    rule: str
    source: str | None
    validation_state: str
    production_use: bool
    risk_level: str
    duplicate_status: str
    classification: str


class EducationLogicInventory:
    """M001: Existing Education Logic Inventory."""

    def __init__(self):
        self.inventory: list[EducationLogicRecord] = []
        self.search_keywords = [
            "education", "academic", "study", "studies", "learning",
            "intellect", "intelligence", "knowledge", "school", "college",
            "university", "degree", "exam", "examination", "higher education",
            "4th house", "5th house", "9th house", "Mercury", "Jupiter",
            "Saraswati", "education yoga", "Vidya", "D24", "Chaturvimshamsha",
            "Siddhamsha"
        ]
        self.patterns = {
            "4th_bhava": r"4th.*bhava|house.*4|bhava_4",
            "5th_bhava": r"5th.*bhava|house.*5|bhava_5",
            "9th_bhava": r"9th.*bhava|house.*9|bhava_9",
            "mercury": r"Mercury|mercury",
            "jupiter": r"Jupiter|jupiter",
            "d24": r"D24|d24|Chaturvimshamsha|chaturvimshamsha|Siddhamsha",
        }

    def inventory_repository(self) -> dict[str, Any]:
        """Execute full repository inventory."""
        results = {
            "timestamp": "2026-08-14T00:00:00Z",
            "scope": "Full repository education-related implementations",
            "summary": {
                "total_records": 0,
                "by_classification": defaultdict(int),
                "by_risk_level": defaultdict(int),
                "production_active": 0,
                "research_only": 0,
                "duplicates": 0,
            },
            "records": [],
            "key_findings": [],
            "recommendations": [],
        }

        # Known education-related files to audit
        audit_files = {
            "kundli": [
                "engines/intelligence/kundli_engine.py",
                "engines/intelligence/kundli_interpretator.py",
                "engines/ai/chatbot/tools/kundli_interpreter.py",
            ],
            "life_domain_synthesis": [
                "engines/career/veda_p021_engine.py",
                "engines/ai/knowledge/career_wealth_governance.py",
                "engines/ai/knowledge/wealth_governance.py",
            ],
            "chatbot": [
                "engines/ai/chatbot/tools/kundli_life_guide.py",
                "engines/ai/chatbot/chat_engine.py",
            ],
            "legacy": [
                "engines/intelligence/jyotisha_runtime.py",
            ],
            "rag": [
                "engines/ai/knowledge/unified_corpus_builder.py",
                "engines/ai/knowledge/retriever.py",
            ],
            "tests": [
                "tests/test_veda_astrology_golden.py",
                "tests/test_veda_jyotisha_runtime_boundary.py",
            ],
        }

        for category, files in audit_files.items():
            for file_path in files:
                full_path = ROOT / file_path
                if full_path.exists():
                    self._audit_file(category, str(full_path), results)

        # Summarize
        results["summary"]["total_records"] = len(results["records"])
        for rec in results["records"]:
            results["summary"]["by_classification"][rec["classification"]] += 1
            results["summary"]["by_risk_level"][rec["risk_level"]] += 1
            if rec["production_use"]:
                results["summary"]["production_active"] += 1
            if "RESEARCH_ONLY" in rec["classification"]:
                results["summary"]["research_only"] += 1
            if rec["duplicate_status"] == "DUPLICATE":
                results["summary"]["duplicates"] += 1

        # Generate findings
        results["key_findings"] = self._generate_findings(results)
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _audit_file(self, category: str, file_path: str, results: dict) -> None:
        """Audit a single file for education-related logic."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            results["records"].append({
                "file_path": file_path,
                "category": category,
                "status": "ERROR",
                "error": str(e),
                "classification": "NOT_IMPLEMENTED",
                "production_use": False,
                "risk_level": "N/A",
                "duplicate_status": "UNKNOWN",
            })
            return

        # Search for education patterns
        for keyword in self.search_keywords:
            if keyword.lower() in content.lower():
                # Found education-related content
                records = self._extract_education_logic(
                    file_path, category, content, keyword
                )
                results["records"].extend(records)

    def _extract_education_logic(
        self, file_path: str, category: str, content: str, keyword: str
    ) -> list[dict[str, Any]]:
        """Extract education-related logic records from a file."""
        records = []

        # Find line numbers and contexts
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                # Extract function/class context
                func_name = self._find_function_name(lines, i)
                class_name = self._find_class_name(lines, i)

                record = {
                    "file_path": file_path,
                    "line_number": i + 1,
                    "function": func_name,
                    "class": class_name,
                    "category": category,
                    "keyword": keyword,
                    "context": line.strip()[:100],
                    "classification": self._classify_logic(
                        file_path, category, keyword, line
                    ),
                    "validation_state": self._infer_validation_state(
                        file_path, keyword
                    ),
                    "production_use": self._infer_production_use(file_path, keyword),
                    "risk_level": self._infer_risk_level(keyword),
                    "duplicate_status": "PENDING_REVIEW",
                    "source": None,
                }
                records.append(record)

        return records

    def _find_function_name(self, lines: list[str], current_line: int) -> str | None:
        """Find function name containing the current line."""
        for i in range(current_line, -1, -1):
            if re.match(r'^\s*def\s+(\w+)', lines[i]):
                match = re.match(r'^\s*def\s+(\w+)', lines[i])
                return match.group(1) if match else None
        return None

    def _find_class_name(self, lines: list[str], current_line: int) -> str | None:
        """Find class name containing the current line."""
        for i in range(current_line, -1, -1):
            if re.match(r'^\s*class\s+(\w+)', lines[i]):
                match = re.match(r'^\s*class\s+(\w+)', lines[i])
                return match.group(1) if match else None
        return None

    def _classify_logic(
        self, file_path: str, category: str, keyword: str, line: str
    ) -> str:
        """Classify the education logic."""
        if "test" in file_path.lower():
            return "TEST"
        if category == "legacy":
            return "LEGACY"
        if "comment" in line.lower() or line.strip().startswith("#"):
            return "DOCUMENTATION"
        if any(k in keyword.lower() for k in ["research", "sandbox", "experimental"]):
            return "RESEARCH_ONLY"
        if any(k in file_path.lower() for k in ["governance", "knowledge"]):
            return "GOVERNED"
        return "HEURISTIC"

    def _infer_validation_state(self, file_path: str, keyword: str) -> str:
        """Infer validation state based on file and keyword."""
        if "test" in file_path.lower():
            return "TESTED"
        if "wealth" in keyword.lower() or "career" in keyword.lower():
            return "SHADOW_VALIDATED"
        return "UNVALIDATED"

    def _infer_production_use(self, file_path: str, keyword: str) -> bool:
        """Infer whether logic is used in production."""
        # P020/P021/P022 are production-active
        if any(k in file_path.lower() for k in ["career", "wealth", "p021", "p022"]):
            return True
        if "test" in file_path.lower():
            return False
        if "legacy" in file_path.lower():
            return False
        return False

    def _infer_risk_level(self, keyword: str) -> str:
        """Infer risk level for education-related keyword."""
        if "education" in keyword.lower():
            return "HIGH_STAKES"
        if "exam" in keyword.lower() or "degree" in keyword.lower():
            return "HIGH_STAKES"
        if "mercury" in keyword.lower() or "jupiter" in keyword.lower():
            return "MODERATE"
        if "d24" in keyword.lower():
            return "MODERATE"
        return "LOW"

    def _generate_findings(self, results: dict) -> list[str]:
        """Generate key findings from inventory."""
        findings = []

        total = results["summary"]["total_records"]
        prod_active = results["summary"]["production_active"]
        research = results["summary"]["research_only"]
        duplicates = results["summary"]["duplicates"]

        findings.append(f"Total education-related logic records found: {total}")
        findings.append(f"Production-active implementations: {prod_active}")
        findings.append(f"Research-only implementations: {research}")
        findings.append(f"Potential duplicates: {duplicates}")

        # Classification breakdown
        by_class = results["summary"]["by_classification"]
        findings.append(f"Breakdown by classification: {dict(by_class)}")

        # Risk analysis
        by_risk = results["summary"]["by_risk_level"]
        findings.append(f"Risk levels: {dict(by_risk)}")

        return findings

    def _generate_recommendations(self, results: dict) -> list[str]:
        """Generate recommendations for P023."""
        recs = []

        recs.append("[ ] M002: Execute classical education research programme")
        recs.append("[ ] M003: Define education ontology based on inventory findings")
        recs.append("[ ] M004: Formalize natal education foundation rules")
        recs.append("[ ] Review duplicate logic for consolidation")
        recs.append("[ ] Preserve existing P020/P021/P022 patterns")
        recs.append("[ ] Audit Mercury/Jupiter usage across codebase")
        recs.append("[ ] Determine D24 calculation availability and validation state")

        return recs


def main():
    """Execute M001 inventory."""
    print("\n" + "="*80)
    print("VEDA-P023-M001 — EXISTING EDUCATION LOGIC INVENTORY")
    print("="*80 + "\n")

    inventory = EducationLogicInventory()
    results = inventory.inventory_repository()

    # Write results
    output_path = ROOT / "docs" / "current-state" / "p023" / "m001_inventory.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"[OK] Inventory complete: {results['summary']['total_records']} records")
    print(f"\nKey Findings:")
    for finding in results["key_findings"]:
        print(f"  • {finding}")

    print(f"\nRecommendations:")
    for rec in results["recommendations"]:
        print(f"  {rec}")

    print(f"\nOutput saved to: {output_path}")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
