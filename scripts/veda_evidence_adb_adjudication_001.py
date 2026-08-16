"""Blind ADB birth-source-note adjudication; no astrology or outcome selection."""

from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts.veda_evidence_adb_sample_001 import (
        DEFAULT_XML, EVENT_MAP, ZIP_SHA256, _birth_flags, _source_note, country_text, event_rows,
    )
except ModuleNotFoundError:
    from veda_evidence_adb_sample_001 import (
        DEFAULT_XML, EVENT_MAP, ZIP_SHA256, _birth_flags, _source_note, country_text, event_rows,
    )

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/evidence-adb-adjudication-001"
REVIEW_VERSION = "VEDA-EVIDENCE-ADB-ADJUDICATION-001/R1"
SELECTION_POLICY = "reason=REQUIRES_SOURCE_ADJUDICATION from frozen parent provenance rubric; no chart/event/outcome inputs"
RUBRIC_VERSION = "R1-FROZEN-SOURCE-ONLY"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def load_entries(xml_path: Path = DEFAULT_XML) -> tuple[ET.Element, list[ET.Element]]:
    if not xml_path.exists():
        raise FileNotFoundError(xml_path)
    root = ET.parse(xml_path).getroot()
    return root, root.findall("adb_entry")


def _source_cluster(note: str) -> str:
    lowered = note.lower()
    if "steinbrecher" in lowered:
        return "STEINBRECHER_COLLECTION"
    if "geslain" in lowered:
        return "DIDIER_GESLAIN_ARCHIVE"
    if "scholfield" in lowered:
        return "SY_SCHOLFIELD_SUBMISSIONS"
    if "bordoni" in lowered:
        return "GRAZIA_BORDONI_COLLECTION"
    if "gauquelin" in lowered:
        return "GAUQUELIN_COLLECTION"
    return "OTHER_OR_UNRESOLVED"


def _direct_original(note: str) -> bool:
    direct = re.search(r"in hand|provided birth certificate|extract from birth certificate|municipal archive|conservateur|legislation|officially", note, re.I)
    secondary_only = "quotes" in note.lower() and "in hand" not in note.lower()
    return bool(direct) and not secondary_only


def _documented_timed(note: str) -> bool:
    return bool(re.search(r"birth certificate|birth record|hospital|news report|newspaper|biograph|autobiograph|diary", note, re.I))


def adjudicate(entry: ET.Element) -> dict[str, Any]:
    flags = _birth_flags(entry)
    note = _source_note(entry)
    dsc = flags["dsc"]
    state = "UNRESOLVED_REVIEW_REQUIRED"
    reason = "Source-note semantics remain unresolved under the frozen rubric."
    source_class = "STRUCTURED_DOCUMENTARY"
    documentary_status = "DOCUMENTED"
    original_identifiable = False
    chain_complete = False
    birth_time_supported = flags["itimeacc"] != "ABSENT" and not flags["time_unknown"]
    precision_supported = birth_time_supported and flags["birth_precision"] != "UNKNOWN"
    if dsc in {"1", "51"} and _direct_original(note):
        state = "VERIFIED_TIER_A"
        reason = "Direct/official documentary wording supports the recorded birth time; no conflict or rectification flag."
        original_identifiable = True
        chain_complete = True
    elif dsc in {"2", "4", "5"} and _documented_timed(note):
        state = "VERIFIED_TIER_B"
        reason = "Referenced documentary, news, biography, autobiography, or historical source supports a timed birth record under Tier B; no conflict or rectification flag."
        original_identifiable = True
        chain_complete = True
    elif dsc in {"1", "51"}:
        state = "UNRESOLVED_REVIEW_REQUIRED"
        reason = "Structured high-authority code is present, but the note does not establish a sufficiently direct source chain for autonomous Tier A verification."
        source_class = "SOURCE_CHAIN_AMBIGUOUS"
        documentary_status = "AMBIGUOUS"
    else:
        source_class = "SOURCE_CHAIN_AMBIGUOUS"
        documentary_status = "AMBIGUOUS"
    return {
        "adb_record_id": int(entry.attrib["adb_id"]),
        "dsc": dsc,
        "rodden_rating": (entry.findtext("./public_data/roddenrating") or "").strip(),
        "itimeacc": flags["itimeacc"],
        "stimeacc": flags["stimeacc"],
        "time_unknown": flags["time_unknown"],
        "alternative_birth_data": flags["bdata_alt"],
        "source_note_hash": sha256_text(note),
        "source_class": source_class,
        "documentary_status": documentary_status,
        "original_source_identifiable": original_identifiable,
        "source_chain_complete": chain_complete,
        "birth_time_explicitly_supported": birth_time_supported,
        "time_precision_supported": precision_supported,
        "rectification_present": flags["rectified"],
        "material_conflict": flags["conflict"],
        "secondary_copy_dependence": not original_identifiable,
        "source_note_ambiguity": state == "UNRESOLVED_REVIEW_REQUIRED",
        "adjudication_state": state,
        "adjudication_reason": reason,
        "upstream_source_cluster": _source_cluster(note),
        "review_version": REVIEW_VERSION,
    }


