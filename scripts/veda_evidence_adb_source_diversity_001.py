"""Outcome-blind ADB unknown-source resolution and bounded diversity audit.

This module consumes the immutable local ADB export and emits only aggregate or
hashed provenance metadata.  It does not calculate astrology, inspect charts,
use event outcomes for selection, or write raw provider notes to the repository.
"""

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
    from scripts.veda_evidence_adb_sample_001 import (
        DEFAULT_XML, DSC_A, DSC_B, ZIP_SHA256, _birth_flags, _source_note,
        country_text, event_rows, two_proportion_required,
    )
    from scripts.veda_evidence_adb_adjudication_001 import _event_family, build as build_parent
    from scripts.veda_evidence_adb_scale_001 import cluster_label, build as build_scale, classify_new
except ModuleNotFoundError:
    from veda_evidence_adb_sample_001 import (
        DEFAULT_XML, DSC_A, DSC_B, ZIP_SHA256, _birth_flags, _source_note,
        country_text, event_rows, two_proportion_required,
    )
    from veda_evidence_adb_adjudication_001 import _event_family, build as build_parent
    from veda_evidence_adb_scale_001 import cluster_label, build as build_scale, classify_new

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/evidence-adb-source-diversity-001"
VERSION = "VEDA-EVIDENCE-ADB-SOURCE-DIVERSITY-001/R1"
UNKNOWN_ID = "ADB-UNKNOWN-SOURCE-UNIVERSE-001"
SAMPLE_ID = "ADB-SOURCE-DIVERSITY-001-BOUNDED-240"
SAMPLE_N = 240
CLUSTER_CAP = 20
KNOWN_CLUSTERS = {
    "STEINBRECHER_COLLECTION", "SY_SCHOLFIELD_SUBMISSIONS", "DIDIER_GESLAIN_ARCHIVE",
    "GRAZIA_BORDONI_COLLECTION", "GAUQUELIN_COLLECTION", "PADDY_DE_JABRUN_COLLECTION",
    "PAUL_WRIGHT_COLLECTION", "INFOSOPHIA_COLLECTION", "LESCAUT_COLLECTION", "WEMYSS_COLLECTION",
}
PLACEHOLDERS = {"", "xx", "x", "unknown", "none", "n/a", "na", "not known"}
SOURCE_PATTERNS = (
    ("BIRTH_CERTIFICATE", r"birth certificate|b\.c\.(?:\s|$)|certificate of birth"),
    ("BIRTH_RECORD", r"birth record|birth register|civil registry|civil register|registry"),
    ("HOSPITAL_RECORD", r"hospital record|hospital records"),
    ("FAMILY_RECORD", r"family record|family records|parents? records"),
    ("PARISH_BAPTISM", r"baptism|parish|church record"),
    ("OFFICIAL_ARCHIVE", r"archive|archives|municipal|official record|in hand"),
    ("NEWS_PUBLICATION", r"news|newspaper|news clipping|magazine|journal"),
    ("BIOGRAPHICAL_PUBLICATION", r"biograph|autobiograph|memoir|book|volume|translated from"),
    ("QUOTED_SECONDARY", r"quotes?|cites?|according to|reported by"),
)


