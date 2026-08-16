"""Feature-blind feasibility and corpus packaging for EVIDENCE-CORPUS-001.

The script only normalizes existing public event records and provenance.  It
does not calculate charts, inspect houses/dashas/transits, score features, or
train a model.  It intentionally treats OGDB timed records as available
research inputs rather than documentary Tier A birth evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVENT_SOURCE = ROOT / "data/veda/research/empirical/ogdb_event_candidates.json"
POSEND_MANIFEST = ROOT / "docs/current-state/emp-posend-acq-001/04_FINAL_MANIFEST.json"
OUT = ROOT / "docs/current-state/evidence-corpus-001"

SCHEMA_VERSION = "VEDA-LONGITUDINAL-EVIDENCE-SCHEMA-1.0"
ELIGIBILITY_POLICY_VERSION = "VEDA-EVIDENCE-CORPUS-001-POLICY-1.0"


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def event_precision(raw: str) -> str:
    return {"EXACT": "DAY", "DAY": "DAY", "MONTH": "MONTH", "YEAR": "YEAR"}.get(raw, "NOT_AVAILABLE")


def source_tier(source_quality: str, *, birth: bool = False) -> str:
    if birth:
        # OGDB records are available timed-birth inputs, not documentary proof.
        return "C"
    if source_quality in {"PRIMARY_OFFICIAL_RECORD", "PRIMARY_OFFICIAL"}:
        return "A"
    if source_quality in {"OFFICIAL_INSTITUTIONAL_YEAR_LEVEL", "REFERENCED_WIKIDATA_PLUS_OFFICIAL_CORROBORATION", "REFERENCED_WIKIDATA_PLUS_INSTITUTIONAL_CORROBORATION", "INSTITUTIONAL_ARCHIVE"}:
        return "B"
    if source_quality:
        return "C"
    return "D"


def cluster(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.netloc or "UNKNOWN").lower()


def normalize_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for subject in payload.get("records", []):
        birth = {
            "birth_date": subject.get("birth_date"),
            "birth_time": subject.get("birth_time"),
            "birth_time_precision": subject.get("birth_time_precision", "AVAILABLE"),
            "birth_place": subject.get("birth_place"),
            "country_code": subject.get("country_code"),
            "provenance": subject.get("identity_sources", []),
            "tier": source_tier("OGDB_TIMED_RECORD_SOURCE_REVIEWED", birth=True),
            "source_cluster": "opengauquelin.org",
        }
        for event in subject.get("events", []):
            start = event.get("event_date_start")
            precision = event_precision(event.get("date_precision", ""))
            source = event.get("verification_source") or event.get("discovery_source") or ""
            rows.append({
                "subject_id": subject.get("ogid"),
                "subject": {"label": subject.get("subject_label"), "country_code": subject.get("country_code"), "profession": subject.get("occupation")},
                "birth": birth,
                "event": {
                    "event_id": event.get("event_id"),
                    "event_family": event.get("event_class"),
                    "event_subtype": event.get("event_class"),
                    "event_date_start": start,
                    "event_date_end": event.get("event_date_end", start),
                    "event_precision": precision,
                    "original_date_text": start,
                    "normalized_date": start if precision == "DAY" else None,
                    "normalization_method": "ISO_EXACT_DAY" if precision == "DAY" else "INTERVAL_PRESERVED",
                    "provenance": [source] if source else [],
                    "tier": source_tier(event.get("source_quality", "")),
                    "source_cluster": cluster(source),
                    "corroboration": event.get("verification_status", "UNVERIFIED"),
                    "conflicts": [],
                },
                "prior_veda_exposure": False,
                "eligibility": "FEASIBILITY_ONLY",
            })
    return sorted(rows, key=lambda row: (row["subject_id"] or "", row["event"]["event_id"] or ""))


def feasibility(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["event"]["event_family"]].append(row)
    output = []
    for family, items in sorted(grouped.items()):
        counts = Counter(item["event"]["event_precision"] for item in items)
        ab_birth = sum(item["birth"]["tier"] in {"A", "B"} for item in items)
        ab_event = sum(item["event"]["tier"] in {"A", "B"} for item in items)
        day_ab = sum(item["event"]["event_precision"] == "DAY" and item["event"]["tier"] in {"A", "B"} and item["birth"]["tier"] in {"A", "B"} for item in items)
        if day_ab:
            decision = "FEASIBLE_BUT_EXPENSIVE"
        elif ab_event and not ab_birth:
            decision = "INSUFFICIENT_TIMED_BIRTH_YIELD"
        elif counts["DAY"] == 0:
            decision = "INSUFFICIENT_EXACT_DAY_YIELD"
        else:
            decision = "SOURCE_QUALITY_INSUFFICIENT"
        output.append({"event_family": family, "candidates": len(items), "tier_a_birth": sum(item["birth"]["tier"] == "A" for item in items), "tier_b_birth": sum(item["birth"]["tier"] == "B" for item in items), "tier_a_b_birth": ab_birth, "tier_a_b_event": ab_event, "day": counts["DAY"], "month": counts["MONTH"], "year": counts["YEAR"], "day_tier_a_b_birth_and_event": day_ab, "decision": decision, "automation_feasibility": "BOUNDED_EXISTING_RECORDS_ONLY"})
    return output


def build() -> dict[str, Any]:
    payload = json.loads(EVENT_SOURCE.read_text(encoding="utf-8"))
    rows = normalize_records(payload)
    subject_ids = sorted({row["subject_id"] for row in rows})
    events = [{"subject_id": row["subject_id"], **row["event"]} for row in rows]
    sources = sorted({url for row in rows for url in row["event"]["provenance"]})
    schema_hash = digest({"schema_version": SCHEMA_VERSION, "fields": ["subject", "birth", "event", "prior_veda_exposure", "eligibility"]})
    policy_hash = digest({"version": ELIGIBILITY_POLICY_VERSION, "birth_tiers": ["A", "B"], "event_tiers": ["A", "B"], "confirmatory_precision": "DAY", "synthetic_dates": False})
    return {
        "programme": "VEDA-EVIDENCE-CORPUS-001", "status": "PASS_WITH_CONDITION", "mode": "FEASIBILITY_ONLY_NO_ASTROLOGY",
        "schema_version": SCHEMA_VERSION, "schema_hash": schema_hash, "eligibility_policy_hash": policy_hash,
        "subject_hash": digest(subject_ids), "event_hash": digest(events), "source_manifest_hash": digest(sources),
        "subjects": rows, "feasibility": feasibility(rows),
        "source_yield": {"candidate_subjects": len(subject_ids), "events": len(rows), "tier_a_birth": 0, "tier_b_birth": 0, "tier_a_b_birth": 0, "tier_c_birth": len(subject_ids), "day_events": sum(row["event"]["event_precision"] == "DAY" for row in rows), "month_events": sum(row["event"]["event_precision"] == "MONTH" for row in rows), "year_events": sum(row["event"]["event_precision"] == "YEAR" for row in rows)},
        "posend_legacy": {"subjects": 20, "day": 0, "month": 0, "year": 20, "confirmatory_eligible": False, "classification": "EXPLORATORY_LEGACY_FEASIBILITY", "source_manifest": str(POSEND_MANIFEST.relative_to(ROOT))},
        "india_lane": {"status": "FOUNDATION_MISSING", "tier_a_b": 0, "day": 0, "reason": "No governed India longitudinal source was acquired in this bounded feasibility activity."},
        "power": {"planner": "scripts/veda_power_planner.py", "required_effects": [0.05, 0.10, 0.15, 0.20], "alpha": 0.05, "power": 0.80, "mesi": "Must be specified per event family after yield and estimand freeze."},
        "acquisition_policy": {"stages": ["FEASIBILITY_SAMPLE", "YIELD_ESTIMATE", "POWER_TARGET", "FULL_ACQUISITION"], "synthetic_dates": False, "astrology_inspected": False, "feature_scoring": False, "ml": False, "production_changed": False, "rag_changed": False, "approved_core_changed": False, "pred_m4": "UNCHANGED"},
        "source_manifest": sources,
    }


def write() -> dict[str, Any]:
    result = build(); OUT.mkdir(parents=True, exist_ok=True)
    for name, value in [("01_CORPUS_FEASIBILITY.json", result), ("02_SOURCE_YIELD_MATRIX.json", result["feasibility"]), ("03_CORPUS_SCHEMA.json", {"schema_version": result["schema_version"], "schema_hash": result["schema_hash"], "eligibility_policy_hash": result["eligibility_policy_hash"]}), ("04_CORPUS_MANIFEST.json", {key: result[key] for key in ("programme", "status", "mode", "schema_hash", "eligibility_policy_hash", "subject_hash", "event_hash", "source_manifest_hash", "source_yield", "posend_legacy", "india_lane", "acquisition_policy")})]:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    result = write() if args.write else build()
    print(json.dumps({"programme": result["programme"], "status": result["status"], "subjects": result["source_yield"]["candidate_subjects"], "events": result["source_yield"]["events"], "day": result["source_yield"]["day_events"], "tier_a_b_birth": result["source_yield"]["tier_a_b_birth"]}, indent=2))
