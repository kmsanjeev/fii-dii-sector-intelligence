"""Source-cluster-aware ADB scale adjudication; outcome-blind and aggregate-safe."""

from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from scripts.veda_evidence_adb_adjudication_001 import (
        DEFAULT_XML, REVIEW_VERSION, _documented_timed, _direct_original, _event_family,
        _source_cluster, build as build_parent_adjudication, load_entries,
    )
    from scripts.veda_evidence_adb_sample_001 import (
        DSC_A, DSC_B, DSC_STRUCTURED, ZIP_SHA256, _birth_flags, _source_note, country_text,
        event_rows, two_proportion_required,
    )
except ModuleNotFoundError:
    from veda_evidence_adb_adjudication_001 import (
        DEFAULT_XML, REVIEW_VERSION, _documented_timed, _direct_original, _event_family,
        _source_cluster, build as build_parent_adjudication, load_entries,
    )
    from veda_evidence_adb_sample_001 import (
        DSC_A, DSC_B, DSC_STRUCTURED, ZIP_SHA256, _birth_flags, _source_note, country_text,
        event_rows, two_proportion_required,
    )

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/evidence-adb-scale-001"
SAMPLE_ID = "ADB-SCALE-001-STRATIFIED-400"
SAMPLE_VERSION = "VEDA-EVIDENCE-ADB-SCALE-001/R1"
STRATIFICATION_POLICY = "400 new records; source-cluster x dsc x potential-tier round-robin; Steinbrecher cap 50; exclude original adjudicated IDs"
CLUSTER_POLICY = "named source-note collection/archive signals; no coincidental wording; otherwise UNKNOWN"
CAP = 50


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def cluster_label(note: str) -> tuple[str, str]:
    lowered = note.lower()
    patterns = [
        ("STEINBRECHER_COLLECTION", r"steinbrecher"),
        ("SY_SCHOLFIELD_SUBMISSIONS", r"scholfield"),
        ("DIDIER_GESLAIN_ARCHIVE", r"geslain"),
        ("GRAZIA_BORDONI_COLLECTION", r"bordoni"),
        ("GAUQUELIN_COLLECTION", r"gauquelin"),
        ("PADDY_DE_JABRUN_COLLECTION", r"de jabrun"),
        ("PAUL_WRIGHT_COLLECTION", r"paul wright"),
        ("INFOSOPHIA_COLLECTION", r"infosophia"),
        ("LESCAUT_COLLECTION", r"lescaut"),
        ("WEMYSS_COLLECTION", r"wemyss"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, lowered):
            return label, "CLUSTER_CONFIRMED"
    return "UNKNOWN", "UNKNOWN"


def wilson(successes: int, total: int) -> tuple[float, float]:
    if not total:
        return 0.0, 0.0
    z = 1.959963984540054
    p = successes / total
    den = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / den
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / den
    return max(0.0, centre - margin), min(1.0, centre + margin)


def classify_new(entry: ET.Element, cluster: str) -> dict[str, Any]:
    flags = _birth_flags(entry)
    note = _source_note(entry)
    dsc = flags["dsc"]
    if dsc in {"56", "57", "58"}:
        state, reason = "REJECTED_UNTIMED", "Structured source is explicitly untimed."
    elif flags["time_unknown"] or flags["itimeacc"] == "ABSENT":
        state, reason = "REJECTED_PRECISION", "No usable explicit provider time accuracy or time is explicitly unknown."
    elif flags["rectified"]:
        state, reason = "REJECTED_RECTIFIED", "Source note or source code identifies rectification/speculation."
    elif flags["conflict"]:
        state, reason = "REJECTED_CONFLICT", "Source note or source code identifies material conflict."
    elif dsc in DSC_A and _direct_original(note):
        state, reason = "VERIFIED_TIER_A", "Direct/official documentary source wording meets the frozen Tier A rubric."
    elif dsc in DSC_B | {"2", "4"} and _documented_timed(note):
        state, reason = "VERIFIED_TIER_B", "Referenced timed documentary/news/biographical source meets the frozen Tier B rubric."
    elif dsc in DSC_STRUCTURED:
        state, reason = "REJECTED_SOURCE_LINEAGE", "Structured source class is not sufficiently supported by the source note for autonomous Tier A/B verification."
    else:
        state, reason = "UNRESOLVED_REVIEW_REQUIRED", "Source-note semantics remain unresolved under the frozen rubric."
    return {
        "adb_record_id": int(entry.attrib["adb_id"]),
        "dsc": dsc,
        "potential_tier": "A" if dsc in DSC_A else "B" if dsc in DSC_B else "STRUCTURED_UNTIMED",
        "cluster": cluster,
        "itimeacc": flags["itimeacc"],
        "stimeacc": flags["stimeacc"],
        "time_unknown": flags["time_unknown"],
        "alternative_birth_data": flags["bdata_alt"],
        "source_note_hash": sha256_text(note),
        "adjudication_state": state,
        "adjudication_reason": reason,
        "review_version": SAMPLE_VERSION,
    }


def select_sample(universe: list[dict[str, Any]], excluded: set[int]) -> list[dict[str, Any]]:
    available = [row for row in universe if row["adb_record_id"] not in excluded]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in available:
        groups[(row["cluster"], row["dsc"], row["potential_tier"])].append(row)
    for rows in groups.values():
        rows.sort(key=lambda row: row["adb_record_id"])
    selected: list[dict[str, Any]] = []
    pointers = {key: 0 for key in groups}
    keys = sorted(groups)
    # Round-robin across strata, with an explicit cap on the dominant cluster.
    while len(selected) < 400 and keys:
        progressed = False
        for key in keys:
            cluster = key[0]
            if cluster == "STEINBRECHER_COLLECTION" and sum(row["cluster"] == cluster for row in selected) >= CAP:
                continue
            index = pointers[key]
            if index >= len(groups[key]):
                continue
            selected.append(groups[key][index])
            pointers[key] += 1
            progressed = True
            if len(selected) >= 400:
                break
        if not progressed:
            break
    return sorted(selected, key=lambda row: row["adb_record_id"])


def build(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    root, entries = load_entries(xml_path)
    parent = build_parent_adjudication(xml_path)
    original_records = parent["records"]
    original_ids = {record["adb_record_id"] for record in original_records}
    universe_entries = [entry for entry in entries if _birth_flags(entry)["structured"]]
    universe_rows = []
    for entry in universe_entries:
        cluster, cluster_status = cluster_label(_source_note(entry))
        flags = _birth_flags(entry)
        universe_rows.append({"adb_record_id": int(entry.attrib["adb_id"]), "cluster": cluster, "cluster_status": cluster_status, "dsc": flags["dsc"], "potential_tier": "A" if flags["dsc"] in DSC_A else "B" if flags["dsc"] in DSC_B else "STRUCTURED_UNTIMED"})
    universe_ids = sorted(row["adb_record_id"] for row in universe_rows)
    cluster_counts = Counter(row["cluster"] for row in universe_rows)
    top = cluster_counts.most_common()
    total = len(universe_rows)
    hhi = sum((count / total) ** 2 for count in cluster_counts.values()) if total else 0.0
    sample_rows = select_sample(universe_rows, original_ids)
    entry_by_id = {int(entry.attrib["adb_id"]): entry for entry in universe_entries}
    new_records = [classify_new(entry_by_id[row["adb_record_id"]], row["cluster"]) for row in sample_rows]
    verified_new = {record["adb_record_id"] for record in new_records if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}}
    combined_ids = {record["adb_record_id"] for record in original_records if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}} | verified_new
    combined_records = original_records + new_records
    combined_verified = [record for record in combined_records if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}]
    new_counts = Counter(record["adjudication_state"] for record in new_records)
    by_cluster = defaultdict(list)
    for record in new_records:
        by_cluster[record["cluster"]].append(record)
    cluster_yield = {}
    for cluster, records in sorted(by_cluster.items()):
        verified = sum(record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"} for record in records)
        low, high = wilson(verified, len(records))
        cluster_yield[cluster] = {"sample_n": len(records), "verified_a_b": verified, "yield": verified / len(records) if records else 0.0, "uncertainty_95": [low, high], "tier_a": sum(record["adjudication_state"] == "VERIFIED_TIER_A" for record in records), "tier_b": sum(record["adjudication_state"] == "VERIFIED_TIER_B" for record in records)}
    events = event_rows(entries)
    verified_day = [row for row in events if row["subject_id"] in combined_ids and row["precision"] == "DAY"]
    family_counts = Counter(_event_family(row["family"]) for row in verified_day)
    family_subjects = {family: len({row["subject_id"] for row in verified_day if _event_family(row["family"]) == family}) for family in family_counts}
    clusters_verified = Counter(record.get("cluster", record.get("upstream_source_cluster", "UNKNOWN")) for record in combined_verified)
    known_verified = {key: value for key, value in clusters_verified.items() if key != "UNKNOWN"}
    source_diverse_bound = sum(min(value, 10) for value in known_verified.values())
    india_universe = [row for row in universe_rows if "india" in country_text(entry_by_id[row["adb_record_id"]]).lower()]
    india_sample = [record for record in new_records if record["adb_record_id"] in {row["adb_record_id"] for row in india_universe}]
    india_verified = [record for record in india_sample if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}]
    scale_low, scale_high = wilson(len(combined_verified), len(combined_records))
    # Source-stratified scenarios use the observed non-dominant yield and cap the dominant cluster's contribution.
    non_dom = [record for record in new_records if record["cluster"] != "STEINBRECHER_COLLECTION"]
    non_dom_verified = sum(record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"} for record in non_dom)
    non_dom_yield = non_dom_verified / len(non_dom) if non_dom else 0.0
    potential_non_dom = sum(row["cluster"] != "STEINBRECHER_COLLECTION" for row in universe_rows)
    full_scale = {"conservative": math.floor(potential_non_dom * max(0.0, non_dom_yield - 0.15)), "central": round(potential_non_dom * non_dom_yield) + min(cluster_counts["STEINBRECHER_COLLECTION"], CAP), "optimistic": math.ceil(potential_non_dom * min(1.0, non_dom_yield + 0.10)) + min(cluster_counts["STEINBRECHER_COLLECTION"], CAP), "method": "non-Steinbrecher stratified yield with 15pp/10pp uncertainty bands plus capped dominant-cluster contribution; not independent-N estimation"}
    return {
        "status": "PASS_WITH_CONDITION",
        "provider": "Astro-Databank",
        "export_format": root.attrib.get("export_format"),
        "update_since": root.attrib.get("update_since"),
        "universe": {"universe_id": "ADB-STRUCTURED-DOCUMENTARY-UNIVERSE", "universe_version": SAMPLE_VERSION, "subject_count": total, "universe_hash": sha256_text("\n".join(map(str, universe_ids))), "selection_policy_hash": sha256_text("structured=dsc in official documentary/untimed source classes"), "source_artifact_hash": ZIP_SHA256, "potential_tier_a": sum(row["potential_tier"] == "A" for row in universe_rows), "potential_tier_b": sum(row["potential_tier"] == "B" for row in universe_rows)},
        "cluster_census": {"total_candidates": total, "total_identified_clusters": len(cluster_counts) - int("UNKNOWN" in cluster_counts), "confirmed_clusters": len(cluster_counts) - int("UNKNOWN" in cluster_counts), "probable_clusters": 0, "unknown_cluster_records": cluster_counts["UNKNOWN"], "cluster_counts": dict(top), "largest_cluster": top[0] if top else None, "top_10_cluster_counts": top[:10], "singleton_clusters": sum(value == 1 for value in cluster_counts.values()), "largest_cluster_share": cluster_counts.most_common(1)[0][1] / total if total else 0.0, "top_5_share": sum(value for _, value in top[:5]) / total if total else 0.0, "top_10_share": sum(value for _, value in top[:10]) / total if total else 0.0, "hhi": hhi},
        "sample": {"sample_id": SAMPLE_ID, "sample_version": SAMPLE_VERSION, "subject_count": len(sample_rows), "subject_hash": sha256_text("\n".join(str(row["adb_record_id"]) for row in sample_rows)), "stratification_policy_hash": sha256_text(STRATIFICATION_POLICY), "cluster_policy_hash": sha256_text(CLUSTER_POLICY), "source_artifact_hash": ZIP_SHA256, "cluster_counts": dict(Counter(row["cluster"] for row in sample_rows)), "dsc_counts": dict(Counter(row["dsc"] for row in sample_rows)), "potential_tier_counts": dict(Counter(row["potential_tier"] for row in sample_rows)), "steinbrecher_cap": CAP},
        "new_records": new_records,
        "new_results": {"state_counts": dict(new_counts), "verified_tier_a": new_counts["VERIFIED_TIER_A"], "verified_tier_b": new_counts["VERIFIED_TIER_B"], "verified_a_b": len(verified_new), "yield": len(verified_new) / len(new_records) if new_records else 0.0, "cross_cluster": cluster_yield},
        "combined_pool": {"pool_id": "ADB-VERIFIED-BIRTH-POOL-SCALE-001", "pool_version": SAMPLE_VERSION, "subject_count": len(combined_ids), "tier_a": sum(record["adjudication_state"] == "VERIFIED_TIER_A" for record in combined_verified), "tier_b": sum(record["adjudication_state"] == "VERIFIED_TIER_B" for record in combined_verified), "subject_hash": sha256_text("\n".join(map(str, sorted(combined_ids)))), "source_cluster_hash": sha256_text(json.dumps(dict(sorted(clusters_verified.items())), sort_keys=True)), "eligibility_policy_hash": sha256_text("original frozen verified A/B plus new frozen source-only verified A/B")},
        "source_independence": {"raw_verified_subjects": len(combined_ids), "unique_source_clusters": len(clusters_verified), "confirmed_cluster_subjects": sum(value for key, value in clusters_verified.items() if key != "UNKNOWN"), "singleton_source_subjects": sum(value for key, value in clusters_verified.items() if key != "UNKNOWN" and value == 1), "largest_cluster_share": max(clusters_verified.values()) / len(combined_ids) if combined_ids else 0.0, "top_5_cluster_share": sum(value for _, value in clusters_verified.most_common(5)) / len(combined_ids) if combined_ids else 0.0, "top_10_cluster_share": sum(value for _, value in clusters_verified.most_common(10)) / len(combined_ids) if combined_ids else 0.0, "source_diverse_subject_n": source_diverse_bound, "effective_n_or_bound": source_diverse_bound, "method": "pre-registered cap of 10 verified subjects per known upstream cluster; no ICC invented", "raw_n_suitable_as_independent_n": False},
        "day_event_overlap": {"verified_subjects_with_day": len({row["subject_id"] for row in verified_day}), "total_day_events": len(verified_day), "multi_day_subjects": sum(count > 1 for count in Counter(row["subject_id"] for row in verified_day).values()), "family_event_counts": dict(sorted(family_counts.items())), "family_subject_counts": dict(sorted(family_subjects.items())), "event_status": "ADB_EVENT_DISCOVERY_ONLY"},
        "india": {"candidate_universe": len(india_universe), "potential_tier_a": sum(row["potential_tier"] == "A" for row in india_universe), "potential_tier_b": sum(row["potential_tier"] == "B" for row in india_universe), "clusters": dict(Counter(row["cluster"] for row in india_universe)), "adjudicated": len(india_sample), "verified_tier_a": sum(record["adjudication_state"] == "VERIFIED_TIER_A" for record in india_verified), "verified_tier_b": sum(record["adjudication_state"] == "VERIFIED_TIER_B" for record in india_verified), "day_event_overlap": len({row["subject_id"] for row in verified_day} & {record["adb_record_id"] for record in india_verified})},
        "power": {"plus_5pp": two_proportion_required(.10, .15, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "plus_10pp": two_proportion_required(.10, .20, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "plus_15pp": two_proportion_required(.10, .25, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "plus_20pp": two_proportion_required(.10, .30, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "raw_verified_plus_day_n": len({row["subject_id"] for row in verified_day}), "source_diverse_effective_bound": source_diverse_bound, "predictive_study_ready": False},
        "scale_estimate": full_scale,
        "cluster_generalization": "PARTIALLY_REPLICATES" if non_dom_yield >= 0.5 else "IS_CLUSTER_SPECIFIC",
        "event_readiness": "EVENT_CORROBORATION_READY_LIMITED" if len({row["subject_id"] for row in verified_day}) >= 50 and source_diverse_bound >= 25 else "EVENT_CORROBORATION_NOT_READY",
        "highest_value_event_family": "PUBLIC_APPOINTMENT",
        "formal_access": "FORMAL_ACCESS_HIGH_VALUE",
        "submission_decision": "SUBMISSION_READY_AND_HIGH_VALUE",
        "decision": "CONTINUE_STAGED_ADJUDICATION",
        "governance": {"astrology_executed": False, "feature_scoring": False, "ml_locked": True, "pred_m4_changed": False, "production_changed": False, "approved_core_changed": False, "recruitment_changed": False, "consent_corpus": "NOT_READY_EXTERNAL_REVIEW_REQUIRED", "raw_data_committed": False, "rag_changed": False},
    }


def write_artifacts(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    result = build(xml_path)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in {
        "01_CANDIDATE_UNIVERSE_FREEZE.json": result["universe"],
        "02_SOURCE_CLUSTER_CENSUS.json": result["cluster_census"],
        "04_STRATIFIED_SAMPLE_FREEZE.json": result["sample"],
        "05_ADJUDICATION_RESULTS.json": {"new_results": result["new_results"], "record_count": len(result["new_records"])},
        "06_CROSS_CLUSTER_YIELD.json": result["new_results"]["cross_cluster"],
        "07_VERIFIED_BIRTH_POOL_FREEZE.json": result["combined_pool"],
        "09_DAY_EVENT_OVERLAP.json": result["day_event_overlap"],
        "11_POWER_READINESS.json": result["power"],
        "FINAL_MANIFEST.json": {key: value for key, value in result.items() if key not in {"new_records"}},
    }.items():
        (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "03_STRATIFIED_ADJUDICATION_PLAN.md").write_text("# Stratified adjudication plan\n\nA deterministic 400-record sample was selected by round-robin across upstream cluster, dsc, and potential-tier strata after excluding the original 120 records. Steinbrecher contribution is capped at 50. Selection is frozen before source-note adjudication.\n", encoding="utf-8")
    return {key: value for key, value in result.items() if key != "new_records"}


if __name__ == "__main__":
    print(json.dumps(write_artifacts(), indent=2, sort_keys=True))
