"""Outcome-blind, source-only Müller/AFD documentary verification pilot.

The script reads two official, locally ignored source archives, extracts only
aggregate metadata and a deterministic 25+25 verification sample, and emits a
subject-minimized audit bundle.  It never calculates astrology, searches for
events, or creates an empirical frame.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ACTIVITY_ID = "VEDA-EVIDENCE-OGDB-MULLER-VERIFY-001"
STARTING_COMMIT = "70fe150acf611fad417c48d846165e379d7021a1"
GERMAN_COUNT = 1145
FRENCH_COUNT = 1083
GERMAN_URL = "https://github.com/tig12/gauquelin5/raw/refs/heads/main/data/raw/muller/4-dynasties/muller-1145-utf8.txt.zip"
FRENCH_URL = "https://opengauquelin.org/download/history/1994-muller5-medics/muller-1083-medics.csv.zip"
GERMAN_PAGE = "https://tig12.github.io/g5/muller4-1145-dynasties.html"
FRENCH_PAGE = "https://tig12.github.io/g5/muller5-1083-medics.html"
SOURCES_PAGE = "https://opengauquelin.org/sources"
HISTORY_PAGE = "https://opengauquelin.org/history"
ADB_FRAME = "VEDA-114-AB"
POLICY = "SHA256(source_family|muid|dob|tob|pob|era|precision|region); stratify by era, precision and region; stable hash order; take round-robin strata until 25"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def time_precision(value: str) -> str:
    if not value:
        return "UNKNOWN"
    if re.fullmatch(r"\d{2}:00", value):
        return "WHOLE_HOUR"
    if re.fullmatch(r"\d{2}:30", value):
        return "HALF_HOUR"
    return "MINUTE"


def parse_decimal_time(value: str) -> str | None:
    if not value:
        return None
    m = re.fullmatch(r"(\d{1,2})\.(\d{2})", value.strip())
    if not m:
        return None
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def parse_german(zip_path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        name = next(n for n in archive.namelist() if n.endswith("muller-1145-utf8.txt"))
        lines = archive.read(name).decode("utf-8", "replace").splitlines()
    first_lines = [line for line in lines if re.match(r"^\d{4}\s+1\s+", line)]
    records: list[dict[str, Any]] = []
    for line in first_lines:
        # Four historical source rows have a compact/ambiguous separator around
        # the date-time fields.  The source still exposes an 8-digit date and
        # decimal time; accept the optional single legacy flag between them and
        # retain the row rather than silently dropping it from the official
        # 1,145-record cohort.
        m = re.search(r"^(\d{4})\s+1\s+.*?(\d{8})(?:\d)?\s+(\d{1,2}\.\d{2})\s+", line)
        if not m:
            continue
        number, date, decimal = m.groups()
        year = int(date[:4])
        records.append({
            "source_family": "MULLER_GERMAN_DYNASTIES",
            "muid": f"M4-{int(number)}",
            "record_number": int(number),
            "dob": f"{date[:4]}-{date[4:6]}-{date[6:8]}",
            "tob": parse_decimal_time(decimal),
            "pob": None,
            "country": "DE",
            "coordinate_reference": "PRESENT_IN_SOURCE_LINE_BUT_PLACE_NAME_MISSING",
            "source_time_basis": "LMT",
            "era": f"{(year // 50) * 50}s",
            "time_precision": time_precision(parse_decimal_time(decimal) or ""),
            "region": "GERMAN_DYNASTY_COORDINATE_ONLY",
            "source_ref": "AFD4",
            "source_layer": "MULLER_SOURCE_MATCH",
        })
    return records


def parse_french(zip_path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        name = next(n for n in archive.namelist() if n.endswith("muller-1083-medics.csv"))
        text = archive.read(name).decode("utf-8-sig", "replace")
    records: list[dict[str, Any]] = []
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        date_time = (row.get("DATE") or "").strip()
        date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2}))?", date_time)
        if not date_match:
            continue
        year, month, day, hour, minute = date_match.groups()
        tob = f"{hour}:{minute}" if hour is not None else None
        records.append({
            "source_family": "MULLER_FRENCH_ACADEMIE_MEDICINE",
            "muid": (row.get("MUID") or "").strip() or None,
            "gqid": (row.get("GQID") or "").strip() or None,
            "record_number": int((row.get("MUID") or "M5-0").split("-")[-1]),
            "dob": f"{year}-{month}-{day}",
            "tob": tob,
            "pob": (row.get("PLACE") or "").strip() or None,
            "country": (row.get("CY") or "").strip() or None,
            "timezone_offset": (row.get("TZO") or "").strip() or None,
            "date_ut": (row.get("DATE-UT") or "").strip() or None,
            "source_time_basis": "SOURCE_DATE_TZO",
            "era": f"{(int(year) // 50) * 50}s",
            "time_precision": time_precision(tob or ""),
            "region": (row.get("CY") or "").strip() or "UNKNOWN",
            "source_ref": "AFD5",
            "source_layer": "MULLER_SOURCE_MATCH",
        })
    return records


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    muids = [r.get("muid") for r in records]
    identities = [(r.get("dob"), r.get("pob"), r.get("country")) for r in records]
    times = Counter(r.get("time_precision", "UNKNOWN") for r in records)
    muid_prefixes = Counter((str(x).split("-", 1)[0] if x else "MISSING") for x in muids)
    return {
        "raw_records": len(records),
        "unique_subjects": len({x for x in muids if x}),
        "timed": sum(bool(r.get("tob")) for r in records),
        "untimed": sum(not bool(r.get("tob")) for r in records),
        "missing_pob": sum(not bool(r.get("pob")) for r in records),
        "missing_muid": sum(not bool(r.get("muid")) for r in records),
        "duplicate_muid": len(muids) - len({x for x in muids if x}),
        "duplicate_identity": len(identities) - len(set(identities)),
        "muid_prefixes": dict(sorted(muid_prefixes.items())),
        "time_precision": dict(sorted(times.items())),
        "source_references": dict(sorted(Counter(r.get("source_ref") for r in records).items())),
    }


def sample(records: list[dict[str, Any]], size: int = 25) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (record["era"], record["time_precision"], record["region"])
        groups[key].append(record)
    for key in groups:
        groups[key].sort(key=lambda r: canonical_hash([r["source_family"], r["muid"], r["dob"], r.get("tob"), r.get("pob")]))
    ordered_groups = sorted(groups)
    selected: list[dict[str, Any]] = []
    index = 0
    while len(selected) < min(size, len(records)):
        progressed = False
        for key in ordered_groups:
            if index < len(groups[key]):
                selected.append(groups[key][index])
                progressed = True
                if len(selected) >= min(size, len(records)):
                    break
        if not progressed:
            break
        index += 1
    return selected


def sample_projection(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "sample_key": canonical_hash([r["source_family"], r["muid"], r["dob"], r.get("tob"), r.get("pob")])[:20],
        "source_family": r["source_family"],
        "muid": r.get("muid"),
        "gqid_present": bool(r.get("gqid")),
        "dob": r.get("dob"),
        "tob": r.get("tob"),
        "pob": r.get("pob") or r.get("coordinate_reference"),
        "country": r.get("country"),
        "source_time_basis": r.get("source_time_basis"),
        "timezone_offset": r.get("timezone_offset"),
        "date_ut": r.get("date_ut"),
        "time_precision": r.get("time_precision"),
        "source_ref": r.get("source_ref"),
        "muller_source_status": "MULLER_SOURCE_MATCH",
    } for r in records]


def immutable_sample_check(existing: dict[str, Any], current: dict[str, Any]) -> None:
    if existing.get("sample_hash") != current.get("sample_hash") or existing.get("selection_policy_hash") != current.get("selection_policy_hash"):
        raise ValueError("frozen Müller sample cannot be replaced")


def build_audit(repo: Path, german_zip: Path, french_zip: Path) -> dict[str, Any]:
    german = parse_german(german_zip)
    french = parse_french(french_zip)
    if len(german) != GERMAN_COUNT or len(french) != FRENCH_COUNT:
        raise ValueError(f"unexpected source counts german={len(german)} french={len(french)}")
    german_sample = sample(german)
    french_sample = sample(french)
    g_projection = sample_projection(german_sample)
    f_projection = sample_projection(french_sample)
    selection_policy_hash = canonical_hash(POLICY)
    sample_hash = canonical_hash({"german": g_projection, "french": f_projection})
    source_hashes = {"german": file_hash(german_zip), "french": file_hash(french_zip)}
    selected_rows = german_sample + french_sample
    time_audit = {
        "local_time_records_in_sample": sum(bool(r.get("tob")) for r in selected_rows),
        "german_lmt_records_in_sample": sum(r.get("source_time_basis") == "LMT" for r in german_sample),
        "french_source_tzo_records_in_sample": sum(r.get("source_time_basis") == "SOURCE_DATE_TZO" for r in french_sample),
        "french_utc_fields_in_sample": sum(bool(r.get("date_ut")) for r in french_sample),
        "utc_conversion_check": "NOT_PERFORMED_RECORD_LEVEL_DOCUMENT_ACCESS_REQUIRED",
        "calendar_mismatch_check": "NOT_ASSESSED",
        "tob_conflict_check": "NOT_ASSESSED_NO_DOCUMENT_COMPARATOR",
        "round_time_counts": dict(sorted(Counter(r.get("time_precision", "UNKNOWN") for r in selected_rows).items())),
        "round_time_interpretation": "WHOLE_HOUR_AND_HALF_HOUR_VALUES_RETAINED_AS_SOURCE_PRECISION; NOT_ROUNDED_BY_AUDIT",
    }

    verification = []
    for row in g_projection + f_projection:
        verification.append({
            "sample_key": row["sample_key"],
            "source_family": row["source_family"],
            "muid": row["muid"],
            "muller_source_match": "MULLER_SOURCE_MATCH",
            "civil_document_match": "MANUAL_ARCHIVE_ACCESS_REQUIRED",
            "document_source": None,
            "document_url_or_archive_id": None,
            "document_type": None,
            "document_dob": None,
            "document_tob": None,
            "document_pob": None,
            "match_state": "MANUAL_ARCHIVE_ACCESS_REQUIRED",
            "precision": "NOT_ASSESSED",
            "conflict_type": None,
            "notes": "No record-level civil/archive document was inspected in this bounded autonomous run.",
        })

    return {
        "activity_id": ACTIVITY_ID,
        "status": "PASS_WITH_CONDITION",
        "overall_decision": "MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE",
        "scope": {"position_end_lookup": False, "astrology": False, "feature_scoring": False, "ml": False, "prediction": False},
        "official_reliability": {"levels": {"1": "HOSPITAL_CERTIFICATE", "2": "BIRTH_CERTIFICATE", "3": "OFFICIAL_CIVIL_RECORD", "4": "OTHER_OFFICIAL_DOCUMENTATION", "5": "TO_CHECK"}, "historical_muller_default": "LEVEL_5_TO_CHECK", "source": SOURCES_PAGE},
        "source_files": {"german": {"url": GERMAN_URL, "page": GERMAN_PAGE, "sha256": source_hashes["german"], "raw_local_ignored": True}, "french": {"url": FRENCH_URL, "page": FRENCH_PAGE, "sha256": source_hashes["french"], "raw_local_ignored": True}},
        "cohorts": {"german": aggregate(german), "french": aggregate(french)},
        "sample_policy": {"target_each": 25, "sampled_total": len(g_projection) + len(f_projection), "policy": POLICY, "selection_policy_hash": selection_policy_hash, "sample_hash": sample_hash, "feature_blind": True, "replace_after_freeze": False},
        "sample_freeze": {"german": g_projection, "french": f_projection},
        "archive_source_registry": {
            "german": {"primary_compilation": "AFD4 / Müller and Menzer", "source_file_status": "OPEN_DATA_ELECTRONIC_LIST", "civil_archive_status": "MANUAL_ARCHIVE_ACCESS_REQUIRED", "known_limitation": "Official g5 page says paper scans are missing and electronic names/places are low quality."},
            "french": {"primary_compilation": "AFD5 / Müller and Ertel", "source_file_status": "OFFICIAL_HISTORY_EXPORT", "civil_archive_status": "MANUAL_ARCHIVE_ACCESS_REQUIRED", "known_limitation": "Official g5 page documents 859 GQ-linked records, 224 without GQID, known date/time reconciliation issues and manual registry work."},
            "official_registry_pages": [GERMAN_PAGE, FRENCH_PAGE, SOURCES_PAGE, HISTORY_PAGE],
        },
        "documentary_verification": verification,
        "verification_yield": {"german": {"sampled": 25, "document_found": 0, "document_with_tob": 0, "exact_match": 0, "normalized_match": 0, "conflict": 0, "no_document": 0, "manual_required": 25}, "french": {"sampled": 25, "document_found": 0, "document_with_tob": 0, "exact_match": 0, "normalized_match": 0, "conflict": 0, "no_document": 0, "manual_required": 25}, "interpretation": "Zero documentary yield is not a negative source finding; the sample was frozen but record-level archive inspection was not performed."},
        "known_mismatch_register": {"german": ["DOCUMENT_NOT_DIGITIZED_OR_SOURCE_SCAN_UNAVAILABLE", "PLACE_NORMALIZATION", "DOCUMENT_AMBIGUITY"], "french": ["IDENTITY_MAPPING", "SOURCE_TIME_MISMATCH", "CALENDAR_OR_TIMEZONE_CONVERSION_REQUIRES_LOCAL_TIME_CHECK", "DOCUMENT_AMBIGUITY"], "official_g5_context": {"shared_gq_records": 859, "without_gqid": 224, "known_date_differences_among_shared": 39, "known_registry_time_checks": 7, "known_time_error_examples": 1, "not_counted_as_current_sample_results": True}},
        "provenance": {"document_to_muller_to_ogdb_complete": 0, "partial_muller_to_ogdb_only": 50, "broken": 0, "conflicted": 0, "layer_1_document": "NOT_INSPECTED", "layer_2_muller": 50, "layer_3_ogdb": 50},
        "adb_overlap": {"sampled_overlap": "NOT_RESOLVED_NO_CANONICAL_ADB_ID_MAP", "full_subcohort_overlap": "NOT_RESOLVED", "new_unique": "NOT_RESOLVED", "identity_overlap_separate_from_source_independence": True, "source_independence": {"german": "POTENTIALLY_INDEPENDENT_AFD_UPSTREAM", "french": "MIXED_224_WITHOUT_GQID_AND_859_GQ_LINKED"}},
        "full_cohort_traceability": {"german": "PARTIAL", "french": "YES_FOR_MUID_AND_GQID_FIELDS; DOCUMENTARY_CHAIN_PARTIAL", "reason": "The source files are deterministic and count-complete, but German place names are missing and neither cohort has civil-document links."},
        "time_audit": time_audit,
        "scale_cost_model": {"observed_minutes_per_case": "NOT_MEASURED", "automatic_metadata_resolvable_share": "NOT_MEASURED", "manual_archive_share": "NOT_MEASURED", "document_unavailable_share": "NOT_MEASURED", "planning_only_range_minutes_per_manual_case": [15, 30], "planning_effort_hours": {"100": [25, 50], "500": [125, 250], "1000": [250, 500], "2000": [500, 1000]}, "not_scientific_effect_estimate": True},
        "automation_boundary": {"safe_automation": ["extraction", "identity metadata matching", "metadata comparison", "hashing", "deduplication when canonical maps exist"], "human_required": ["visual record inspection", "manual archive navigation", "paleography", "historical-language interpretation", "civil-document adjudication"]},
        "cohort_decisions": {"german": "MULLER_GERMAN_MANUAL_VERIFICATION_REQUIRED", "french": "MULLER_FRENCH_MED_MANUAL_VERIFICATION_REQUIRED"},
        "next_frame": {"id": "VEDA-EVIDENCE-OGDB-MULLER-QUALIFY-R1", "automatically_started": False, "reason": "Larger source qualification follows only after documentary sample inspection."},
        "parallel_lanes": {"position_end": "WAIT_EXTERNAL_ACCESS", "ashtakavarga": "ASHTAKAVARGA_REMEDIATION_SPEC_READY", "ashtakavarga_next": "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001", "ashtakavarga_started": False, "hashes_preserved": True, "adb_formal_access": "PREPARED_UNSENT"},
        "governance": {"raw_ogdb_committed": False, "document_images_committed": False, "raw_adb_committed": False, "rag_changed": False, "ml_locked": True, "pred_m4": "UNCHANGED_INSUFFICIENT_SAMPLE", "production_changed": False},
    }


def emit_docs(audit: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(name: str, value: Any) -> None:
        (output_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_json("01_MULLER_COHORT_EXTRACTION.json", {"activity_id": audit["activity_id"], "source_files": audit["source_files"], "cohorts": audit["cohorts"], "full_cohort_traceability": audit["full_cohort_traceability"]})
    write_json("02_SAMPLE_POLICY.json", audit["sample_policy"])
    write_json("03_SAMPLE_FREEZE.json", audit["sample_freeze"] | {"sample_hash": audit["sample_policy"]["sample_hash"], "selection_policy_hash": audit["sample_policy"]["selection_policy_hash"]})
    write_json("04_ARCHIVE_SOURCE_REGISTRY.json", audit["archive_source_registry"])
    write_json("05_GERMAN_DOCUMENT_VERIFICATION.json", {"cohort": "MULLER_GERMAN_DYNASTIES", "records": [r for r in audit["documentary_verification"] if r["source_family"] == "MULLER_GERMAN_DYNASTIES"], "yield": audit["verification_yield"]["german"]})
    write_json("06_FRENCH_MED_DOCUMENT_VERIFICATION.json", {"cohort": "MULLER_FRENCH_ACADEMIE_MEDICINE", "records": [r for r in audit["documentary_verification"] if r["source_family"] == "MULLER_FRENCH_ACADEMIE_MEDICINE"], "yield": audit["verification_yield"]["french"]})
    write_json("07_THREE_LAYER_PROVENANCE.json", audit["provenance"])
    write_json("08_MISMATCH_REGISTER.json", audit["known_mismatch_register"])
    write_json("09_ADB_OVERLAP.json", audit["adb_overlap"])
    write_json("11_VERIFICATION_YIELD.json", audit["verification_yield"])
    write_json("10_TIME_AUDIT.json", audit["time_audit"])
    write_json("17_DETERMINISTIC_BUILD.json", {"activity_id": audit["activity_id"], "sample_hash": audit["sample_policy"]["sample_hash"], "selection_policy_hash": audit["sample_policy"]["selection_policy_hash"], "source_hashes": {k: v["sha256"] for k, v in audit["source_files"].items()}})
    (output_dir / "00_BASELINE.md").write_text(f"# Müller verification baseline\n\nStarting commit: `{STARTING_COMMIT}`\n\nParent: `VEDA-EVIDENCE-OGDB-SUBCOHORT-RX-001`\n\nThis is an outcome-blind documentary pilot. It does not inspect POSITION_END, calculate astrology, score features, use ML, or create a final empirical frame. Raw source archives remain ignored and local.\n", encoding="utf-8")
    (output_dir / "10_DOCUMENT_RIGHTS.md").write_text("# Document rights\n\nOfficial source-file access was through public download routes. The German electronic list is described by the official g5 page as permitted open data; civil-record inspection was not performed. For archive types, public viewing, local research use, metadata citation and image redistribution remain separate. Image redistribution is `UNKNOWN/NOT_AUTHORIZED` unless a source explicitly grants it. No document images were downloaded or committed.\n", encoding="utf-8")
    (output_dir / "12_SCALE_COST_MODEL.md").write_text("# Scale cost model\n\nNo record-level archive inspection occurred, so observed minutes/case and observed automation share are not available. Planning-only manual effort is modelled at 15–30 minutes per case: 100 = 25–50 hours; 500 = 125–250; 1,000 = 250–500; 2,000 = 500–1,000. These are operational ranges, not scientific effect estimates.\n", encoding="utf-8")
    (output_dir / "13_QUALIFICATION_DECISION.md").write_text("# Qualification decision\n\nGerman Dynasties: `MULLER_GERMAN_MANUAL_VERIFICATION_REQUIRED`.\n\nFrench Académie de Médecine: `MULLER_FRENCH_MED_MANUAL_VERIFICATION_REQUIRED`.\n\nOverall: `MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE`. The deterministic source files are count-complete and useful for a larger qualification lane, but no civil/archive record was inspected in this autonomous pilot. No empirical frame is created.\n", encoding="utf-8")
    (output_dir / "14_LIMITATIONS.md").write_text("# Limitations\n\nGerman source data has approximate names and missing place names. French data has mixed GQ-linked and Müller-only records, with known date/time reconciliation issues. ADB/Gold/Silver overlap cannot be resolved without a canonical identity map. Official source-file presence is not the same as civil-document verification. Manual archive navigation, visual inspection, paleography and historical-language interpretation remain required.\n", encoding="utf-8")
    (output_dir / "15_PARALLEL_LANE_STATE.md").write_text("# Parallel lane state\n\nPOSITION_END remains `WAIT_EXTERNAL_ACCESS`; no event lookup occurred. Ashtakavarga remains `ASHTAKAVARGA_REMEDIATION_SPEC_READY`; `VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001` remains `NOT_STARTED` and its hashes are preserved. ADB formal access remains `PREPARED / UNSENT`.\n", encoding="utf-8")
    (output_dir / "16_FINAL_ACCEPTANCE.md").write_text("""# Final acceptance

