"""Feature-blind documentary timed-birth source-yield pilot.

This module audits source metadata for existing exact-day event subjects. It
does not calculate charts or evaluate any astrological input. Birth-source
quality is intentionally conservative: an OGDB time plus identity references
is retained as Tier C until a documentary source chain for the time itself is
verified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/veda/research/empirical/ogdb_event_candidates.json"
OUT = ROOT / "docs/current-state/evidence-birth-001"


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def host(value: str) -> str:
    return (urlparse(value).netloc or "UNKNOWN").lower()


def time_precision(raw: str | None) -> str:
    return {"MINUTE": "EXACT_MINUTE", "HOUR": "HOUR_ONLY", "DAY": "UNKNOWN"}.get(str(raw or "").upper(), "UNKNOWN")


def queue_state(identity_sources: list[str]) -> str:
    return "PENDING_REVIEW" if identity_sources else "DISCOVERED"


def build() -> dict[str, Any]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = []
    for subject in payload.get("records", []):
        exact_events = [event for event in subject.get("events", []) if event.get("date_precision") == "EXACT" and event.get("event_class") in {"DEATH", "PUBLIC_APPOINTMENT", "PUBLIC_OFFICE_START", "POSITION_END"}]
        for event in exact_events:
            birth_sources = list(subject.get("identity_sources", []))
            event_source = event.get("verification_source") or event.get("discovery_source") or ""
            rows.append({
                "subject_id": subject.get("ogid"),
                "subject_label": subject.get("subject_label"),
                "event_frame": event.get("event_class"),
                "birth": {
                    "date": subject.get("birth_date"),
                    "time": subject.get("birth_time"),
                    "time_precision": time_precision(subject.get("birth_time_precision")),
                    "time_qualifier": "NOT_RECORDED_IN_CURRENT_FEED",
                    "place": subject.get("birth_place"),
                    "original_source": "OGDB",
                    "external_rating": None,
                    "veda_tier": "C",
                    "documentary_status": "NOT_VERIFIED",
                    "source_urls": birth_sources,
                    "upstream_source_cluster": "OGDB_FEED_SHARED_CLUSTER",
                },
                "event": {
                    "event_id": event.get("event_id"),
                    "date": event.get("event_date_start"),
                    "precision": "DAY",
                    "source_url": event_source,
                    "source_tier": "A" if event.get("source_quality") in {"PRIMARY_OFFICIAL_RECORD", "PRIMARY_OFFICIAL"} else "B" if "INSTITUTIONAL" in str(event.get("source_quality")) or "OFFICIAL_CORROBORATION" in str(event.get("source_quality")) else "C",
                },
                "identity_match": subject.get("identity_status", "UNKNOWN"),
                "birth_source_lineage": "PARTIAL_IDENTITY_CHAIN_ONLY" if birth_sources else "NOT_FOUND",
                "source_clusters": sorted({host(url) for url in birth_sources + ([event_source] if event_source else [])}),
                "verification_queue": queue_state(birth_sources),
                "human_review": True,
                "upgrade": "NOT_ATTEMPTED_IN_BOUNDED_METADATA_PILOT",
                "prior_veda_exposure": False,
            })
    rows.sort(key=lambda row: (row["subject_id"] or "", row["event"]["event_id"] or ""))
    subject_count = len({row["subject_id"] for row in rows})
    source_counts = Counter({"C": subject_count})
    frame_counts = Counter(row["event_frame"] for row in rows)
    precision_counts = Counter(row["birth"]["time_precision"] for row in rows)
    return {
        "programme": "VEDA-EVIDENCE-BIRTH-001",
        "status": "PASS_WITH_CONDITION",
        "mode": "DOCUMENTARY_SOURCE_YIELD_METADATA_PILOT_NO_ASTROLOGY",
        "subjects_screened": len({row["subject_id"] for row in rows}),
        "exact_day_event_subjects": len(rows),
        "frame_counts": dict(sorted(frame_counts.items())),
        "birth_yield": {"timed_births": subject_count, "tier_a": 0, "tier_b": 0, "tier_a_b": 0, "tier_c": source_counts["C"], "tier_d": 0, "conflicted": 0, "timed_birth_yield": 1.0, "tier_a_b_yield": 0.0},
        "birth_time_precision": dict(sorted(precision_counts.items())),
        "precision_qualifier_status": "UNRESOLVED_FOR_ALL_CURRENT_RECORDS",
        "source_lanes": {
            "ASTRO_DATABANK": {"status": "FORMAL_PERMISSION_REQUIRED", "checked": 0, "tier_a_b": 0, "automation": "DO_NOT_SCRAPE"},
            "OGDB": {"status": "AVAILABLE_RESEARCH_INPUT_NOT_DOCUMENTARY_TIME_PROOF", "checked": subject_count, "timed": subject_count, "source_lineage_resolved": 0, "tier_a_b": 0, "tier_c": subject_count, "automation": "LIMITED_SCALE"},
            "PUBLIC_DOCUMENTARY_ARCHIVES": {"status": "NOT_ATTEMPTED_BEYOND_EXISTING_REFERENCES", "checked": 0, "tier_a_b": 0, "automation": "SCALABLE_WITH_MANUAL_ADJUDICATION"},
            "PUBLISHED_BIOGRAPHIES": {"status": "NOT_ATTEMPTED_FOR_BIRTH_TIME", "checked": 0, "tier_a_b": 0, "automation": "CASE_BY_CASE_ONLY"},
            "INSTITUTIONAL_ARCHIVES": {"status": "NOT_ATTEMPTED_FOR_BIRTH_TIME", "checked": 0, "tier_a_b": 0, "automation": "CASE_BY_CASE_ONLY"},
            "INDIA": {"status": "FOUNDATION_MISSING", "checked": 0, "tier_a_b": 0, "automation": "LIMITED_SCALE"},
            "CONSENTED_PARTICIPANTS": {"status": "DESIGN_ONLY", "checked": 0, "tier_a_b": 0, "automation": "SCALABLE_WITH_MANUAL_ADJUDICATION"},
        },
        "scale_estimates": {str(target): {"candidates_required": None, "reason": "Observed Tier A/B yield is zero; no finite estimate is justified."} for target in (50, 100, 200, 500)},
        "rows": rows,
        "governance": {"astrology_inspected": False, "feature_scoring": False, "death_use": "RETROSPECTIVE_DATA_SOURCE_FEASIBILITY_ONLY", "production_changed": False, "approved_core_changed": False, "pred_m4": "UNCHANGED", "ml": False, "rag_changed": False},
        "source_rating_mapping": {"external_rating": "UNRESOLVED_WHEN_NOT_PRESENT", "veda_tier": "C_FOR_OGDB_TIMED_INPUT_UNTIL_DOCUMENTARY_TIME_CHAIN_VERIFIED"},
        "manifest_hash": digest({"rows": rows, "birth_yield": {"tier_a": 0, "tier_b": 0}, "governance": {"astrology_inspected": False}}),
    }


def write() -> dict[str, Any]:
    result = build(); OUT.mkdir(parents=True, exist_ok=True)
    for name, value in [("01_BIRTH_SOURCE_YIELD.json", result), ("02_VERIFICATION_QUEUE.json", result["rows"]), ("03_SOURCE_LANE_MATRIX.json", result["source_lanes"]), ("04_FINAL_MANIFEST.json", {key: result[key] for key in ("programme", "status", "mode", "subjects_screened", "exact_day_event_subjects", "frame_counts", "birth_yield", "birth_time_precision", "precision_qualifier_status", "scale_estimates", "governance", "manifest_hash")})]:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    result = write() if args.write else build()
    print(json.dumps({"programme": result["programme"], "status": result["status"], "subjects": result["subjects_screened"], "tier_a_b": result["birth_yield"]["tier_a_b"]}, indent=2))
