"""Turn governed identity candidates into source-traceable event candidates.

This module never infers an event from a missing property and never uses
astrological agreement for selection. Optional CaseRegistry ingestion is
explicit and limited to cases that satisfy the acquisition contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

# Support both ``python -m scripts...`` and direct Windows script execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.ai.orchestration.case_intake import CaseIntakeService

GOOD_IDENTITY = {"VERIFIED", "PROBABLE"}
GOOD_PRECISION = {"EXACT", "MONTH", "YEAR"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _event_is_usable(event: dict[str, Any]) -> bool:
    return (
        bool(event.get("event_id"))
        and bool(event.get("event_class"))
        and bool(event.get("event_date_start"))
        and event.get("date_precision") in GOOD_PRECISION
        and event.get("verification_status") in {"VERIFIED_EXACT", "VERIFIED_MONTH", "VERIFIED_YEAR"}
        and bool(event.get("discovery_source"))
        and bool(event.get("verification_source"))
        and bool(event.get("source_quality"))
        and event.get("public_private_status") == "PUBLIC"
    )


def _retrospective_cutoff(event_date: str) -> str:
    parsed = date.fromisoformat(event_date[:10])
    return f"{parsed.year - 1:04d}-12-31"


def enrich_candidates(payload: dict[str, Any], *, chart_revision: str, ingest: bool = False, db_path: str | None = None) -> dict[str, Any]:
    accepted: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    service = CaseIntakeService(db_path) if ingest else None
    used_case_ids = {case.case_id for case in service._existing_cases()} if service else set()
    next_case_number = 1
    for record in payload.get("records", []):
        reasons: list[str] = []
        if record.get("identity_status") not in GOOD_IDENTITY:
            reasons.append("IDENTITY_NOT_SUFFICIENTLY_RESOLVED")
        if not record.get("birth_date") or not record.get("birth_time") or not record.get("birth_place"):
            reasons.append("BIRTH_INPUT_INCOMPLETE")
        if record.get("timezone_status") not in {"RESOLVED", "BOUNDED"}:
            reasons.append("TIMEZONE_UNRESOLVED")
        events = [event for event in record.get("events", []) if _event_is_usable(event)]
        if not events:
            reasons.append("NO_VERIFIABLE_EVENTS")
        if reasons:
            excluded.append({"subject_id": record.get("ogid"), "subject_label": record.get("subject_label"), "exclusion_reasons": reasons, "record": record})
            continue

        for event_index, event in enumerate(events):
            if record.get("case_id") and event_index == 0:
                case_id = str(record["case_id"])
            else:
                while f"VEDA-EMP-CASE-{next_case_number:03d}" in used_case_ids:
                    next_case_number += 1
                case_id = f"VEDA-EMP-CASE-{next_case_number:03d}"
                next_case_number += 1
            used_case_ids.add(case_id)
            case_payload = {
                "case_external_id": case_id,
                "case_class": "HISTORICAL_VERIFIED",
                "subject_name": record.get("subject_label"),
                "subject_id": record.get("ogid"),
                "birth_date": record.get("birth_date"),
                "birth_time": record.get("birth_time"),
                "birth_time_precision": record.get("birth_time_precision", "MINUTE"),
                "birth_place": record.get("birth_place"),
                "timezone": record.get("timezone_offset"),
                "birth_data_source": "OGDB_TIMED_RECORD_PLUS_IDENTITY_VERIFICATION",
                "birth_data_quality": "DOCUMENT_VERIFIED",
                "domain": "GENERAL_TIMING",
                "event_type": event["event_class"],
                "event_start": event["event_date_start"],
                "event_end": event.get("event_date_end", ""),
                "event_time_precision": event["date_precision"],
                "event_description": event.get("notes", ""),
                "event_direction": "TRANSITION",
                "event_source": event["verification_source"],
                "event_verification_quality": "MULTI_SOURCE_VERIFIED",
                "source_type": "PUBLIC_RECORDS",
                "source_title": event["discovery_source"],
                "source_passage_reference": event.get("claim_id", "REFERENCE_NOT_VERIFIED"),
                "original_case_source": record.get("ogid"),
                "independent_verification": event["verification_source"],
                "prediction_cutoff": _retrospective_cutoff(event["event_date_start"]),
                "knowledge_cutoff": _retrospective_cutoff(event["event_date_start"]),
                "outcome_cutoff": event["event_date_start"],
                "notes": f"Acquisition-only case; chart revision lock {chart_revision}. No chart/event agreement was used for selection.",
            }
            if event_index > 0:
                # Preserve multiple objective events for one subject without
                # collapsing them into the first event's case family.
                case_payload["case_family_id"] = f"{record.get('ogid')}:{event.get('event_id')}"
            item = {"case_id": case_id, "subject_id": record.get("ogid"), "identity": record, "events": [event], "case_payload": case_payload, "eligibility_status": "EMPIRICAL_ELIGIBLE"}
            if service:
                try:
                    item["ingest_result"] = service.create_case(case_payload, actor="VEDA-EMP-EVENT-001")
                except ValueError as exc:
                    if "DUPLICATE" in str(exc):
                        item["ingest_result"] = {"status": "DUPLICATE", "reason": "Existing CaseRegistry family retained."}
                    else:
                        raise
            accepted.append(item)
    result = {
        "activity_id": "VEDA-EMP-EVENT-001",
        "created_at": _now(),
        "input_feed_id": payload.get("feed_id"),
        "records_considered": len(payload.get("records", [])),
        "identity_resolved": sum(record.get("identity_status") in GOOD_IDENTITY for record in payload.get("records", [])),
        "event_enriched_subjects": sum(bool(record.get("events")) for record in payload.get("records", [])),
        "empirical_eligible_cases": len(accepted),
        "accepted_cases": accepted,
        "excluded_subjects": excluded,
        "leakage_status": "VALID_FOR_ACQUISITION_ONLY",
        "astrology_used_for_selection": False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidates", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--chart-revision", required=True)
    parser.add_argument("--ingest", action="store_true")
    parser.add_argument("--db-path")
    args = parser.parse_args()
    result = enrich_candidates(json.loads(args.candidates.read_text(encoding="utf-8")), chart_revision=args.chart_revision, ingest=args.ingest, db_path=args.db_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("records_considered", "identity_resolved", "event_enriched_subjects", "empirical_eligible_cases")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
