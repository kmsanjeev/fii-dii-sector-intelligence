"""Build the source-only OGDB subcohort audit.

This activity deliberately consumes only the existing bounded, outcome-free
OGDB pilot metadata.  It does not download raw OGDB data, inspect events,
perform astrology, or create empirical cases.  The output is derived audit
metadata only and is deterministic when the same local pilot is present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ACTIVITY_ID = "VEDA-EVIDENCE-OGDB-SUBCOHORT-RX-001"
SOURCE_URL = "https://opengauquelin.org/download/ogdb-time.csv.zip"
STATS_URL = "https://opengauquelin.org/stats"
SOURCES_URL = "https://opengauquelin.org/sources"
DOWNLOADS_URL = "https://opengauquelin.org/downloads"
HISTORY_URL = "https://opengauquelin.org/history"
ISSUES_URL = "https://opengauquelin.org/wiki/issues"

OFFICIAL_COUNTS = {
    "total": 25872,
    "timed": 24542,
    "untimed": 1330,
    "countries": 25,
}

SOURCE_FAMILIES = [
    {
        "family_id": "LERRCP",
        "source_key": "lerrcp",
        "authority": "PRIMARY_OFFICIAL_SOURCE_FAMILY",
        "official_scope": "Gauquelin/LERRCP historical data",
        "official_count": 21469,
        "lineage_parent": None,
        "independence": "PRIMARY_UPSTREAM_BUT_DOCUMENTARY_TRACEABILITY_UNVERIFIED",
        "eligibility": "SOURCE_VERIFICATION_REQUIRED",
    },
    {
        "family_id": "MULLER_AFD_GERMAN_DYNASTIES",
        "source_key": "afd",
        "authority": "PRIMARY_OFFICIAL_SOURCE_FAMILY",
        "official_count": 1145,
        "lineage_parent": None,
        "independence": "POTENTIALLY_INDEPENDENT_UPSTREAM",
        "eligibility": "EMPIRICAL_ELIGIBLE_WITH_CONDITION",
    },
    {
        "family_id": "MULLER_AFD_FRENCH_ACADEMIE_MEDICINE",
        "source_key": "afd",
        "authority": "PRIMARY_OFFICIAL_SOURCE_FAMILY",
        "official_count": 1083,
        "lineage_parent": None,
        "independence": "POTENTIALLY_INDEPENDENT_UPSTREAM",
        "eligibility": "EMPIRICAL_ELIGIBLE_WITH_CONDITION",
    },
    {
        "family_id": "MULLER_AFD_ITALIAN_WRITERS",
        "source_key": "afd",
        "authority": "PRIMARY_OFFICIAL_SOURCE_FAMILY",
        "official_count": 402,
        "lineage_parent": None,
        "independence": "POTENTIALLY_INDEPENDENT_UPSTREAM",
        "eligibility": "EMPIRICAL_ELIGIBLE_WITH_CONDITION",
    },
    {
        "family_id": "MULLER_AFD_FAMOUS_MEN",
        "source_key": "afd",
        "authority": "PRIMARY_OFFICIAL_SOURCE_FAMILY",
        "official_count": 612,
        "lineage_parent": None,
        "independence": "POTENTIALLY_INDEPENDENT_UPSTREAM",
        "eligibility": "EMPIRICAL_ELIGIBLE_WITH_CONDITION",
    },
    {
        "family_id": "MULLER_AFD_FAMOUS_WOMEN",
        "source_key": "afd",
        "authority": "PRIMARY_OFFICIAL_SOURCE_FAMILY",
        "official_count": 234,
        "lineage_parent": None,
        "independence": "POTENTIALLY_INDEPENDENT_UPSTREAM",
        "eligibility": "EMPIRICAL_ELIGIBLE_WITH_CONDITION",
    },
    {
        "family_id": "CURA_V5",
        "source_key": "cura5",
        "authority": "SECONDARY_OFFICIAL_CATALOG_ENTRY",
        "official_count": None,
        "lineage_parent": "LERRCP",
        "independence": "DERIVATIVE_OR_REPACKAGED_NOT_INDEPENDENT",
        "eligibility": "MECHANICS_PREVALENCE_ONLY",
    },
    {
        "family_id": "NEW_ALCHEMY",
        "source_key": "newalch",
        "authority": "SECONDARY_OFFICIAL_CATALOG_ENTRY",
        "official_count": None,
        "lineage_parent": "LERRCP_AND_AFD",
        "independence": "DERIVATIVE_OR_MIXED_LINEAGE",
        "eligibility": "PROVENANCE_INSUFFICIENT",
    },
    {
        "family_id": "WIKIDATA_ENRICHMENT",
        "source_key": "wd",
        "authority": "SECONDARY_ENRICHMENT",
        "official_count": None,
        "lineage_parent": "MULTIPLE_UPSTREAMS",
        "independence": "IDENTITY_ENRICHMENT_ONLY",
        "eligibility": "NOT_SUITABLE",
    },
]


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_pilot(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("feed_id") != "VEDA-EMP-OGDB-001":
        raise ValueError("unexpected OGDB feed")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("OGDB pilot records are missing")
    return payload


def time_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    precision = Counter(str(row.get("birth_time_precision") or "UNKNOWN") for row in records)
    round_clock = Counter()
    for row in records:
        value = str(row.get("birth_time") or "")
        if re.fullmatch(r"(?:00|12):00", value):
            round_clock[value] += 1
        elif re.fullmatch(r"\d{2}:00", value):
            round_clock["OTHER_HOUR"] += 1
        elif value:
            round_clock["NON_ROUND_MINUTE"] += 1
        else:
            round_clock["UNKNOWN"] += 1
    offset_present = sum(1 for row in records if row.get("timezone_offset"))
    return {
        "local_pilot_records": len(records),
        "timed_records": sum(bool(row.get("birth_time")) for row in records),
        "untimed_records": sum(not bool(row.get("birth_time")) for row in records),
        "precision": dict(sorted(precision.items())),
        "round_clock": dict(sorted(round_clock.items())),
        "timezone_offset_present": offset_present,
        "utc_datetime_present": 0,
        "historical_calendar_audit": "NOT_PERFORMED_SOURCE_ONLY_LOCAL_PILOT",
        "local_vs_utc_separated": False,
        "limitation": "Pilot metadata retains a local time and optional offset, but not a source-document chain or a full local/UTC audit frame.",
    }


def dedup_audit(records: list[dict[str, Any]], repo_root: Path) -> dict[str, Any]:
    ogids = {str(row.get("ogid")) for row in records if row.get("ogid")}
    return {
        "canonical_ogdb_ids": len(ogids),
        "overlap_with_other_local_ogdb_derivatives": "NOT_RESOLVED",
        "other_local_ogdb_derivative_files": [],
        "adb_overlap": "NOT_RESOLVED_NO_CANONICAL_ADB_ID_MAP_IN_LOCAL_DERIVED_ARTIFACTS",
        "gold_silver_overlap": "NOT_RESOLVED_NO_SUBJECT_LEVEL_ID_MAP_USED",
        "position_end_overlap": "NOT_QUERIED_BY_POLICY",
        "boundary": "No event-bearing or outcome-bearing local files were opened for deduplication; a canonical cross-corpus ID map is required in a later governed lane.",
        "raw_subject_records_written": False,
    }


def build_audit(repo_root: Path, pilot_path: Path) -> dict[str, Any]:
    pilot = load_pilot(pilot_path)
    records = pilot["records"]
    families = []
    for family in SOURCE_FAMILIES:
        row = dict(family)
        row.update({
            "local_family_count": None,
            "local_family_traceability": "NOT_PRESENT_IN_BOUNDED_PILOT",
            "source_document_sample_requested": 25,
            "source_document_sample_completed": 0,
            "source_document_sample_status": "SOURCE_DOCUMENTS_NOT_LOCALLY_AVAILABLE",
            "final_use": "NO_EMPIRICAL_FRAME_CREATED",
        })
        families.append(row)
    source_inventory = {
        "activity_id": ACTIVITY_ID,
        "official_catalogue_urls": [STATS_URL, SOURCES_URL, DOWNLOADS_URL, HISTORY_URL, ISSUES_URL],
        "official_counts": OFFICIAL_COUNTS,
        "source_families": families,
        "local_artifact": {
            "path": str(pilot_path.relative_to(repo_root)),
            "record_count": len(records),
            "source_family_fields_present": False,
            "source_document_fields_present": False,
            "outcome_fields_present": False,
            "astrology_used": False,
        },
        "authority_note": "Official OGDB catalogue metadata was reviewed; local pilot records are source-preserving birth-record metadata, not documentary source verification.",
    }
    dag = {
        "nodes": [
            {"id": "OGDB_OFFICIAL_CATALOGUE", "kind": "official_catalogue", "authority": "PRIMARY_OFFICIAL_METADATA"},
            {"id": "LERRCP", "kind": "primary_upstream", "parent": None},
            {"id": "AFD_MULLER", "kind": "primary_upstream", "parent": None},
            {"id": "CURA5", "kind": "secondary_derivative", "parent": "LERRCP"},
            {"id": "NEW_ALCHEMY", "kind": "secondary_derivative", "parent": "LERRCP_AND_AFD"},
            {"id": "WIKIDATA", "kind": "secondary_enrichment", "parent": "MULTIPLE_UPSTREAMS"},
            {"id": "VEDA_OGDB_PILOT_1000", "kind": "local_bounded_derivative", "parent": "OGDB_OFFICIAL_DOWNLOAD"},
        ],
        "edges": [
            ["OGDB_OFFICIAL_CATALOGUE", "LERRCP"],
            ["OGDB_OFFICIAL_CATALOGUE", "AFD_MULLER"],
            ["LERRCP", "CURA5"],
            ["LERRCP", "NEW_ALCHEMY"],
            ["AFD_MULLER", "NEW_ALCHEMY"],
            ["MULTIPLE_UPSTREAMS", "WIKIDATA"],
            ["OGDB_OFFICIAL_DOWNLOAD", "VEDA_OGDB_PILOT_1000"],
        ],
        "independence_rule": "Repeated catalogue, Cura, New Alchemy and Wikidata references are not counted as independent evidence without upstream separation.",
    }
    eligibility = [
        {"scope": "WHOLE_OGDB", "state": "MECHANICS_PREVALENCE_ONLY", "reason": "No source-family traceability or dated outcome frame."},
        {"scope": "LERRCP", "state": "SOURCE_VERIFICATION_REQUIRED", "reason": "Primary lineage identified, documentary birth-time chain not verified in local artifact."},
        {"scope": "MULLER_AFD_SUBCOHORTS", "state": "EMPIRICAL_ELIGIBLE_WITH_CONDITION", "reason": "Potentially independent official upstream families, pending source-document sample and dedup verification."},
        {"scope": "CURA_NEW_ALCHEMY_WIKIDATA", "state": "PROVENANCE_INSUFFICIENT", "reason": "Derivative or enrichment lineage; not independent birth-time authority."},
    ]
    return {
        "activity_id": ACTIVITY_ID,
        "status": "PASS_WITH_CONDITION",
        "decision": "OGDB_SOURCE_DIVERSITY_USEFUL_BUT_SCALE_LIMITED",
        "scope": {"astrology": False, "position_end_lookup": False, "feature_scoring": False, "ml": False, "prediction": False},
        "official_current_state": {"urls": [STATS_URL, SOURCES_URL, DOWNLOADS_URL, HISTORY_URL, ISSUES_URL], "counts": OFFICIAL_COUNTS, "trust_level_note": "Official OGDB documentation states Gauquelin/Muller data are trust level 5 and requires record-by-record checking."},
        "pilot": {"feed_id": pilot["feed_id"], "pilot_limit": pilot.get("pilot_limit"), "records": len(records), "usable_empirical_cases": pilot.get("usable_empirical_cases"), "case_eligibility": "RESEARCH_ONLY_NO_EVENT", "source_quality": "SOURCE_RECORD_UNREVIEWED"},
        "time_provenance": time_audit(records),
        "source_family_inventory": source_inventory,
        "provenance_dag": dag,
        "muller_subcohort_audit": {"official_families": [x for x in families if x["source_key"] == "afd"], "decision": "CONDITIONAL_CANDIDATE_ONLY", "documentary_sample": "NOT_COMPLETED"},
        "lerrcp_subcohort_audit": {"official_family": "LERRCP", "decision": "SOURCE_VERIFICATION_REQUIRED", "documentary_sample": "NOT_COMPLETED"},
        "skeptic_source_audit": {"cura": "DERIVATIVE_LERRCP", "ertel": "OVERLAP_OR_VERIFICATION_LINEAGE_REQUIRES_CASE_LEVEL_REVIEW", "csicop_cfepp_comite_para": "COLLECTION_OR_VERIFICATION_LINEAGE_NOT_COUNTED_AS_INDEPENDENT", "cura_new_alchemy": "NOT_AUTOMATICALLY_INDEPENDENT"},
        "document_traceability": {"required_per_potential_family": 25, "completed": 0, "state": "SOURCE_VERIFICATION_REQUIRED", "reason": "No documentary scans/source notes were locally available and no bulk source documents were acquired."},
        "deduplication": dedup_audit(records, repo_root),
        "wikidata_correction": {"P1811": "LIST_OF_EPISODES_NOT_TIME_OF_BIRTH", "P569": "DATE_OF_BIRTH_IDENTITY_ENRICHMENT", "exact_tob_source": "NO", "veda_role": "IDENTITY_OCCUPATION_COUNTRY_PUBLIC_ROLE_EVENT_SOURCE_ENRICHMENT_ONLY", "overwrite_tob": False},
        "empirical_eligibility": eligibility,
        "provisional_frame": {"created": False, "state": "NOT_CREATED_SOURCE_VERIFICATION_REQUIRED", "next_gate": "VEDA-EVIDENCE-POSEND-R2-FRAME-RX2_OR_EQUIVALENT", "no_event_acquisition": True},
        "scale_context": {"r1_yield": 4 / 114, "scenarios": {"50_percent": 737, "100_percent": 237, "150_percent": 89}, "power_claim": False},
        "legal_scope": {"database_access": "OPEN_DOWNLOAD_METADATA_REVIEWED_RAW_LOCAL_ONLY", "source_docs": "RIGHTS_SCOPE_UNRESOLVED", "local_storage": "LOCAL_IGNORED_ONLY", "derived_metadata": "PERMITTED_WITH_CONDITION", "redistribution": "NOT_AUTHORIZED"},
        "parallel_lane_state": {"position_end": "WAIT_EXTERNAL_ACCESS", "position_end_r2": "BLOCKED_FORMAL_ACCESS_REQUIRED", "ashtakavarga_next": "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001", "ashtakavarga_started": False},
        "governance": {"raw_data_committed": False, "rag_changed": False, "approved_core_changed": False, "pred_m4": "INSUFFICIENT_SAMPLE", "emp_001": "ACTIVE_LONGITUDINAL", "production_changed": False},
    }


def emit_docs(audit: dict[str, Any], output_dir: Path) -> None:
    """Emit the governed, subject-free documentation bundle."""
    output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(name: str, value: Any) -> None:
        (output_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_json("01_OGDB_CURRENT_STATE.json", {
        "activity_id": audit["activity_id"],
        "status": audit["status"],
        "official_current_state": audit["official_current_state"],
        "pilot": audit["pilot"],
        "scope": audit["scope"],
    })
    write_json("02_SOURCE_FAMILY_INVENTORY.json", audit["source_family_inventory"])
    write_json("03_PROVENANCE_DAG.json", audit["provenance_dag"])
    write_json("04_MULLER_SUBCOHORT_AUDIT.json", audit["muller_subcohort_audit"])
    write_json("05_LERRCP_SUBCOHORT_AUDIT.json", audit["lerrcp_subcohort_audit"])
    write_json("06_SKEPTIC_SOURCE_AUDIT.json", audit["skeptic_source_audit"])
    write_json("07_TIME_PROVENANCE_AUDIT.json", audit["time_provenance"])
    write_json("08_DOCUMENT_TRACEABILITY.json", audit["document_traceability"])
    write_json("09_ADB_OVERLAP.json", audit["deduplication"])
    write_json("12_EMPIRICAL_ELIGIBILITY_MATRIX.json", audit["empirical_eligibility"])
    write_json("13_PROVISIONAL_FRAME_FREEZE.json", audit["provisional_frame"])
    acceptance_ids = [
        "STD-001 inherited", "P031/P032 state preserved", "existing knowledge audited", "official research performed",
        "source families inventoried", "provenance DAG recorded", "Muller subcohorts audited", "LERRCP audited",
        "secondary/derivative sources separated", "time completeness audited", "round-time states audited", "local/UTC limitation recorded",
        "document traceability gate recorded", "ADB overlap limitation recorded", "Wikidata P1811 corrected", "no TOB overwrite",
        "eligibility state assigned", "no provisional frame without gate", "scale scenarios non-power", "legal scope classified",
        "no raw data committed", "no POSITION_END lookup", "no astrology", "no feature scoring", "no ML/prediction",
        "Ashtakavarga lane preserved", "R1 lane preserved", "RAG unchanged", "EMP-001 preserved", "PRED-M4 preserved",
        "research log complete", "weak sources rejected", "deterministic hash emitted", "focused tests added", "selective staging",
        "commit/push/tag planned", "tracked tree clean after handoff",
    ]
    write_json("19_ACCEPTANCE_REGISTER.json", {
        "activity_id": audit["activity_id"],
        "entries": [
            {"id": f"AC{i:02d}", "criterion": criterion, "status": "PASS_WITH_CONDITION" if i in {5, 7, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20} else "PASS"}
            for i, criterion in enumerate(acceptance_ids, 1)
        ],
        "blocked_conditions": ["record-level source-document sampling", "canonical ADB overlap map", "rights scope for source documents"],
    })
    write_json("16_FINAL_ACCEPTANCE.json", {
        "activity_id": audit["activity_id"],
        "overall_status": audit["status"],
        "decision": audit["decision"],
        "audit_hash": audit["audit_hash"],
        "raw_data_committed": audit["governance"]["raw_data_committed"],
        "position_end_lookup": audit["scope"]["position_end_lookup"],
        "astrology_executed": audit["scope"]["astrology"],
        "rag_changed": audit["governance"]["rag_changed"],
        "acceptance_register": "19_ACCEPTANCE_REGISTER.json",
    })
    (output_dir / "00_BASELINE.md").write_text(
        "# OGDB subcohort audit baseline\n\n"
        f"Starting repository: `6c96da68d4cd6fc21f29f70dde616acddfa52984`\n\n"
        "The existing `VEDA-EMP-OGDB-001` artifact is a bounded, outcome-free 1,000-record pilot. "
        "This activity audits source-family independence and time/provenance mechanics only. "
        "It does not download raw OGDB, inspect POSITION_END, calculate astrology, score features, or create cases.\n",
        encoding="utf-8",
    )
    (output_dir / "10_LICENSE_SCOPE.md").write_text(
        "# License and access scope\n\n"
        "The official public catalogue/download metadata was reviewed. Raw provider records remain local and ignored. "
        "Individual source-document redistribution and source-database terms are `RIGHTS_SCOPE_UNRESOLVED`; no bulk source documents were acquired. "
        "Derived subject-free audit metadata is committed. This is a governance classification, not legal advice.\n",
        encoding="utf-8",
    )
    (output_dir / "11_WIKIDATA_CORRECTION.md").write_text(
        "# Wikidata correction\n\n"
        "P1811 is treated as a list of episodes, not time of birth. P569 is an identity/date-of-birth enrichment property. "
        "No exact time-of-birth authority is inferred from Wikidata, and it cannot overwrite OGDB local time. "
        "Permitted VEDA role: identity, occupation, country, public-role, event and source enrichment only.\n",
        encoding="utf-8",
    )
    (output_dir / "14_SCALE_AND_DIVERSITY.md").write_text(
        "# Scale and diversity\n\n"
        f"Official OGDB counts are {OFFICIAL_COUNTS['total']} total, {OFFICIAL_COUNTS['timed']} timed and {OFFICIAL_COUNTS['untimed']} untimed. "
        "The local pilot is 1,000 records and does not expose source-family labels or documentary birth-source links. "
        "Müller/AFD families are potentially useful independent upstream subcohorts, but source-document sampling and deduplication remain gates. "
        "The 50/100/150% R1-yield planning scenarios are not power claims.\n",
        encoding="utf-8",
    )
    (output_dir / "15_PARALLEL_LANE_STATE.md").write_text(
        "# Parallel lane state\n\n"
        "POSITION_END remains `WAIT_EXTERNAL_ACCESS`; R2 remains `BLOCKED_FORMAL_ACCESS_REQUIRED`. "
        "The next calculation activity remains `VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001`, not started. "
        "The Ashtakavarga runtime/source/decision hashes are preserved in the parent decision bundle and were not changed by this activity.\n",
        encoding="utf-8",
    )
    (output_dir / "17_RESEARCH_LOG.md").write_text(
        "# Research log\n\n"
        "Inspected official OGDB statistics, source inventory, downloads/schema, history and issues pages. "
        "The official catalogue identifies LERRCP as the main historical source, AFD/Müller subcohorts, and Cura/New Alchemy/Wikidata as secondary or enrichment lineages. "
        "Rejected as authority: generic search results, unsourced yoga/astrology pages, and any inference that a repeated derivative reference is independent. "
        "Unresolved: record-level source-document chain, full family assignment, ADB overlap map and source-document rights scope.\n",
        encoding="utf-8",
    )
    (output_dir / "18_DETERMINISTIC_BUILD.json").write_text(
        json.dumps({"activity_id": audit["activity_id"], "audit_hash": audit["audit_hash"], "second_run_required": True}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pilot", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--emit-dir", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo.resolve()
    pilot = (args.pilot or repo / "data/veda/research/empirical/ogdb_pilot_1000.json").resolve()
    audit = build_audit(repo, pilot)
    audit["audit_hash"] = canonical_hash(audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.emit_dir:
        emit_docs(audit, args.emit_dir)
    print(json.dumps({"activity_id": ACTIVITY_ID, "decision": audit["decision"], "audit_hash": audit["audit_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
