"""Freeze a deterministic, source-only EMP-025 corpus manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_manifest(enrichment: dict[str, Any], chart_snapshot: dict[str, Any], split: dict[str, Any], *, knowledge_cutoff: str, engine_revision: str) -> dict[str, Any]:
    cases = []
    for item in enrichment.get("accepted_cases", []):
        record = item["identity"]
        event = item["events"][0]
        cases.append({
            "case_id": item["case_id"],
            "subject_id": item["subject_id"],
            "birth_date": record.get("birth_date"),
            "birth_time": record.get("birth_time"),
            "birth_time_precision": record.get("birth_time_precision"),
            "birth_place": record.get("birth_place"),
            "timezone_offset": record.get("timezone_offset"),
            "event_id": event.get("event_id"),
            "event_class": event.get("event_class"),
            "event_date_start": event.get("event_date_start"),
            "date_precision": event.get("date_precision"),
            "verification_status": event.get("verification_status"),
            "source_quality": event.get("source_quality"),
            "claim_id": event.get("claim_id"),
            "verification_source": event.get("verification_source"),
        })
    cases.sort(key=lambda item: item["case_id"])
    chart_cases = sorted(item["case_id"] for item in chart_snapshot.get("charts", []) if item.get("chart_ready"))
    stable = {
        "activity_id": "VEDA-EMP-025-R3-CORPUS-FREEZE",
        "knowledge_cutoff": knowledge_cutoff,
        "chart_engine_revision": engine_revision,
        "cases": cases,
        "chart_ready_case_ids": chart_cases,
        "split": split,
        "controls": {
            "subject_level_split": True,
            "design_validation_holdout": ["DESIGN", "VALIDATION", "HOLDOUT"],
            "method_tuning_allowed": False,
            "holdout_locked": True,
            "astrology_used_for_acquisition": False,
            "bav_sav_activated": False,
        },
        "pilot_scope": {
            "status": "LAUNCHED_HANDOFF",
            "question_id": "EMP025-MP-Q01",
            "question": "Does governed Dasha timing discriminate public-role transition events from matched time-window controls?",
            "primary_methods": ["D1 chart facts", "governed Vimshottari Dasha timing"],
            "excluded_methods": ["BAV", "SAV", "holdout tuning"],
        },
    }
    digest = hashlib.sha256(_canonical(stable).encode("utf-8")).hexdigest()
    return {"corpus_hash_algorithm": "SHA256(canonical JSON; sorted keys; compact separators)", "corpus_hash": digest, **stable}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("enrichment", type=Path)
    parser.add_argument("chart_snapshot", type=Path)
    parser.add_argument("split", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--knowledge-cutoff", required=True)
    parser.add_argument("--engine-revision", required=True)
    args = parser.parse_args()
    result = build_manifest(json.loads(args.enrichment.read_text(encoding="utf-8")), json.loads(args.chart_snapshot.read_text(encoding="utf-8")), json.loads(args.split.read_text(encoding="utf-8")), knowledge_cutoff=args.knowledge_cutoff, engine_revision=args.engine_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"corpus_hash": result["corpus_hash"], "cases": len(result["cases"]), "chart_ready": len(result["chart_ready_case_ids"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