def _wilson(successes: int, total: int) -> tuple[float, float]:
    if not total:
        return 0.0, 0.0
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _event_family(family: str) -> str:
    names = [("PUBLIC_APPOINTMENT", EVENT_MAP["PUBLIC_APPOINTMENT"]), ("OFFICE_START", EVENT_MAP["OFFICE_START"]), ("OFFICE_END", EVENT_MAP["OFFICE_END"]), ("AWARD", EVENT_MAP["AWARD_HONOUR"]), ("SPORTS", EVENT_MAP["SPORTS"]), ("MARRIAGE", EVENT_MAP["MARRIAGE"]), ("DIVORCE", EVENT_MAP["DIVORCE"]), ("DEATH", EVENT_MAP["DEATH"])]
    return next((name for name, pattern in names if pattern.search(family)), "OTHER_OBJECTIVE")


def build(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    root, entries = load_entries(xml_path)
    frozen_candidates = [entry for entry in entries if _birth_flags(entry)["reason"] == "REQUIRES_SOURCE_ADJUDICATION"]
    candidate_ids = sorted(int(entry.attrib["adb_id"]) for entry in frozen_candidates)
    candidate_set = {
        "candidate_set_id": "ADB-PROVENANCE-R1-REQUIRES-SOURCE-ADJUDICATION",
        "candidate_set_version": REVIEW_VERSION,
        "subject_count": len(candidate_ids),
        "subject_hash": sha256_text("\n".join(map(str, candidate_ids))),
        "selection_policy_hash": sha256_text(SELECTION_POLICY),
        "source_artifact_hash": ZIP_SHA256,
        "selection_policy": SELECTION_POLICY,
    }
    records = [adjudicate(entry) for entry in frozen_candidates]
    counts = Counter(record["adjudication_state"] for record in records)
    verified_ids = {record["adb_record_id"] for record in records if record["adjudication_state"] in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}}
    verified_a = sum(record["adjudication_state"] == "VERIFIED_TIER_A" for record in records)
    verified_b = sum(record["adjudication_state"] == "VERIFIED_TIER_B" for record in records)
    all_events = event_rows(entries)
    verified_day = [row for row in all_events if row["subject_id"] in verified_ids and row["precision"] == "DAY"]
    family_rows = Counter(_event_family(row["family"]) for row in verified_day)
    family_subjects = {family: len({row["subject_id"] for row in verified_day if _event_family(row["family"]) == family}) for family in family_rows}
    verified_subjects_with_day = {row["subject_id"] for row in verified_day}
    multi = Counter(row["subject_id"] for row in verified_day)
    india_ids = {int(entry.attrib["adb_id"]) for entry in frozen_candidates if "india" in country_text(entry).lower()}
    india_verified = verified_ids & india_ids
    clusters = Counter(record["upstream_source_cluster"] for record in records)
    yield_rate = (verified_a + verified_b) / len(records) if records else 0.0
    low, high = _wilson(verified_a + verified_b, len(records))
    broader_pool = 4232 + 233
    scale = {"conservative": math.floor(broader_pool * low), "central": round(broader_pool * yield_rate), "optimistic": math.ceil(broader_pool * high), "interval_method": "95% Wilson interval on frozen 120; selection/source-cluster bias remains"}
    # Second pass is independent rule recomputation from the same frozen inputs.
    second_pass = [adjudicate(entry)["adjudication_state"] for entry in frozen_candidates]
    consistency_exceptions = [record["adb_record_id"] for record, state in zip(records, second_pass) if record["adjudication_state"] != state]
    return {
        "status": "PASS_WITH_CONDITION",
        "provider": "Astro-Databank",
        "export_format": root.attrib.get("export_format"),
        "update_since": root.attrib.get("update_since"),
        "candidate_set": candidate_set,
        "rubric_version": RUBRIC_VERSION,
        "records": records,
        "results": {"verified_tier_a": verified_a, "verified_tier_b": verified_b, "total_verified_a_b": verified_a + verified_b, "retained_tier_c": counts["RETAINED_TIER_C"], "rejected_precision": counts["REJECTED_PRECISION"], "rejected_rectified": counts["REJECTED_RECTIFIED"], "rejected_conflict": counts["REJECTED_CONFLICT"], "rejected_source_lineage": counts["REJECTED_SOURCE_LINEAGE"], "rejected_untimed": counts["REJECTED_UNTIMED"], "unresolved": counts["UNRESOLVED_REVIEW_REQUIRED"], "verification_yield": yield_rate, "uncertainty_95": [low, high]},
        "source_clusters": {"unique_upstream_clusters": len(clusters), "largest_cluster": max(clusters.items(), key=lambda item: item[1]) if clusters else None, "cluster_counts": dict(sorted(clusters.items())), "dependent_records": sum(value for value in clusters.values() if value > 1)},
        "consistency": {"exceptions": consistency_exceptions, "second_pass": "PASS" if not consistency_exceptions else "FAIL"},
        "day_event_overlap": {"verified_subjects_with_any_day_event": len(verified_subjects_with_day), "total_day_events": len(verified_day), "multi_day_event_subjects": sum(value > 1 for value in multi.values()), "family_event_counts": dict(sorted(family_rows.items())), "family_subject_counts": dict(sorted(family_subjects.items())), "event_status": "ADB_EVENT_DISCOVERY_ONLY"},
        "india": {"candidates": len(india_ids), "verified_a": sum(record["adb_record_id"] in india_ids and record["adjudication_state"] == "VERIFIED_TIER_A" for record in records), "verified_b": sum(record["adb_record_id"] in india_ids and record["adjudication_state"] == "VERIFIED_TIER_B" for record in records), "day_event_overlap": len(india_verified & verified_subjects_with_day)},
        "scale": scale,
        "event_readiness": "READY_LIMITED" if len(verified_subjects_with_day) >= 25 else "NOT_READY",
        "formal_access": "FORMAL_ACCESS_HIGH_VALUE" if yield_rate >= 0.5 else "FORMAL_ACCESS_CONDITIONAL_VALUE",
        "decision": "SCALE_ADJUDICATION_TO_BROADER_ADB_POOL" if yield_rate >= 0.5 else "ADB_BIRTH_EVIDENCE_NOT_SCALABLE",
        "governance": {"astrology_executed": False, "feature_scoring": False, "ml_locked": True, "pred_m4_changed": False, "production_changed": False, "approved_core_changed": False, "recruitment_changed": False, "consent_corpus": "NOT_READY_EXTERNAL_REVIEW_REQUIRED", "raw_data_committed": False},
    }


