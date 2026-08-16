"""VEDA-EMP-FEATURE-003: preregister a new event-family feature study.

This activity freezes a new POSITION_END feature family and runs only the
outcome-free prevalence/legacy feasibility path.  The available source feed
has four previously exposed subjects, so no independent primary cohort is
fabricated and no predictive inference is emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POP = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json"
EVENTS = ROOT / "data/veda/research/empirical/ogdb_event_candidates.json"
OUT = ROOT / "docs/current-state/emp-feature-003"
POPULATION_HASH = "10e8debb06afa0280aa1523a7fba0c868788871d4a7736e9358584582b400863"
FEATURE_FAMILY_ID = "VEDA_EMP_FEATURE_FAMILY_POSITION_END_V1"
FEATURE_FAMILY_VERSION = "1.0.0"
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
LORDS = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def d(value: str) -> date:
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def chart(row: dict[str, Any]) -> dict[str, Any]:
    return {"lagna": row["d1"]["lagna"], "planets": row["d1"]["planets"]}


def lord_for_house(ch: dict[str, Any], house: int) -> str:
    index = SIGNS.index(ch["lagna"]["sign"])
    return LORDS[SIGNS[(index + house - 1) % 12]]


def period(row: dict[str, Any], when: date, level: str) -> str | None:
    for md in row["vimshottari"]["mahadashas"]:
        if d(md["start_utc"]) <= when < d(md["end_utc"]):
            if level == "MD":
                return md["lord"]
            for ad in md["antardashas"]:
                if d(ad["start_utc"]) <= when < d(ad["end_utc"]):
                    return ad["lord"]
    return None


def feature_value(feature_id: str, ch: dict[str, Any], md: str | None, ad: str | None) -> bool | None:
    if feature_id == "PEND-P01_MD_LORD_IS_10TH_LORD":
        return None if md is None else md == lord_for_house(ch, 10)
    if feature_id == "PEND-P02_MD_LORD_OCCUPIES_10TH":
        return None if md is None else ch["planets"].get(md, {}).get("house") == 10
    if feature_id == "PEND-P03_AD_LORD_IS_10TH_LORD":
        return None if ad is None else ad == lord_for_house(ch, 10)
    if feature_id == "PEND-S01_AD_LORD_OCCUPIES_10TH":
        return None if ad is None else ch["planets"].get(ad, {}).get("house") == 10
    if feature_id == "PEND-S02_MD_LORD_IS_8TH_LORD":
        return None if md is None else md == lord_for_house(ch, 8)
    raise KeyError(feature_id)


def value(feature_id: str, row: dict[str, Any], when: date) -> bool | None:
    return feature_value(feature_id, chart(row), period(row, when, "MD"), period(row, when, "AD"))


FEATURES = [
    ("PEND-P01_MD_LORD_IS_10TH_LORD", "Mahadasha lord equals the 10th lord", "PRIMARY"),
    ("PEND-P02_MD_LORD_OCCUPIES_10TH", "Mahadasha lord occupies the 10th house", "PRIMARY"),
    ("PEND-P03_AD_LORD_IS_10TH_LORD", "Antardasha lord equals the 10th lord", "PRIMARY"),
    ("PEND-S01_AD_LORD_OCCUPIES_10TH", "Antardasha lord occupies the 10th house", "SECONDARY"),
    ("PEND-S02_MD_LORD_IS_8TH_LORD", "Mahadasha lord equals the 8th lord", "SECONDARY"),
]


def contracts() -> list[dict[str, Any]]:
    result = []
    for feature_id, name, tier in FEATURES:
        item = {
            "feature_id": feature_id,
            "version": "1.0.0",
            "event_family": "POSITION_END",
            "tier": tier,
            "name": name,
            "source_status": "PLATFORM_SYNTHESIS",
            "source_ids": ["P016", "VEDA-KNOW-TIMING-001", "VEDA-EMP-FEATURE-003"],
            "source_lineage": "P016 period mechanics plus event-specific platform hypothesis; no classical event-end claim",
            "timing_level": "MAHADASHA_OR_ANTARDASHA_INTERVAL",
            "required_inputs": ["D1", "P016_CANONICAL_TIMING", "source-recorded event date"],
            "deterministic_contract": {
                "present": "the named period lord satisfies the stated natal relationship",
                "absent": "the named period lord does not satisfy the stated natal relationship",
                "indeterminate": "no period covers the evaluation date",
                "date_precision_rule": "use source-recorded event precision without manufactured dates",
            },
            "implementation_status": "RESEARCH_ONLY",
            "production_status": "INACTIVE",
            "empirical_status": "PENDING_RUN",
        }
        item["hash"] = digest(item)
        result.append(item)
    return result


def intervals_for(row: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    if "ANTARDASHA" not in contract["timing_level"]:
        return row["vimshottari"]["mahadashas"]
    return [ad for md in row["vimshottari"]["mahadashas"] for ad in md["antardashas"]]


def population_prevalence(cs: list[dict[str, Any]]) -> dict[str, Any]:
    rows = json.loads(POP.read_text(encoding="utf-8"))["records"]
    out = []
    for c in cs:
        values: list[bool] = []
        subject_rates: list[float] = []
        active_days = total_days = 0
        for row in rows:
            local: list[bool] = []
            levels = intervals_for(row, c)
            for interval in levels:
                start, end = d(interval["start_utc"]), d(interval["end_utc"])
                days = max((end - start).days, 0)
                md = interval["lord"] if "ANTARDASHA" not in c["timing_level"] else None
                ad = interval["lord"] if "ANTARDASHA" in c["timing_level"] else None
                val = feature_value(c["feature_id"], chart(row), md, ad)
                if val is not None:
                    values.append(val); local.append(val); total_days += days
                    if val: active_days += days
            if local: subject_rates.append(sum(local) / len(local))
        out.append({
            "feature_id": c["feature_id"],
            "subjects_analyzed": len(rows),
            "subject_activation_rate": sum(any(feature_value(c["feature_id"], chart(r), i["lord"] if "ANTARDASHA" not in c["timing_level"] else None, i["lord"] if "ANTARDASHA" in c["timing_level"] else None) for i in intervals_for(r, c)) for r in rows) / len(rows),
            "time_prevalence": active_days / total_days if total_days else None,
            "mean_interval_prevalence": sum(values) / len(values) if values else None,
            "median_subject_prevalence": sorted(subject_rates)[len(subject_rates) // 2] if subject_rates else None,
            "zero_activation_rate": (len(values) - sum(values)) / len(values) if values else None,
            "indeterminate_rate": 0.0,
            "classification": "EMPIRICALLY_TESTABLE" if values and 0 < sum(values) < len(values) else "TOO_COMMON_OR_ZERO",
            "outcome_join_performed": False,
        })
    return {"population_id": "VEDA-POP-OGDB-001", "population_hash": POPULATION_HASH, "outcome_free": True, "features": out}


def legacy_events() -> list[dict[str, Any]]:
    source = json.loads(EVENTS.read_text(encoding="utf-8"))
    return [{"subject_id": r["ogid"], "subject_label": r["subject_label"], "event_date": e["event_date_start"], "precision": e["date_precision"], "event_id": e["event_id"], "source_quality": e.get("source_quality"), "verification_source": e.get("verification_source")} for r in source["records"] for e in r.get("events", []) if e["event_class"] == "POSITION_END"]


@lru_cache(maxsize=1)
def build() -> dict[str, Any]:
    cs = contracts()
    candidates = legacy_events()
    prevalence = population_prevalence(cs)
    source_ids = sorted({x["subject_id"] for x in candidates})
    return {"programme": "VEDA-EMP-FEATURE-003", "overall_status": "COMPLETE_WITH_CONDITION", "event_family_selection": {"selected": "POSITION_END", "reason": "Highest objectivity, source provenance and control feasibility among audited candidates; new independent cohort gate remains unresolved.", "candidates": [{"candidate": "POSITION_END", "score": 8.7}, {"candidate": "RELOCATION_FOREIGN_RESIDENCE", "score": 5.2}, {"candidate": "PROPERTY_ACQUISITION", "score": 4.8}, {"candidate": "EDUCATION_COMPLETION", "score": 5.6}]}, "event_definition": "Documented date on which a subject ceased to hold a distinct professional or public position; term completion, resignation, retirement, removal and death-in-office are not conflated.", "feature_family_id": FEATURE_FAMILY_ID, "feature_family_version": FEATURE_FAMILY_VERSION, "feature_family_hash": digest(cs), "contracts": cs, "prevalence": prevalence, "legacy_secondary_cohort": {"subjects": len(source_ids), "events": len(candidates), "subject_ids": source_ids, "source_file": "data/veda/research/empirical/ogdb_event_candidates.json"}, "primary_cohort": {"eligible_subjects": 0, "target": 20, "status": "BLOCKED_INSUFFICIENT_INDEPENDENT_EVENT_COHORT", "holdout": "NOT_CREATED", "controls": "NOT_RUN", "permutations": "NOT_RUN"}, "position_start_closure": {"F001_F005": "REPLICATED_NO_ASSOCIATION_PRESERVED", "reopened": False}, "production_changed": False, "approved_core_changed": False, "rag_changed": False, "ml_used": False, "composition_used": False, "pred_m4": "INSUFFICIENT_SAMPLE", "prospective_feature_candidate": "NONE"}


def write() -> dict[str, Any]:
    result = build(); OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "01_EVENT_FAMILY_SELECTION.json").write_text(json.dumps(result["event_family_selection"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "02_FEATURE_FAMILY_REGISTRY.json").write_text(json.dumps({k: result[k] for k in ["feature_family_id", "feature_family_version", "feature_family_hash", "event_definition", "contracts"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "03_OUTCOME_FREE_PREVALENCE.json").write_text(json.dumps(result["prevalence"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "04_LEGACY_SECONDARY_COHORT.json").write_text(json.dumps(result["legacy_secondary_cohort"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "05_FINAL_MANIFEST.json").write_text(json.dumps({k: result[k] for k in ["programme", "overall_status", "event_family_selection", "feature_family_id", "feature_family_hash", "primary_cohort", "position_start_closure", "production_changed", "approved_core_changed", "rag_changed", "ml_used", "composition_used", "pred_m4", "prospective_feature_candidate"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    result = write() if args.write else build()
    print(json.dumps({"programme": result["programme"], "status": result["overall_status"], "selected": result["event_family_selection"]["selected"], "primary_subjects": result["primary_cohort"]["eligible_subjects"], "feature_family_hash": result["feature_family_hash"]}, indent=2))