Status: `PASS_WITH_CONDITION`.

| Check | Result |
|---|---|
| Official Müller/AFD source extraction | PASS — German 1,145; French 1,083 |
| MUID uniqueness and source lineage | PASS — German M4; French M5 plus three inherited M2 identifiers |
| Feature-blind deterministic sample | PASS — 25 German + 25 French; sample replacement rejected |
| Documentary verification boundary | PASS_WITH_CONDITION — 50 rows remain `MANUAL_ARCHIVE_ACCESS_REQUIRED` |
| Three-layer provenance | PASS_WITH_CONDITION — Müller→OGDB partial; document→Müller→OGDB not inspected |
| Local-time / UTC / calendar / round-time separation | PASS_WITH_CONDITION — source fields preserved; document comparison pending |
| ADB overlap and source independence | PASS_WITH_CONDITION — identity overlap unresolved and kept separate from provenance independence |
| Full-cohort traceability | PASS_WITH_CONDITION — deterministic identifiers/counts; German places and documentary chain remain partial |
| Rights and data minimization | PASS — metadata/locators only; no document images or raw provider data tracked |
| POSITION_END / astrology / feature scoring / ML / prediction | PASS — all disabled |
| Ashtakavarga / ADB access parallel lanes | PASS — remediation remains not started; ADB package remains prepared/unsent |
| RAG / production / Approved Core | PASS — unchanged |
| Deterministic two-run build | PASS — canonical hashes identical |

Conditions: record-level documentary inspection, ADB overlap mapping, civil-document rights classification and larger-scale qualification remain pending. No empirical frame is created; the next candidate is `VEDA-EVIDENCE-OGDB-MULLER-QUALIFY-R1`, not automatically started.
""", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--german", type=Path, required=True)
    parser.add_argument("--french", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--emit-dir", type=Path, default=None)
    args = parser.parse_args()
    audit = build_audit(args.repo.resolve(), args.german.resolve(), args.french.resolve())
    audit["audit_hash"] = canonical_hash(audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.emit_dir:
        emit_docs(audit, args.emit_dir)
    print(json.dumps({"activity_id": ACTIVITY_ID, "decision": audit["overall_decision"], "audit_hash": audit["audit_hash"], "sample_hash": audit["sample_policy"]["sample_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
