"""Run the deterministic first-ten empirical corpus sanity gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from engines.ai.orchestration.cases import CaseRegistry


def build_report(enrichment: dict[str, Any], registry: CaseRegistry) -> dict[str, Any]:
    eligible = registry.eligible()
    events = [event for item in enrichment.get("accepted_cases", []) for event in item.get("events", []) if event.get("verification_status") in {"VERIFIED_EXACT", "VERIFIED_MONTH"}]
    timezone_counts = Counter(item.get("identity", {}).get("timezone_status") for item in enrichment.get("accepted_cases", []))
    identity_counts = Counter(item.get("identity", {}).get("identity_confidence") for item in enrichment.get("accepted_cases", []))
    event_classes = Counter(event.get("event_class") for event in events)
    source_quality = Counter(event.get("source_quality") for event in events)
    checks = {
        "case_count_reached": len(eligible) >= 10,
        "all_registry_cases_valid": all(case.leakage_status == "VALID" for case in eligible),
        "event_provenance_present": all(case.event_provenance != "UNVERIFIED" for case in eligible),
        "birth_provenance_present": all(case.birth_data_provenance != "UNVERIFIED" for case in eligible),
        "no_astrology_selection": enrichment.get("astrology_used_for_selection") is False,
        "calculation_lock_present": all("chart revision lock" in case.notes.lower() for case in eligible),
    }
    return {
        "activity_id": "VEDA-EMP-010-SANITY",
        "status": "PASS_WITH_CONDITION" if all(checks.values()) else "FAIL",
        "predictive_accuracy_claim": False,
        "cases": len(eligible),
        "checks": checks,
        "case_quality": Counter(case.quality for case in eligible),
        "birth_time_precision": Counter((case.chart_input or {}).get("birth_time_precision") for case in eligible),
        "timezone": dict(timezone_counts),
        "identity_confidence": dict(identity_counts),
        "event_precision": Counter(event.get("date_precision") for event in events),
        "event_classes": dict(event_classes),
        "source_quality": dict(source_quality),
        "leakage_control": "PASS" if checks["all_registry_cases_valid"] else "FAIL",
        "calculation_reproducibility": "CONDITIONAL_CHART_FACTS_PENDING_COORDINATE_LOCK",
        "limitations": [
            "All currently accepted events are DEATH; event diversity is insufficient for method comparison.",
            "Most event claims are referenced Wikidata-only and remain lower-confidence until independent source corroboration.",
            "Chart-fact generation is pending governed latitude/longitude resolution; no coordinates are inferred from place names.",
        ],
        "excluded_subjects": enrichment.get("excluded_subjects", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("enrichment", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = build_report(json.loads(args.enrichment.read_text(encoding="utf-8")), CaseRegistry())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=dict) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "cases", "event_classes", "timezone")}, indent=2))
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
