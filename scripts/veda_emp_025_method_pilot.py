"""Run the EMP-025 method-pilot governance gate before any scoring.

The pilot must not invent an event-specific Dasha signal.  This runner freezes
the primary sample and method contract, then stops deterministically when the
existing repository lacks that governed signal definition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

PRIMARY_CLASSES = {"POSITION_START", "POSITION_END", "PUBLIC_APPOINTMENT", "ELECTION_WIN"}
CORPUS_HASH = "3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_audit(enrichment: dict[str, Any], split: dict[str, Any], corpus_manifest: dict[str, Any]) -> dict[str, Any]:
    if corpus_manifest.get("corpus_hash") != CORPUS_HASH:
        raise ValueError("CORPUS_HASH_MISMATCH_STOP")
    split_by_subject = {item["subject_id"]: item["split"] for item in split.get("records", [])}
    primary = []
    for item in enrichment.get("accepted_cases", []):
        event = item["events"][0]
        if event.get("event_class") not in PRIMARY_CLASSES:
            continue
        primary.append({
            "case_id": item["case_id"],
            "subject_id": item["subject_id"],
            "split": split_by_subject.get(item["subject_id"], "UNASSIGNED"),
            "event_id": event.get("event_id"),
            "event_class": event.get("event_class"),
            "date_precision": event.get("date_precision"),
            "source_quality": event.get("source_quality"),
            "event_date_start": event.get("event_date_start"),
        })
    primary.sort(key=lambda item: item["case_id"])
    split_counts = Counter(item["split"] for item in primary)
    stable_input = {"corpus_hash": CORPUS_HASH, "primary": primary, "split": split}
    audit_id = hashlib.sha256(_canonical(stable_input).encode("utf-8")).hexdigest()
    return {
        "activity_id": "VEDA-EMP-025-METHOD-PILOT",
        "status": "COMPLETED_WITH_PRIMARY_SCORING_STOP",
        "audit_id": audit_id,
        "corpus_hash": CORPUS_HASH,
        "hash_verified": True,
        "primary_question": "Does governed Vimshottari Dasha timing discriminate verified public-role transitions from matched time-window controls?",
        "primary_method": {
            "method_id": "VEDA-DASHA-VIMSHOTTARI",
            "method_version": "P016_CANONICAL_TIMING",
            "hierarchy": ["MAHADASHA", "ANTARDASHA"],
            "pratyantardasha": "NOT_USED",
            "starting_point": "MOON_JANMA_NAKSHATRA_REMAINDER",
            "ayanamsha": "LAHIRI",
            "ephemeris": "Swiss Ephemeris via existing D1 chart runtime",
            "timezone": "Frozen case timezone and existing chart-input normalization",
            "window_rule": "NOT_ACTIVATED_PENDING_SIGNAL_GOVERNANCE",
        },
        "signal_governance": {
            "status": "FAIL",
            "result_state": "INSUFFICIENT_SIGNAL_GOVERNANCE",
            "reason": "P016 governs deterministic timing facts, but no source-governed event-specific public-role Dasha signal definition exists.",
            "primary_scoring": "STOPPED",
            "rule_invented": False,
        },
        "primary_sample": {
            "subjects": len({item["subject_id"] for item in primary}),
            "events": len(primary),
            "event_classes": dict(sorted(Counter(item["event_class"] for item in primary).items())),
            "date_precision": dict(sorted(Counter(item["date_precision"] for item in primary).items())),
            "source_quality": dict(sorted(Counter(item["source_quality"] for item in primary).items())),
            "split_counts": dict(sorted(split_counts.items())),
            "records": primary,
        },
        "controls": {
            "matched_time_window": "SPECIFICATION_FROZEN_NOT_GENERATED",
            "event_shuffled": "SPECIFICATION_FROZEN_NOT_GENERATED",
            "subject_event_permutation": "SPECIFICATION_FROZEN_NOT_GENERATED",
            "time_perturbed": "SPECIFICATION_FROZEN_NOT_GENERATED",
            "random_baseline": "SPECIFICATION_FROZEN_NOT_GENERATED",
            "dasha_output_used_for_control_generation": False,
        },
        "runs": {"design": "NOT_RUN", "validation": "NOT_RUN", "holdout": "SEALED_NOT_RUN"},
        "holdout_audit": {"protected_before_unseal": True, "outcomes_accessed": False, "unseal_event": None},
        "results": {
            "validation": None,
            "holdout": None,
            "combined": None,
            "method_result_state": "INSUFFICIENT_SIGNAL_GOVERNANCE",
            "interpretation": "No empirical separation claim is possible until a source-governed event-specific signal is validated.",
        },
        "next_activity": "TIMING_VALIDATION_SOURCE_SIGNAL",
        "production_changes": False,
        "approved_core_changes": False,
        "rag_changes": False,
        "predictive_maturity": "PRED-M3_OPERATIONAL_PLUS",
        "next_empirical_target": "VEDA-EMP-050",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("enrichment", type=Path)
    parser.add_argument("split", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build_audit(json.loads(args.enrichment.read_text(encoding="utf-8")), json.loads(args.split.read_text(encoding="utf-8")), json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "signal_governance": result["signal_governance"]["status"], "result_state": result["results"]["method_result_state"], "primary_events": result["primary_sample"]["events"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
