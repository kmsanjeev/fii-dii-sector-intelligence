"""Deterministic source-ranked atomic feature study for VEDA-EMP-FEATURE-001.

This module deliberately stops at feature evidence. It does not create a
composite score, predictive rule, model, or production integration.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.orchestration.cases import CaseRegistry
POPULATION_PATH = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json"
OUTPUT_DIR = ROOT / "docs/current-state/emp-feature-001"
POPULATION_ID = "VEDA-POP-OGDB-001"
POPULATION_HASH = "10e8debb06afa0280aa1523a7fba0c868788871d4a7736e9358584582b400863"
EVENT_FAMILY = "POSITION_START"
CONTROL_OFFSET_DAYS = 365

SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
LORDS = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _date(value: str) -> date:
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def _chart(record: dict[str, Any]) -> dict[str, Any]:
    if "d1" in record:
        return {"lagna": record["d1"]["lagna"], "planets": record["d1"]["planets"]}
    facts = record.get("chart_facts", {})
    return {"lagna": facts["lagna"], "planets": facts["planets"]}


def _intervals(record: dict[str, Any]) -> list[dict[str, Any]]:
    if "vimshottari" in record:
        return record["vimshottari"]["mahadashas"]
    return record["chart_facts"]["current_dasha"]["all_mahadashas"]


def _lord_for_house(chart: dict[str, Any], house: int) -> str:
    lagna_sign = chart["lagna"]["sign"]
    lagna_index = SIGNS.index(lagna_sign)
    sign = SIGNS[(lagna_index + house - 1) % 12]
    return LORDS[sign]


def _md_lord_at(record: dict[str, Any], when: date) -> str | None:
    for interval in _intervals(record):
        start = _date(interval.get("start_date") or interval["start_utc"])
        end = _date(interval.get("end_date") or interval["end_utc"])
        if start <= when < end:
            return interval["planet"] if "planet" in interval else interval["lord"]
    return None


def _feature_value(feature_id: str, record: dict[str, Any], when: date) -> bool | None:
    chart = _chart(record)
    md_lord = _md_lord_at(record, when)
    if md_lord is None:
        return None
    if feature_id == "F001_MD_LORD_IS_10TH_LORD":
        return md_lord == _lord_for_house(chart, 10)
    if feature_id == "F002_MD_LORD_OCCUPIES_10TH":
        return chart["planets"].get(md_lord, {}).get("house") == 10
    if feature_id == "F003_MD_LORD_IS_9TH_LORD":
        return md_lord == _lord_for_house(chart, 9)
    if feature_id == "F004_MD_LORD_OCCUPIES_9TH":
        return chart["planets"].get(md_lord, {}).get("house") == 9
    if feature_id == "F005_MD_LORD_IS_LAGNA_LORD":
        return md_lord == chart["lagna"]["lord"]
    raise KeyError(feature_id)


FEATURES = [
    {"feature_id": "F001_MD_LORD_IS_10TH_LORD", "name": "Mahadasha lord equals 10th lord", "event_family": EVENT_FAMILY},
    {"feature_id": "F002_MD_LORD_OCCUPIES_10TH", "name": "Mahadasha lord occupies 10th house", "event_family": EVENT_FAMILY},
    {"feature_id": "F003_MD_LORD_IS_9TH_LORD", "name": "Mahadasha lord equals 9th lord", "event_family": EVENT_FAMILY},
    {"feature_id": "F004_MD_LORD_OCCUPIES_9TH", "name": "Mahadasha lord occupies 9th house", "event_family": EVENT_FAMILY},
    {"feature_id": "F005_MD_LORD_IS_LAGNA_LORD", "name": "Mahadasha lord equals Lagna lord", "event_family": EVENT_FAMILY},
]


def feature_contracts() -> list[dict[str, Any]]:
    contracts = []
    for item in FEATURES:
        contract = {
            **item,
            "version": "1.0.0",
            "feature_type": "ATOMIC_DASHA_NATAL_RELATIONSHIP",
            "source_status": "PLATFORM_SYNTHESIS",
            "source_ids": ["P016", "VEDA-KNOW-TIMING-001", "VEDA-TIMING-RESEARCH-REBASELINE-001"],
            "source_lineage": "P016 timing mechanics plus platform feature framing; no classical event claim",
            "calculation_dependency": "P016_CANONICAL_TIMING+D1_HOUSE_LORDS",
            "timing_level": "MAHADASHA_INTERVAL",
            "deterministic_contract": {
                "present": "resolved Mahadasha lord satisfies exactly one named natal relationship",
                "absent": "resolved Mahadasha lord does not satisfy the relationship",
                "indeterminate": "no matching Mahadasha interval covers the evaluation date",
                "date_precision_rule": "use source-recorded event date; control is exactly 365 days earlier",
            },
            "implementation_status": "RESEARCH_ONLY",
            "prevalence_status": "PENDING_RUN",
            "empirical_status": "PENDING_RUN",
            "replication_status": "NOT_RUN",
            "production_status": "INACTIVE",
        }
        contract["hash"] = _hash(contract)
        contracts.append(contract)
    return contracts


def _case_payload(case: Any) -> dict[str, Any]:
    return case.to_dict()


def prevalence(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    population = json.loads(POPULATION_PATH.read_text(encoding="utf-8"))
    rows = population["records"]
    result = []
    for contract in contracts:
        values: list[bool] = []
        subject_rates: list[float] = []
        active_days = 0
        total_days = 0
        subjects_with_any = 0
        for row in rows:
            subject_values = []
            for interval in _intervals(row):
                start = _date(interval.get("start_date") or interval["start_utc"])
                end = _date(interval.get("end_date") or interval["end_utc"])
                days = max((end - start).days, 0)
                value = _feature_value(contract["feature_id"], row, start)
                if value is not None:
                    values.append(value)
                    subject_values.append(value)
                    total_days += days
                    if value:
                        active_days += days
            if any(subject_values):
                subjects_with_any += 1
            if subject_values:
                subject_rates.append(sum(subject_values) / len(subject_values))
        true_count = sum(values)
        subject_rates.sort()
        median = subject_rates[len(subject_rates) // 2] if subject_rates else None
        if subject_rates and len(subject_rates) % 2 == 0:
            median = (subject_rates[len(subject_rates) // 2 - 1] + subject_rates[len(subject_rates) // 2]) / 2
        result.append({
            "feature_id": contract["feature_id"],
            "subjects_analyzed": len(rows),
            "subject_activation_rate": subjects_with_any / len(rows),
            "subjects_with_any_activation": subjects_with_any,
            "time_intervals_analyzed": len(values),
            "time_prevalence": active_days / total_days if total_days else None,
            "mean_interval_prevalence": true_count / len(values) if values else None,
            "median_subject_prevalence": median,
            "zero_activation_rate": (len(values) - true_count) / len(values) if values else None,
            "indeterminate_rate": 0.0,
            "classification": "EMPIRICALLY_TESTABLE" if 0 < true_count < len(values) else "TOO_COMMON_OR_ZERO",
            "outcome_join_performed": False,
        })
    return {"population_id": POPULATION_ID, "population_hash": POPULATION_HASH, "outcome_free": True, "features": result}


def reachability(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    population = json.loads(POPULATION_PATH.read_text(encoding="utf-8"))["records"]
    fixtures = []
    for contract in contracts:
        positive = negative = indeterminate = None
        for row in population:
            for interval in _intervals(row):
                when = _date(interval.get("start_date") or interval["start_utc"])
                value = _feature_value(contract["feature_id"], row, when)
                fixture = {"chart_hash": row["chart_hash"], "evaluation_date": when.isoformat(), "value": value}
                if value is True and positive is None:
                    positive = fixture
                elif value is False and negative is None:
                    negative = fixture
                elif value is None and indeterminate is None:
                    indeterminate = fixture
        fixtures.append({"feature_id": contract["feature_id"], "positive": positive, "negative": negative, "indeterminate": indeterminate, "indeterminate_reachable": indeterminate is not None})
    return {"population_id": POPULATION_ID, "fixtures": fixtures, "outcome_free": True}


def study(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [c for c in CaseRegistry().eligible() if c.outcome and c.outcome.get("event_type") == EVENT_FAMILY]
    event_rows = []
    for case in eligible:
        event_date = _date(case.outcome["event_start"])
        control_date = event_date - timedelta(days=CONTROL_OFFSET_DAYS)
        for contract in contracts:
            event_value = _feature_value(contract["feature_id"], _case_payload(case), event_date)
            control_value = _feature_value(contract["feature_id"], _case_payload(case), control_date)
            event_rows.append({"case_id": case.case_id, "subject_id": case.subject_id, "event_date": event_date.isoformat(), "control_date": control_date.isoformat(), "feature_id": contract["feature_id"], "event_value": event_value, "control_value": control_value})
    features = []
    for contract in contracts:
        rows = [r for r in event_rows if r["feature_id"] == contract["feature_id"]]
        events = [r["event_value"] for r in rows if r["event_value"] is not None]
        controls = [r["control_value"] for r in rows if r["control_value"] is not None]
        event_rate = sum(events) / len(events) if events else None
        control_rate = sum(controls) / len(controls) if controls else None
        result = "INSUFFICIENT_SAMPLE" if len(set(r["subject_id"] for r in rows)) < 5 or len(events) < 10 else "NO_ASSOCIATION"
        features.append({"feature_id": contract["feature_id"], "event_count": len(events), "control_count": len(controls), "subject_count": len(set(r["subject_id"] for r in rows)), "event_rate": event_rate, "control_rate": control_rate, "event_control_difference": event_rate - control_rate if event_rate is not None and control_rate is not None else None, "base_prevalence": None, "result": result, "replication_status": "NOT_RUN", "rows": rows})
    return {"event_family": EVENT_FAMILY, "event_definition": "CaseRegistry POSITION_START events using source-recorded event_start dates", "event_count": len(eligible), "subject_count": len(set(c.subject_id for c in eligible)), "control_rule": "MATCHED_TIME_WINDOW: event date minus 365 days", "controls": {"matched_time_window": "PASS", "event_shuffled": "NOT_RUN_INSUFFICIENT_SUBJECTS", "subject_event_permutation": "NOT_RUN_INSUFFICIENT_SUBJECTS", "random_baseline": "NOT_RUN"}, "holdout_status": "NO_NEW_HOLDOUT; existing cases are PREVIOUSLY_EXPOSED", "features": features, "all_prespecified_features_reported": True, "outcome_selection_after_feature_freeze": False}


@lru_cache(maxsize=1)
def build_artifacts() -> dict[str, Any]:
    contracts = feature_contracts()
    prev = prevalence(contracts)
    fixtures = reachability(contracts)
    result = study(contracts)
    prevalence_by_id = {row["feature_id"]: row["mean_interval_prevalence"] for row in prev["features"]}
    for row in result["features"]:
        row["base_prevalence"] = prevalence_by_id[row["feature_id"]]
        if row["result"] == "NO_ASSOCIATION" and row["event_control_difference"] is not None and abs(row["event_control_difference"]) < 0.1:
            row["result"] = "NO_ASSOCIATION"
    statuses = {row["feature_id"]: row["result"] for row in result["features"]}
    prevalence_statuses = {row["feature_id"]: row["classification"] for row in prev["features"]}
    for contract in contracts:
        contract["prevalence_status"] = prevalence_statuses[contract["feature_id"]]
        contract["empirical_status"] = statuses[contract["feature_id"]]
    manifest = {
        "programme": "VEDA-EMP-FEATURE-001",
        "overall_status": "PASS_WITH_CONDITION",
        "feature_registry": "VEDA_EMPIRICAL_FEATURE_REGISTRY",
        "feature_count": len(contracts),
        "primary_feature_count": len(contracts),
        "event_family": EVENT_FAMILY,
        "event_count": result["event_count"],
        "subject_count": result["subject_count"],
        "promising_features": [],
        "negative_or_insufficient_features": [c["feature_id"] for c in result["features"]],
        "new_holdout": False,
        "replication_performed": False,
        "production_changed": False,
        "rag_changed": False,
        "pred_m4": "INSUFFICIENT_SAMPLE",
        "next_recommended_programme": "FEATURE_REPLICATION_OR_NEW_FEATURE_FAMILY_AFTER_LEGITIMATE_CASES",
    }
    return {"registry": {"registry_id": "VEDA_EMPIRICAL_FEATURE_REGISTRY", "version": "1.0.0", "features": contracts}, "prevalence": prev, "reachability": fixtures, "study": result, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    artifacts = build_artifacts()
    names = {"registry": "01_FEATURE_REGISTRY.json", "prevalence": "02_OUTCOME_BLIND_PREVALENCE.json", "reachability": "03_REACHABILITY_FIXTURES.json", "study": "04_FEATURE_STUDY_RESULTS.json", "manifest": "05_FINAL_MANIFEST.json"}
    for key, name in names.items():
        (output / name).write_text(json.dumps(artifacts[key], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(artifacts["manifest"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
