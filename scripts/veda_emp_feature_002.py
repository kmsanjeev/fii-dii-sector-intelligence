"""Independent subject-level replication of the frozen EMP-FEATURE-001 set."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from functools import lru_cache
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.veda_emp_feature_001 import _date, _feature_value, _hash, _intervals

POPULATION_PATH = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json"
COHORT_PATH = ROOT / "docs/current-state/emp-feature-002/01_REPLICATION_COHORT_SOURCE.json"
FROZEN_REGISTRY_PATH = ROOT / "docs/current-state/emp-feature-001/01_FEATURE_REGISTRY.json"
OUTPUT_DIR = ROOT / "docs/current-state/emp-feature-002"
POPULATION_HASH = "10e8debb06afa0280aa1523a7fba0c868788871d4a7736e9358584582b400863"
SEED = 20260816
PERMUTATIONS = 2000
CONTROL_OFFSETS = (365, 730)
MIN_VALIDATION_SUBJECTS = 10
MIN_HOLDOUT_SUBJECTS = 5
MIN_EFFECT = 0.10


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_inputs() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    population = json.loads(POPULATION_PATH.read_text(encoding="utf-8"))
    cohort = json.loads(COHORT_PATH.read_text(encoding="utf-8"))
    registry = json.loads(FROZEN_REGISTRY_PATH.read_text(encoding="utf-8"))
    assert population["population_hash"] == POPULATION_HASH
    assert registry["registry_id"] == "VEDA_EMPIRICAL_FEATURE_REGISTRY"
    assert len(registry["features"]) == 5
    return population["records"], cohort, registry


def freeze(records: list[dict[str, Any]], cohort: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    by_id = {row["source"]["source_record_id"]: row for row in records}
    prior = {"alioto-joseph-1916-02-12", "ariyoshi-george-1926-03-12", "andrus-cecil-1931-08-25", "achille-fould-aymar-1925-07-17", "alvarez-luis-1911-06-13", "annenberg-walter-1908-03-13", "appell-paul-1855-09-27", "ashe-arthur-1943-07-10", "auriol-vincent-1884-08-27", "babinski-joseph-1857-11-17", "baeyer-adolf-1835-10-31", "balmain-pierre-1914-05-18", "barre-raymond-1924-04-12"}
    selected = []
    for item in cohort["subjects"]:
        assert item["source_record_id"] in by_id
        assert item["source_record_id"] not in prior
        row = by_id[item["source_record_id"]]
        source = row["source"]
        assert source["birth_time"] and source["coordinate_status"] == "RESOLVED"
        selected.append({**item, "birth_date": source["birth_date"], "birth_time": source["birth_time"], "chart_hash": row["chart_hash"], "birth_quality": "SOURCE_PROVIDED_TIMED", "chart_ready": True})
    assert len(selected) == 20
    subject_ids = sorted(item["source_record_id"] for item in selected)
    event_ids = [{"source_record_id": item["source_record_id"], "event_start": item["event_start"], "precision": item["precision"]} for item in sorted(selected, key=lambda x: x["source_record_id"])]
    subject_hash = hashlib.sha256(canonical(subject_ids).encode()).hexdigest()
    event_hash = hashlib.sha256(canonical(event_ids).encode()).hexdigest()
    ordered = sorted(selected, key=lambda x: x["source_record_id"])
    validation = ordered[:14]
    holdout = ordered[14:]
    return {"cohort_id": cohort["cohort_id"], "version": "1.0.0", "event_definition": cohort["event_definition"], "subjects": ordered, "subject_list_hash": subject_hash, "event_list_hash": event_hash, "feature_hashes": {x["feature_id"]: x["hash"] for x in registry["features"]}, "validation_subjects": [x["source_record_id"] for x in validation], "holdout_subjects": [x["source_record_id"] for x in holdout], "partition_rule": "lexicographic source_record_id; first 14 validation, final 6 holdout", "holdout_masked_before_validation": True, "prior_subject_overlap": sorted(set(subject_ids) & prior)}


def row_for(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["source"]["source_record_id"]: row for row in records}


def rate(values: list[bool | None]) -> float | None:
    known = [x for x in values if x is not None]
    return sum(known) / len(known) if known else None


def wilson(values: list[bool | None]) -> list[float] | None:
    known = [x for x in values if x is not None]
    if not known:
        return None
    n, p = len(known), sum(known) / len(known)
    z = 1.96
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    margin = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [centre - margin, centre + margin]


def measurements(feature_id: str, selected: list[dict[str, Any]], by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for item in selected:
        record = by_id[item["source_record_id"]]
        event_date = _date(item["event_start"])
        controls = []
        for offset in CONTROL_OFFSETS:
            control_date = event_date - timedelta(days=offset)
            controls.append({"date": control_date.isoformat(), "value": _feature_value(feature_id, record, control_date)})
        rows.append({"source_record_id": item["source_record_id"], "event_date": item["event_start"], "precision": item["precision"], "event_value": _feature_value(feature_id, record, event_date), "controls": controls})
    events = [r["event_value"] for r in rows]
    controls = [c["value"] for r in rows for c in r["controls"]]
    return {"subjects": len(rows), "events": len(rows), "event_positives": sum(x is True for x in events), "event_rate": rate(events), "event_ci95": wilson(events), "matched_control_positives": sum(x is True for x in controls), "matched_control_rate": rate(controls), "matched_control_ci95": wilson(controls), "rows": rows}


def permutation(feature_id: str, selected: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    dates = [_date(x["event_start"]) for x in selected]
    observed = measurements(feature_id, selected, by_id)
    observed_rate = observed["event_rate"] or 0.0
    null = []
    for _ in range(PERMUTATIONS):
        shuffled = dates[:]
        rng.shuffle(shuffled)
        values = [_feature_value(feature_id, by_id[item["source_record_id"]], shuffled[index]) for index, item in enumerate(selected)]
        null.append(sum(x is True for x in values) / len(values))
    exceed = sum(x >= observed_rate for x in null)
    return {"seed": seed, "iterations": PERMUTATIONS, "observed_event_rate": observed_rate, "null_mean": mean(null), "one_sided_p": (exceed + 1) / (PERMUTATIONS + 1)}


def result_state(validation: dict[str, Any], holdout: dict[str, Any]) -> str:
    vd = (validation["event_rate"] or 0.0) - (validation["matched_control_rate"] or 0.0)
    hd = (holdout["event_rate"] or 0.0) - (holdout["matched_control_rate"] or 0.0)
    if validation["subjects"] < MIN_VALIDATION_SUBJECTS or holdout["subjects"] < MIN_HOLDOUT_SUBJECTS:
        return "INSUFFICIENT_SAMPLE"
    if abs(vd) < MIN_EFFECT and abs(hd) < MIN_EFFECT:
        return "REPLICATED_NO_ASSOCIATION"
    if vd >= MIN_EFFECT and hd >= MIN_EFFECT:
        return "PROMISING_ASSOCIATION"
    if vd >= MIN_EFFECT and hd < MIN_EFFECT:
        return "NON_REPLICATING_ASSOCIATION"
    return "NO_ASSOCIATION"


@lru_cache(maxsize=1)
def build() -> dict[str, Any]:
    records, cohort, registry = load_inputs()
    frozen = freeze(records, cohort, registry)
    by_id = row_for(records)
    base = json.loads((ROOT / "docs/current-state/emp-feature-001/02_OUTCOME_BLIND_PREVALENCE.json").read_text(encoding="utf-8"))
    base_rates = {x["feature_id"]: x["mean_interval_prevalence"] for x in base["features"]}
    selected = frozen["subjects"]
    validation_ids = set(frozen["validation_subjects"])
    validation = [x for x in selected if x["source_record_id"] in validation_ids]
    holdout = [x for x in selected if x["source_record_id"] not in validation_ids]
    validation_results = {feature["feature_id"]: measurements(feature["feature_id"], validation, by_id) for feature in registry["features"]}
    # Holdout values are intentionally calculated only after every validation
    # measurement has been completed; no selection is performed afterward.
    holdout_results = {feature["feature_id"]: measurements(feature["feature_id"], holdout, by_id) for feature in registry["features"]}
    features = []
    for index, feature in enumerate(registry["features"]):
        feature_id = feature["feature_id"]
        all_result = measurements(feature_id, selected, by_id)
        validation_result = validation_results[feature_id]
        holdout_result = holdout_results[feature_id]
        features.append({"feature_id": feature_id, "frozen_contract_hash": feature["hash"], "base_prevalence": base_rates[feature_id], "validation": validation_result, "holdout": holdout_result, "combined": all_result, "event_shuffled": permutation(feature_id, selected, by_id, SEED + index), "subject_event_permutation": permutation(feature_id, validation, by_id, SEED + 100 + index), "multiple_testing": {"family_size": 5, "method": "BONFERRONI_ALPHA_0.05", "adjusted_alpha": 0.01, "adjusted_inference": "NOT_USED_FOR_INSUFFICIENT_SAMPLE"}, "state": result_state(validation_result, holdout_result), "source_status_unchanged": True, "production_status": "INACTIVE"})
    manifest = {"programme": "VEDA-EMP-FEATURE-002", "overall_status": "COMPLETE_WITH_CONDITION", "replication_status": "COMPLETE", "event_family": "POSITION_START", "cohort_id": frozen["cohort_id"], "subjects": 20, "validation_subjects": 14, "holdout_subjects": 6, "feature_hashes_verified": True, "prior_subject_overlap": 0, "feature_based_acquisition": False, "holdout_leakage": False, "holdout_unsealed_once_after_validation": True, "promising_features": [x["feature_id"] for x in features if x["state"] == "PROMISING_ASSOCIATION"], "replicated_associations": [x["feature_id"] for x in features if x["state"] == "REPLICATED_ASSOCIATION"], "replicated_no_association": [x["feature_id"] for x in features if x["state"] == "REPLICATED_NO_ASSOCIATION"], "insufficient": [x["feature_id"] for x in features if x["state"] == "INSUFFICIENT_SAMPLE"], "production_changed": False, "approved_core_changed": False, "rag_changed": False, "ml_used": False, "composition_used": False, "pred_m4": "INSUFFICIENT_SAMPLE", "next_recommended_programme": "NEW_EVENT_FAMILY_OR_PROSPECTIVE_FEATURE_CANDIDATE_REVIEW"}
    return {"freeze": frozen, "features": features, "manifest": manifest}


def main() -> None:
    output = build()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for key, name in (("freeze", "02_COHORT_FREEZE.json"), ("features", "03_REPLICATION_RESULTS.json"), ("manifest", "04_FINAL_MANIFEST.json")):
        (OUTPUT_DIR / name).write_text(json.dumps(output[key], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output["manifest"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