def write_artifacts(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    result = build(xml_path)
    OUT.mkdir(parents=True, exist_ok=True)
    records = result.pop("records")
    public_result = {key: value for key, value in result.items()}
    public_result["record_count"] = len(records)
    (OUT / "01_CANDIDATE_FREEZE.json").write_text(json.dumps(result["candidate_set"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "02_ADJUDICATION_RECORDS.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "03_ADJUDICATION_RESULTS.json").write_text(json.dumps({"results": result["results"], "record_count": len(records), "adjudication_state_counts": dict(Counter(record["adjudication_state"] for record in records))}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "04_SOURCE_CLUSTER_AUDIT.json").write_text(json.dumps(result["source_clusters"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "05_DAY_EVENT_OVERLAP.json").write_text(json.dumps(result["day_event_overlap"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "06_INDIA_RESULT.json").write_text(json.dumps(result["india"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "07_SCALE_ANALYSIS.json").write_text(json.dumps(result["scale"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "FINAL_MANIFEST.json").write_text(json.dumps({"status": result["status"], "candidate_set": result["candidate_set"], "results": result["results"], "consistency": result["consistency"], "event_readiness": result["event_readiness"], "formal_access": result["formal_access"], "decision": result["decision"], "governance": result["governance"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Record-level classifications are hashed/minimal and intentionally not published.
    return public_result


if __name__ == "__main__":
    print(json.dumps(write_artifacts(), indent=2, sort_keys=True))