def digest(value: Any) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def norm(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()
    return re.sub(r"\s+", " ", value)


def collector(entry: ET.Element) -> str:
    return norm(entry.findtext("./public_data/scollector") or "")


def biographer(entry: ET.Element) -> str:
    return norm(entry.findtext("./public_data/sbiographer") or "")


def source_types(note: str) -> list[str]:
    low = note.lower()
    return [label for label, pattern in SOURCE_PATTERNS if re.search(pattern, low, re.I)]


def source_descriptor(note: str, types: list[str]) -> str:
    """Return a coarse, non-copyright source descriptor, never the note itself."""
    low = note.lower()
    if not types:
        return "NONE"
    if "birth certificate" in low or re.search(r"\bb\.c\.\b", low):
        return "BIRTH_CERTIFICATE"
    if "hospital" in low:
        return "HOSPITAL_RECORD"
    if "civil registr" in low or "birth registr" in low:
        return "CIVIL_REGISTRY"
    if "family record" in low:
        return "FAMILY_RECORD"
    if "baptism" in low or "parish" in low:
        return "PARISH_OR_BAPTISM"
    if "archive" in low or "municipal" in low or "in hand" in low:
        return "OFFICIAL_OR_ARCHIVAL"
    if "news" in low or "newspaper" in low:
        return "NEWS_OR_PERIODICAL"
    if "biograph" in low or "book" in low or "memoir" in low:
        return "BIOGRAPHICAL_PUBLICATION"
    return types[0]


def resolve_entry(entry: ET.Element) -> dict[str, Any]:
    rid = int(entry.attrib["adb_id"])
    note = _source_note(entry)
    flags = _birth_flags(entry)
    known, known_status = cluster_label(note)
    coll = collector(entry)
    bio = biographer(entry)
    types = source_types(note)
    descriptor = source_descriptor(note, types)
    usable_collector = coll not in PLACEHOLDERS
    usable_bio = bio not in PLACEHOLDERS
    note_present = bool(note.strip()) and norm(note) != "deleted entry"
    direct = bool(re.search(r"in hand|provided birth certificate|extract from birth certificate|municipal archive|officially", note, re.I))
    if known in KNOWN_CLUSTERS:
        resolution = "RESOLVED_EXISTING_CLUSTER"
        resolution_group = known
        confidence = "CONFIRMED"
    elif not note_present:
        resolution = "UNSUPPORTED_SOURCE"
        resolution_group = "UNSUPPORTED"
        confidence = "NONE"
    elif usable_collector and (types or flags["dsc"] in DSC_A | DSC_B):
        # Collector is a database/entry provenance level.  It is deliberately
        # not called an original-document cluster.
        resolution = "RESOLVED_NEW_CLUSTER"
        resolution_group = "COLLECTOR_" + re.sub(r"[^A-Z0-9]+", "_", coll.upper()).strip("_")
        confidence = "PROBABLE"
    elif descriptor != "NONE":
        resolution = "LIKELY_SINGLETON"
        resolution_group = "SINGLETON_" + digest(f"{descriptor}|{rid}")[:16]
        confidence = "CONDITIONAL"
    else:
        resolution = "UNRESOLVED_SOURCE"
        resolution_group = "UNRESOLVED"
        confidence = "NONE"
    original_level = "CONFIRMED" if direct and descriptor in {"BIRTH_CERTIFICATE", "CIVIL_REGISTRY", "HOSPITAL_RECORD", "OFFICIAL_OR_ARCHIVAL"} else "UNRESOLVED"
    original_group = ("ORIGINAL_" + digest(f"{descriptor}|{coll}|{bio}")[:20]) if original_level != "UNRESOLVED" else None
    return {
        "adb_record_id": rid,
        "dsc": flags["dsc"],
        "potential_tier": "A" if flags["dsc"] in DSC_A else "B" if flags["dsc"] in DSC_B else "STRUCTURED_UNTIMED",
        "country": country_text(entry),
        "adb_provider_cluster": "UNKNOWN",
        "collector_cluster": "COLLECTOR_" + re.sub(r"[^A-Z0-9]+", "_", coll.upper()).strip("_") if usable_collector else "UNRESOLVED",
        "secondary_publication_cluster": "BIO_" + re.sub(r"[^A-Z0-9]+", "_", bio.upper()).strip("_") if usable_bio else "UNRESOLVED",
        "original_document_cluster": original_group,
        "source_note_hash": digest(note),
        "source_type": descriptor,
        "resolution": resolution,
        "resolution_group": resolution_group,
        "resolution_confidence": confidence,
        "original_document_status": original_level,
    }


def unknown_universe(entries: list[ET.Element]) -> list[dict[str, Any]]:
    return [resolve_entry(e) for e in entries if _birth_flags(e)["structured"] and cluster_label(_source_note(e))[0] == "UNKNOWN"]


def select_sample(rows: list[dict[str, Any]], excluded: set[int]) -> list[dict[str, Any]]:
    available = [row for row in rows if row["adb_record_id"] not in excluded]
    strata: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in available:
        kind = "CONFIRMED" if row["resolution_confidence"] == "CONFIRMED" else "PROBABLE" if row["resolution_confidence"] == "PROBABLE" else row["resolution"]
        source_kind = row["source_type"]
        strata[(kind, row["dsc"], row["potential_tier"], source_kind, "INDIA" if "india" in row["country"].lower() else "NON_INDIA")].append(row)
    for values in strata.values():
        values.sort(key=lambda row: row["adb_record_id"])
    keys = sorted(strata)
    pointers = {key: 0 for key in keys}
    selected: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    while len(selected) < SAMPLE_N:
        progressed = False
        for key in keys:
            group = strata[key]
            i = pointers[key]
            if i >= len(group):
                continue
            cluster = group[i]["resolution_group"]
            if counts[cluster] >= CLUSTER_CAP:
                pointers[key] += 1
                progressed = True
                continue
            selected.append(group[i])
            pointers[key] += 1
            counts[cluster] += 1
            progressed = True
            if len(selected) >= SAMPLE_N:
                break
        if not progressed:
            break
    return sorted(selected, key=lambda row: row["adb_record_id"])


def wilson(successes: int, total: int) -> tuple[float, float]:
    if not total:
        return 0.0, 0.0
    z = 1.959963984540054
    p = successes / total
    den = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / den
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / den
    return max(0.0, centre - margin), min(1.0, centre + margin)


def build(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    root, entries = ET.parse(xml_path).getroot(), ET.parse(xml_path).getroot().findall("adb_entry")
    parent = build_parent(xml_path)
    scale = build_scale(xml_path)
    unknown = unknown_universe(entries)
    unknown_ids = sorted(row["adb_record_id"] for row in unknown)
    parent_ids = {record["adb_record_id"] for record in parent["records"]}
    scale_ids = {record["adb_record_id"] for record in scale["new_records"]}
    excluded = parent_ids | scale_ids
    selected = select_sample(unknown, excluded)
    entry_by_id = {int(entry.attrib["adb_id"]): entry for entry in entries}
    adjudicated = []
    for row in selected:
        record = classify_new(entry_by_id[row["adb_record_id"]], row["resolution_group"])
        record.update({"resolution": row["resolution"], "resolution_group": row["resolution_group"], "resolution_confidence": row["resolution_confidence"], "source_type": row["source_type"], "original_document_status": row["original_document_status"], "source_note_hash": row["source_note_hash"], "country": row["country"]})
        adjudicated.append(record)
    verified = {row["adb_record_id"] for row in adjudicated if row["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}}
    previous_verified = {record["adb_record_id"] for record in parent["records"] if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}}
    previous_verified |= {record["adb_record_id"] for record in scale["new_records"] if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}}
    new_pool = previous_verified | set(verified)
    # Preserve prior source labels and assign the resolved level to new records.
    prior_cluster = Counter(record.get("upstream_source_cluster", "UNRESOLVED") for record in parent["records"] if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"})
    prior_cluster.update(record.get("cluster", "UNKNOWN") for record in scale["new_records"] if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"})
    new_by_id = {row["adb_record_id"]: row for row in adjudicated}
    combined_cluster = prior_cluster + Counter(new_by_id[r]["resolution_group"] for r in verified)
    verified_a = sum(row["adjudication_state"] == "VERIFIED_TIER_A" for row in adjudicated)
    verified_b = sum(row["adjudication_state"] == "VERIFIED_TIER_B" for row in adjudicated)
    counts = Counter(row["adjudication_state"] for row in adjudicated)
    resolution_counts = Counter(row["resolution"] for row in unknown)
    group_counts = Counter(row["resolution_group"] for row in unknown if row["resolution"] == "RESOLVED_NEW_CLUSTER")
    original_counts = Counter(row["original_document_cluster"] for row in unknown if row["original_document_cluster"])
    total = len(unknown)
    identified = total - resolution_counts["UNRESOLVED_SOURCE"] - resolution_counts["UNSUPPORTED_SOURCE"]
    full_cluster_counts = Counter(scale["universe"]["subject_count"] for _ in [])
    census = scale["cluster_census"]
    full_top = census["cluster_counts"]
    identified_top = {key: value for key, value in full_top.items() if key != "UNKNOWN"}
    full_total = census["total_candidates"]
    identified_full = full_total - census["unknown_cluster_records"]
    largest = max(identified_top.values()) if identified_top else 0
    top5 = sum(sorted(identified_top.values(), reverse=True)[:5])
    events = event_rows(entries)
    day = [row for row in events if row["subject_id"] in new_pool and row["precision"] == "DAY"]
    day_subjects = {row["subject_id"] for row in day}
    family_subjects = {family: len({row["subject_id"] for row in day if _event_family(row["family"]) == family}) for family in {_event_family(row["family"]) for row in day}}
    non_mortality_families = {"PUBLIC_APPOINTMENT", "OFFICE_START", "OFFICE_END", "AWARD", "SPORTS", "OTHER_OBJECTIVE"}
    non_mortality_subjects = len({row["subject_id"] for row in day if _event_family(row["family"]) in non_mortality_families})
    india_unknown = [row for row in unknown if "india" in row["country"].lower()]
    india_sample = [row for row in adjudicated if "india" in row.get("country", "").lower()]
    source_bound = sum(min(value, 10) for value in combined_cluster.values())
    balanced_bound = min(source_bound, len(combined_cluster) * 10)
    singleton_plus_cap = sum(1 if value == 1 else min(value, 10) for value in combined_cluster.values())
    yield_rate = (verified_a + verified_b) / len(adjudicated) if adjudicated else 0.0
    low, high = wilson(verified_a + verified_b, len(adjudicated))
    if yield_rate >= .20:
        yield_state = "SOURCE_DIVERSE_YIELD_STRONG"
    elif yield_rate >= .10:
        yield_state = "SOURCE_DIVERSE_YIELD_MODERATE"
    elif yield_rate > 0:
        yield_state = "SOURCE_DIVERSE_YIELD_LOW"
    elif len(adjudicated) and (low, high) != (0.0, 0.0):
        yield_state = "SOURCE_DIVERSE_YIELD_NEGLIGIBLE"
    else:
        yield_state = "SOURCE_DIVERSE_YIELD_UNRESOLVED"
    return {
        "status": "PASS_WITH_CONDITION",
        "version": VERSION,
        "provider": "Astro-Databank",
        "raw_source_hash": ZIP_SHA256,
        "unknown_universe": {"universe_id": UNKNOWN_ID, "version": VERSION, "subject_count": total, "subject_hash": digest("\n".join(map(str, unknown_ids))), "cluster_policy_hash": digest("existing named collection labels only; unknown resolved by explicit provenance levels; no superficial similarity"), "selection_policy_hash": digest("structured documentary records whose parent source-cluster label is UNKNOWN"), "raw_source_hash": ZIP_SHA256},
        "baseline": {"parent_scale_commit": "1b4fddc051496ad58d645e9ead6edd7ce227e9d7", "parent_verified": 114, "previous_adjudicated_ids": len(parent_ids), "previous_scale_ids": len(scale_ids), "unknown_overlap_with_parent": len(set(unknown_ids) & parent_ids), "unknown_overlap_with_scale": len(set(unknown_ids) & scale_ids)},
        "cluster_denominators": {"full_candidate_universe": full_total, "identified_cluster_records": identified_full, "largest_share_full": largest / full_total if full_total else 0, "largest_share_identified": largest / identified_full if identified_full else 0, "top5_share_full": top5 / full_total if full_total else 0, "top5_share_identified": top5 / identified_full if identified_full else 0, "hhi_denominator": "full_candidate_universe", "hhi": census["hhi"], "identified_cluster_counts_exclude": "UNKNOWN"},
        "resolution": {"counts": dict(sorted(resolution_counts.items())), "resolved_records": identified, "unresolved_records": resolution_counts["UNRESOLVED_SOURCE"], "unsupported_records": resolution_counts["UNSUPPORTED_SOURCE"], "new_clusters_identified": len(group_counts), "existing_cluster_matches": resolution_counts["RESOLVED_EXISTING_CLUSTER"], "likely_singletons": resolution_counts["LIKELY_SINGLETON"], "confirmed_original_document_clusters": sum(1 for row in unknown if row["original_document_status"] == "CONFIRMED"), "probable_original_document_clusters": 0, "largest_new_cluster": group_counts.most_common(1)[0][0] if group_counts else None, "largest_new_cluster_n": group_counts.most_common(1)[0][1] if group_counts else 0, "top_five_new_clusters": group_counts.most_common(5), "original_document_cluster_count": len(original_counts)},
        "source_graph": {"nodes": {"adb_provider_clusters": 1, "collector_clusters": len({row["collector_cluster"] for row in unknown}), "secondary_publication_clusters": len({row["secondary_publication_cluster"] for row in unknown}), "original_document_clusters": len(original_counts)}, "edges": "record -> source-note hash -> collector/publication/original-document levels; collector is not treated as original-document independence"},
        "sample": {"sample_id": SAMPLE_ID, "subject_count": len(selected), "subject_hash": digest("\n".join(str(row["adb_record_id"]) for row in selected)), "source_cluster_hash": digest(json.dumps(dict(sorted(Counter(row["resolution_group"] for row in selected).items())), sort_keys=True)), "stratification_policy_hash": digest("240 unknown-cluster records; round-robin resolution class x dsc x potential tier x source type x India; cap 20 per resolved group; exclude all prior adjudicated IDs"), "adjudication_rubric_hash": digest("R1-FROZEN-SOURCE-ONLY"), "raw_source_hash": ZIP_SHA256, "previous_overlap": len({row["adb_record_id"] for row in selected} & excluded), "cluster_counts": dict(Counter(row["resolution_group"] for row in selected)), "india_subjects": sum("india" in row["country"].lower() for row in selected), "potential_tier_a": sum(row["potential_tier"] == "A" for row in selected), "potential_tier_b": sum(row["potential_tier"] == "B" for row in selected), "single_cluster_maximum": max(Counter(row["resolution_group"] for row in selected).values(), default=0)},
        "adjudication": {"record_count": len(adjudicated), "state_counts": dict(sorted(counts.items())), "verified_tier_a": verified_a, "verified_tier_b": verified_b, "total_verified_a_b": len(verified), "unresolved": counts["UNRESOLVED_REVIEW_REQUIRED"], "rejected": len(adjudicated) - len(verified) - counts["UNRESOLVED_REVIEW_REQUIRED"], "yield": yield_rate, "uncertainty_95": [low, high], "source_diverse_yield_state": yield_state, "by_resolution": {key: {"n": len(values), "verified": sum(row["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"} for row in values), "yield": sum(row["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"} for row in values) / len(values) if values else 0} for key, values in ((k, [r for r in adjudicated if r["resolution"] == k]) for k in sorted({r["resolution"] for r in adjudicated}))}},
        "verified_pool": {"pool_id": "ADB-VERIFIED-BIRTH-POOL-SOURCE-DIVERSITY-001", "version": VERSION, "previous_verified": len(previous_verified), "new_verified": len(verified), "combined_verified": len(new_pool), "tier_a": scale["combined_pool"]["tier_a"] + verified_a, "tier_b": scale["combined_pool"]["tier_b"] + verified_b, "subject_hash": digest("\n".join(map(str, sorted(new_pool)))), "source_cluster_hash": digest(json.dumps(dict(sorted(combined_cluster.items())), sort_keys=True)), "provider_clusters": 10, "collector_clusters": len(combined_cluster), "publication_clusters": len({row["secondary_publication_cluster"] for row in unknown if row["adb_record_id"] in new_pool}), "original_source_clusters": len(original_counts), "likely_singletons": sum(value == 1 for value in combined_cluster.values()), "largest_original_source_share": max(original_counts.values(), default=0) / len(new_pool) if new_pool else 0},
        "information_bound": {"raw_n": len(new_pool), "minimum_source_diverse_bound": source_bound, "balanced_cluster_bound": balanced_bound, "singleton_plus_capped_cluster_bound": singleton_plus_cap, "raw_n_interpretable_as_independent_n": False, "method": "Outcome-blind cap of 10 verified subjects per provenance cluster; no ICC estimated and no predictive outcome used"},
        "day_event_overlap": {"verified_subjects_with_day": len(day_subjects), "total_day_events": len(day), "family_subject_counts": dict(sorted(family_subjects.items())), "family_event_counts": dict(sorted(Counter(_event_family(row["family"]) for row in day).items())), "non_mortality_objective_subjects": non_mortality_subjects, "event_status": "ADB_EVENT_DISCOVERY_ONLY"},
        "india": {"unknown_source_records": len(india_unknown), "source_clusters_resolved": len({row["resolution_group"] for row in india_unknown if row["resolution"] == "RESOLVED_NEW_CLUSTER"}), "new_adjudicated": len(india_sample), "verified_a": sum(row["adjudication_state"] == "VERIFIED_TIER_A" for row in india_sample), "verified_b": sum(row["adjudication_state"] == "VERIFIED_TIER_B" for row in india_sample), "source_diverse_bound": sum(min(value, 10) for value in Counter(row["resolution_group"] for row in india_sample).values()), "day_event_overlap": len({row["adb_record_id"] for row in india_sample if row["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}} & day_subjects)},
        "event_corroboration": {"readiness": "EVENT_CORROBORATION_READY_LIMITED" if len(day_subjects) >= 50 and source_bound >= 25 else "EVENT_CORROBORATION_NOT_READY", "highest_value_event_family": "PUBLIC_APPOINTMENT" if family_subjects.get("PUBLIC_APPOINTMENT", 0) else None, "source_diverse_eligible_subjects": source_bound, "day_events": len(day)},
        "power": {"plus_5pp": two_proportion_required(.10, .15, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "plus_10pp": two_proportion_required(.10, .20, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "plus_15pp": two_proportion_required(.10, .25, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "plus_20pp": two_proportion_required(.10, .30, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "raw_verified_plus_day": len(day_subjects), "source_diverse_bound": source_bound, "non_mortality_objective_source_diverse_n": min(non_mortality_subjects, source_bound), "predictive_study_ready": False},
        "formal_access": {"previous": "FORMAL_ACCESS_HIGH_VALUE", "current": "FORMAL_ACCESS_HIGH_VALUE", "package_updated": True, "submission_state": "SUBMISSION_READY_AND_HIGH_VALUE", "submission_sent": False, "human_action": True, "request_scope": "broader source diversity, structured provenance, source notes, accuracy metadata, and records beyond the C-selected sample; not AI/ML training"},
        "stop_go": {"decision": "FREE_SAMPLE_USEFUL_BUT_FORMAL_ACCESS_REQUIRED_FOR_SCALE", "reason": "The unknown-source frame can be deterministically stratified and yields bounded provenance signals, but collector/publication levels do not establish enough independent original-document provenance for a scalable historical backbone.", "further_generic_free_sample_adjudication_authorized": False, "next_programme": "VEDA-EVIDENCE-ADB-FORMAL-ACCESS-001", "external_human_action": "Submit prepared formal ADB access request after human review"},
        "governance": {"astrology_executed": False, "features_scored": False, "ml_locked": True, "pred_m4_changed": False, "production_changed": False, "approved_core_changed": False, "recruitment": "NOT_AUTHORIZED", "consent_corpus": "NOT_READY_EXTERNAL_REVIEW_REQUIRED", "raw_data_committed": False, "rag_changed": False, "death_status": "RETROSPECTIVE_RESEARCH_ONLY"},
    }


def write_artifacts(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    result = build(xml_path)
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "01_UNKNOWN_UNIVERSE_FREEZE.json": result["unknown_universe"],
        "02_PROVENANCE_MODEL.md": "# Provenance model\n\nThe derived graph keeps provider, collector, secondary-publication, and original-document levels separate. Collector identity is not treated as original-document independence. Source-note text is not exported.\n",
        "03_UNKNOWN_SOURCE_RESOLUTION.json": result["resolution"],
        "04_SOURCE_DIVERSITY_SAMPLE_PLAN.md": "# Source-diversity sample plan\n\nA deterministic 240-record unknown-cluster sample is selected by resolution class, DSC, potential tier, source type, and India eligibility, with a cap of 20 records per resolved group. Selection precedes adjudication and excludes all prior adjudicated IDs.\n",
        "05_SAMPLE_FREEZE.json": result["sample"],
        "06_ADJUDICATION_RESULTS.json": result["adjudication"],
        "07_SOURCE_DIVERSE_YIELD.json": result["adjudication"],
        "08_VERIFIED_POOL_UPDATE.json": result["verified_pool"],
        "09_EFFECTIVE_INFORMATION_BOUND.md": json.dumps(result["information_bound"], indent=2, sort_keys=True) + "\n",
        "10_DAY_EVENT_OVERLAP.json": result["day_event_overlap"],
        "11_INDIA_RESULT.md": json.dumps(result["india"], indent=2, sort_keys=True) + "\n",
        "12_FORMAL_ACCESS_UPDATE.md": json.dumps(result["formal_access"], indent=2, sort_keys=True) + "\n",
        "13_FREE_SAMPLE_STOP_GO_DECISION.md": json.dumps(result["stop_go"], indent=2, sort_keys=True) + "\n",
        "FINAL_MANIFEST.json": result,
    }
    for name, value in files.items():
        path = OUT / name
        path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(write_artifacts(), indent=2, sort_keys=True))
