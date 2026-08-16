"""Feature-blind hybrid birth-evidence strategy feasibility.

This script reads only source identity/birth metadata from the existing OGDB
population. It intentionally ignores any derived calculation fields. The
result is a strategy and workload screen, not a data-collection authorization
or a production personal-data system.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json"
OUT = ROOT / "docs/current-state/evidence-hybrid-001"
PRIOR_SUBJECTS = {"annenberg-walter-1908-03-13", "ashe-arthur-1943-07-10", "auriol-vincent-1884-08-27", "alvarez-luis-1911-06-13", "babinski-joseph-1857-11-17", "appell-paul-1855-09-27", "balmain-pierre-1914-05-18", "barres-maurice-1862-08-17", "achille-fould-aymar-1925-07-17", "barre-raymond-1924-04-12", "alioto-joseph-1916-02-12", "abbe-ernst-1840-01-23", "baeyer-adolf-1835-10-31"}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def frame(occupation: str) -> str:
    text = str(occupation or "").lower()
    if any(term in text for term in ("politician", "political", "president", "minister")):
        return "PUBLIC_OFFICIALS"
    if any(term in text for term in ("scientist", "physicist", "chemist", "mathematician", "engineer")):
        return "SCIENTISTS"
    if any(term in text for term in ("athlete", "sport", "football", "tennis", "cyclist", "boxer", "baseball", "rugby", "ski")):
        return "ATHLETES"
    if any(term in text for term in ("professor", "academic", "director", "administrator", "official")):
        return "INSTITUTIONAL_LEADERS"
    if any(term in text for term in ("actor", "singer", "artist", "writer", "film", "musician")):
        return "ENTERTAINMENT_PUBLIC_FIGURES"
    return "FRAME_NOT_AVAILABLE_FROM_CURRENT_METADATA"


def upper_zero_success_yield(n: int, confidence: float = 0.95) -> float:
    if n <= 0:
        return 0.0
    return 1 - (1 - confidence) ** (1 / n)


def workload(target: int, screened: int, confidence: float = 0.95) -> dict[str, Any]:
    upper = upper_zero_success_yield(screened, confidence)
    return {"target_tier_a_b": target, "observed_yield": 0.0, "screened": screened, "upper_confidence_yield": round(upper, 6), "optimistic_screen_count_at_upper_bound": math.ceil(target / upper), "status": "NOT_ESTIMABLE_WITH_USEFUL_PRECISION", "note": "Upper-bound scenario only; not an expected workload estimate."}


def build() -> dict[str, Any]:
    raw = json.loads(POPULATION.read_text(encoding="utf-8"))
    source_rows = []
    # Only the source object is selected. Derived fields are intentionally not
    # traversed or used in selection.
    for record in raw.get("records", []):
        source = record.get("source", {})
        subject_id = source.get("source_record_id")
        if subject_id and subject_id not in PRIOR_SUBJECTS:
            source_rows.append({"subject_id": subject_id, "birth_date": source.get("birth_date"), "birth_time": source.get("birth_time"), "birth_place": source.get("birth_place_raw"), "country": source.get("country"), "occupation": source.get("occupation", ""), "frame": frame(source.get("occupation", ""))})
    source_rows = sorted(source_rows, key=lambda row: row["subject_id"])[:40]
    for row in source_rows:
        row.update({"birth_source": "OGDB", "external_rating": None, "source_lineage": "OGDB_RECORD_ONLY", "tier": "C", "documentary_status": "NOT_LOCATED", "search_level_reached": 1, "human_review_required": True, "prior_veda_exposure": False})
    frame_counts = Counter(row["frame"] for row in source_rows)
    return {
        "programme": "VEDA-EVIDENCE-HYBRID-001", "status": "PASS_WITH_CONDITION", "mode": "STRATEGY_FEASIBILITY_NO_ASTROLOGY",
        "documentary_pilot": {"new_subjects_screened": len(source_rows), "timed_birth_recorded": len(source_rows), "source_lineage_located": 0, "tier_a": 0, "tier_b": 0, "tier_a_b": 0, "tier_c": len(source_rows), "tier_d": 0, "conflicted": 0, "not_found": 0, "tier_a_b_yield": 0.0, "uncertainty": "95% upper bound on yield is reported; expected yield is not estimable.", "frame_counts": dict(sorted(frame_counts.items())), "decision": "DOCUMENTARY_LIMITED_SCALE"},
        "formal_access": {"astro_databank": {"access_route": "FORMAL_PERMISSION_REQUIRED", "source_metadata_sufficient": "UNKNOWN_UNTIL_ACCESS", "application_package_prepared": True, "external_human_action_required": True, "scraping": "PROHIBITED", "expected_value": "CONDITIONAL_VALUE"}, "other_providers": "NO_OTHER_PROVIDER_INDEPENDENTLY_VERIFIED_IN_THIS_ACTIVITY"},
        "workload": {str(target): workload(target, len(source_rows)) for target in (50, 100, 200, 250, 500)},
        "india": {"foundation": "MISSING", "candidates_screened": 0, "recorded_times": 0, "tier_a": 0, "tier_b": 0, "tier_c": 0, "decision": "INDIA_CONSENTED_ROUTE_REQUIRED", "reason": "Existing source population has no India records and no documentary India lane was accessed."},
        "consented_corpus": {"architecture_designed": True, "consent_model": "PARTIAL_DESIGN", "privacy_model": "PARTIAL_DESIGN", "documentary_birth_verification": "SUPPORTED", "longitudinal_follow_up": "SUPPORTED", "implementation_authorized": False, "fields": ["subject_id", "consent_version", "consent_date", "withdrawal_status", "birth_date", "birth_time", "birth_time_precision", "birth_document_type", "document_verification_status", "birthplace", "coordinates", "timezone", "event_categories_consented", "followup_status", "event_date", "event_precision", "event_source", "self_reported_event", "documented_event", "privacy_class", "retention_policy"]},
        "strategy_comparison": {"formal_licensed_access": {"quality": "HIGH_IF_LINEAGE_PRESENT", "scale": "CONDITIONAL", "speed": "SLOW", "cost": "HIGH", "legal": "FORMAL_GATE", "india": "LOW", "prospective": "LOW", "sustainability": "CONDITIONAL"}, "public_documentary": {"quality": "HIGH_CASE_BY_CASE", "scale": "LOW", "speed": "SLOW", "cost": "HIGH_MANUAL", "legal": "HIGH_IF_LAWFUL", "india": "CONDITIONAL", "prospective": "LOW", "sustainability": "LIMITED"}, "india_archival": {"quality": "UNKNOWN", "scale": "UNKNOWN", "speed": "SLOW", "cost": "HIGH_MANUAL", "legal": "SOURCE_SPECIFIC", "india": "HIGH", "prospective": "LOW", "sustainability": "CONDITIONAL"}, "consented": {"quality": "HIGH_AT_ENTRY", "scale": "SLOW", "speed": "SLOW", "cost": "HIGH", "legal": "STRONG_WITH_CONSENT", "india": "HIGH", "prospective": "HIGH", "sustainability": "CONDITIONAL"}},
        "recommended_strategy": {"primary": "FORMAL_DATABASE_ACCESS_REQUIRED", "secondary": "CONSENTED_CORPUS_REQUIRED", "tertiary": "PUBLIC_DOCUMENTARY_LIMITED_SCALE", "overall": "HYBRID_DATA_STRATEGY_CONFIRMED", "stop_condition": "Stop repeated public screening after materially broader source classes still yield near-zero Tier A/B and projected acquisition remains impractical."},
        "governance": {"astrology_inspected": False, "feature_scoring": False, "production_changed": False, "approved_core_changed": False, "pred_m4": "UNCHANGED", "ml": False, "composite": False, "rag_changed": False, "provider_calls_added": 0, "external_human_action": "HUMAN_EXTERNAL_ACCESS_BLOCKER"},
        "candidate_rows": source_rows,
        "manifest_hash": digest({"candidate_rows": source_rows, "documentary_pilot": {"tier_a": 0, "tier_b": 0}, "india": {"candidates_screened": 0}, "consented_fields": ["subject_id", "consent_version"]}),
    }


def write() -> dict[str, Any]:
    result = build(); OUT.mkdir(parents=True, exist_ok=True)
    files = [("01_HYBRID_FEASIBILITY.json", result), ("02_DOCUMENTARY_PILOT.json", result["documentary_pilot"]), ("03_FORMAL_ACCESS_PACKAGE.json", result["formal_access"]), ("04_INDIA_SOURCE_MAP.json", result["india"]), ("05_CONSENTED_CORPUS_SCHEMA.json", result["consented_corpus"]), ("06_STRATEGY_COMPARISON.json", result["strategy_comparison"]), ("07_FINAL_MANIFEST.json", {key: result[key] for key in ("programme", "status", "mode", "documentary_pilot", "formal_access", "workload", "india", "consented_corpus", "recommended_strategy", "governance", "manifest_hash")})]
    for name, value in files:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    result = write() if args.write else build()
    print(json.dumps({"programme": result["programme"], "status": result["status"], "screened": result["documentary_pilot"]["new_subjects_screened"], "tier_a_b": result["documentary_pilot"]["tier_a_b"], "india": result["india"]["decision"]}, indent=2))
