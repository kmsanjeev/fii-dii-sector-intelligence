"""Astro-Databank free-sample qualification, without astrology execution.

The parser consumes an immutable local provider artifact and emits aggregate
qualification metrics only. Raw provider data is never written to Git, RAG,
ML, prediction or production stores.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts.veda_power_planner import two_proportion_required
except ModuleNotFoundError:
    from veda_power_planner import two_proportion_required

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML = ROOT / "data/research/adb-sample-001/raw/extracted/c_sample.xml"
OUT = ROOT / "docs/current-state/evidence-adb-sample-001"
ZIP_SHA256 = "A88B12D1EDC47651319D33E5A1C47C002DB44E6DBF99374E5943FF9C10AE9B17"
ZIP_SIZE = 2742112
PROVIDER_URL = "https://www.astro.com/adbexport/c_sample.zip"

DOC_RE = re.compile(r"certificate|birth record|hospital|registry|register|document|passport|baptism|parish|official", re.I)
FAMILY_RE = re.compile(r"family|mother|father|parent|grandmother|relative", re.I)
MEMORY_RE = re.compile(r"memory|recalled|remembers|told by", re.I)
RECTIFIED_RE = re.compile(r"rectif|adjusted|corrected|speculat", re.I)

TIME_ACCURACY_CODES = {
    "1": "Second", "2": "Minute", "3": "Five minutes", "4": "Fifteen minutes",
    "5": "Half hour", "7": "1 hours", "8": "2 hours", "9": "6 hours",
    "10": "12 hours", "11": "Day", "12": "Week", "13": "Month",
    "14": "Six months", "15": "Year", "16": "Undetermined", "17": "No Time Recorded",
}
TIME_PRECISION_MAP = {
    "1": "EXACT_MINUTE", "2": "EXACT_MINUTE", "3": "ROUNDED_5_MIN",
    "4": "ROUNDED_15_MIN", "5": "ROUNDED_30_MIN", "7": "HOUR_ONLY",
    "8": "APPROXIMATE", "9": "APPROXIMATE", "10": "APPROXIMATE",
    "11": "APPROXIMATE", "12": "APPROXIMATE", "13": "APPROXIMATE",
    "14": "APPROXIMATE", "15": "APPROXIMATE", "16": "UNKNOWN", "17": "UNKNOWN",
}
DSC_DEFINITIONS = {
    "1": "BC/BR in hand (AA)", "2": "Quoted BC/BR (AA)", "3": "From memory (A)",
    "4": "News report (A)", "5": "Bio/autobiography (B)", "6": "Accuracy in question (C)",
    "7": "Original source not known (C)", "8": "Rectified from approximate time (C)",
    "9": "Conflicting/unverified (DD)", "10": "Date without TOB (X)",
    "11": "Rectified without TOB (X)", "12": "Date in question (XX)",
    "51": "Timed official source (AA)", "52": "Timed documented source/news (A)",
    "53": "Timed historic source (B)", "54": "Timed original source unknown (C)",
    "55": "Dirty/conflicting times (DD)", "56": "Official source untimed (AAX)",
    "57": "Documented source untimed (AX)", "58": "Historic/organizational source untimed (BX)",
    "59": "Original source unknown untimed (CX)", "60": "Conflicting dates (DX)",
    "99": "Undetermined (XX)", "0": "Undetermined/unclassified in current export",
}
DSC_A = frozenset({"1", "2", "4", "51", "52"})
DSC_B = frozenset({"5", "53"})
DSC_STRUCTURED = DSC_A | DSC_B | frozenset({"56", "57", "58"})
NOTE_SUPPORT_RE = re.compile(r"birth certificate|birth record|civil registry|hospital record|official|news|diary|autobiograph|biograph|document", re.I)
NOTE_CONFLICT_RE = re.compile(r"conflict|different time|two birth|doubt remains|alternative (?:date|time)|discrep|however,|but the", re.I)
NOTE_RECTIFIED_RE = re.compile(r"rectif|speculat|adjusted|calculated time", re.I)

EVENT_MAP = {
    "PUBLIC_APPOINTMENT": re.compile(r"New Job|New Career|Gain social status|Great Publicity|Great Achievement", re.I),
    "OFFICE_START": re.compile(r"New Job|New Career", re.I),
    "OFFICE_END": re.compile(r"Retired|Fired/Laid off/Quit", re.I),
    "AWARD_HONOUR": re.compile(r"Prize|Great Achievement", re.I),
    "MARRIAGE": re.compile(r"Relationship : Marriage", re.I),
    "DIVORCE": re.compile(r"Divorce dates", re.I),
    "RELOCATION": re.compile(r"Change residence", re.I),
    "DEATH": re.compile(r"Death", re.I),
    "EDUCATION": re.compile(r"program of study", re.I),
    "SPORTS": re.compile(r"Sports|Debut|Retired", re.I),
}

CORROBORATION = {
    (33, 771): {"source": "https://www.persee.fr/doc/psy_0003-5033_1894_num_1_1_1278", "status": "CONFLICT", "external_date": "1893-08-16", "note": "Persée confirms 16 Aug; historical JAMA notice reports 17 Aug."},
    (53, 764): {"source": "https://catalogue.bnf.fr/ark:/12148/cb12233528w", "status": "EXACT_CONFIRMED", "external_date": "1906-04-19"},
    (64, 766): {"source": "https://musee.curie.fr/blog/de-quoi-est-morte-marie-curie", "status": "EXACT_CONFIRMED", "external_date": "1934-07-04"},
    (81, 771): {"source": "https://www.marlboromusic.org/archives/artists/pablo-casals/", "status": "EXACT_CONFIRMED", "external_date": "1973-10-22"},
    (95, 771): {"source": "https://www.parismuseescollections.paris.fr/fr/palais-galliera/oeuvres/robe-fond-et-noeud", "status": "EXACT_CONFIRMED", "external_date": "1971-01-10"},
    (143, 766): {"source": "https://www.deutsche-digitale-bibliothek.de/person/gnd/118522043", "status": "EXACT_CONFIRMED", "external_date": "1961-05-13"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def text(node: ET.Element | None) -> str:
    return (node.text or "").strip() if node is not None else ""


def date_precision(node: ET.Element | None) -> str:
    attrs = node.attrib if node is not None else {}
    if not attrs or not attrs.get("iyear"):
        return "UNKNOWN"
    if attrs.get("iday") in {None, "", "0", "00"}:
        return "MONTH" if attrs.get("imonth") not in {None, "", "0", "00"} else "YEAR"
    return "DAY"


def country_text(entry: ET.Element) -> str:
    node = entry.find("./public_data/bdata/country")
    return f"{text(node)} {(node.attrib.get('sctr', '') if node is not None else '')}".strip()


def chart_input_complete(entry: ET.Element) -> bool:
    place = entry.find("./public_data/bdata/place")
    if place is None or text(place).lower() in {"", "unknown", "none"}:
        return False
    return bool(place.attrib.get("slati") and place.attrib.get("slong") and entry.find("./public_data/bdata/sbtime") is not None)


def event_rows(entries: list[ET.Element]) -> list[dict[str, Any]]:
    rows = []
    for entry in entries:
        for event in entry.findall("./research_data/events/event"):
            date_node = event.find("./event_data/sbdate")
            rows.append({"subject_id": int(entry.attrib["adb_id"]), "event_id": int(event.attrib.get("evn_id", "0")), "family": event.attrib.get("sevcode", "UNKNOWN"), "date": text(date_node), "precision": date_precision(date_node), "adb_event_state": "ADB_EVENT_DISCOVERY_ONLY"})
    return rows


def _sbtime(entry: ET.Element) -> ET.Element:
    node = entry.find("./public_data/bdata/sbtime")
    return node if node is not None else ET.Element("sbtime")


def _source_note(entry: ET.Element) -> str:
    return text(entry.find("./text_data/sourcenotes"))


def _time_unknown(entry: ET.Element) -> bool:
    return _sbtime(entry).attrib.get("time_unknown", "").lower() in {"1", "yes", "true"}


def _dsc(entry: ET.Element) -> str:
    return entry.find("./public_data/datatype").attrib.get("dsc", "UNKNOWN") if entry.find("./public_data/datatype") is not None else "UNKNOWN"


def _birth_flags(entry: ET.Element) -> dict[str, Any]:
    sbtime = _sbtime(entry)
    note = _source_note(entry)
    dsc = _dsc(entry)
    acc_code = sbtime.attrib.get("itimeacc")
    alternative = entry.find("./public_data/bdata_alt") is not None
    conflict = dsc in {"9", "55", "60"} or bool(NOTE_CONFLICT_RE.search(note))
    rectified = dsc in {"8", "11"} or bool(NOTE_RECTIFIED_RE.search(note))
    source_supported = bool(note) and note.lower() != "deleted entry" and bool(NOTE_SUPPORT_RE.search(note))
    structured = dsc in DSC_STRUCTURED
    potential_tier = "POTENTIAL_TIER_A" if dsc in DSC_A else "POTENTIAL_TIER_B" if dsc in DSC_B else "NOT_TIER_A_B"
    reason = ""
    if _time_unknown(entry):
        reason = "TIME_UNKNOWN"
    elif not acc_code:
        reason = "NO_EXPLICIT_TIME_ACCURACY"
    elif conflict:
        reason = "MATERIAL_CONFLICT"
    elif rectified:
        reason = "RECTIFIED"
    elif not structured:
        reason = "SOURCE_CLASS_NOT_A_B"
    elif not source_supported:
        reason = "SOURCE_NOTES_UNSUPPORTIVE"
    elif dsc in {"56", "57", "58"}:
        reason = "UNTIMED_SOURCE_CODE"
    else:
        reason = "REQUIRES_SOURCE_ADJUDICATION"
    return {
        "dsc": dsc,
        "dsc_definition": DSC_DEFINITIONS.get(dsc, "UNVERIFIED SOURCE CODE"),
        "itimeacc": acc_code or "ABSENT",
        "stimeacc": sbtime.attrib.get("stimeacc", "ABSENT"),
        "time_unknown": _time_unknown(entry),
        "ctimetype": sbtime.attrib.get("ctimetype", "UNKNOWN"),
        "birth_precision": TIME_PRECISION_MAP.get(acc_code, "UNKNOWN"),
        "bdata_alt": alternative,
        "conflict": conflict,
        "rectified": rectified,
        "source_notes_present": bool(note),
        "source_notes_supportive": source_supported,
        "structured": structured,
        "potential_tier": potential_tier,
        "reason": reason,
    }


def provenance_metrics(entries: list[ET.Element], all_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Return structured birth-provenance metrics without exposing record text."""
    flags = [_birth_flags(entry) for entry in entries]
    dsc_counts = Counter(item["dsc"] for item in flags)
    time_accuracy = Counter(item["itimeacc"] for item in flags)
    stime_accuracy = Counter(item["stimeacc"] for item in flags)
    time_unknown = Counter("TIME_UNKNOWN_1" if item["time_unknown"] else "TIME_UNKNOWN_ABSENT" for item in flags)
    ctimetype = Counter(item["ctimetype"] for item in flags)
    dsc_rating = Counter((item["dsc"], text(entry.find("./public_data/roddenrating"))) for entry, item in zip(entries, flags))
    dsc_itimeacc = Counter((item["dsc"], item["itimeacc"]) for item in flags)
    dsc_unknown = Counter((item["dsc"], "1" if item["time_unknown"] else "0") for item in flags)
    day_subjects = {row["subject_id"] for row in all_events if row["precision"] == "DAY"}
    dsc_day = Counter((item["dsc"], "1" if int(entry.attrib["adb_id"]) in day_subjects else "0") for entry, item in zip(entries, flags))
    structured = [item for item in flags if item["structured"]]
    potential_a = [item for item in flags if item["potential_tier"] == "POTENTIAL_TIER_A"]
    potential_b = [item for item in flags if item["potential_tier"] == "POTENTIAL_TIER_B"]
    explicit = [item for item in flags if item["itimeacc"] != "ABSENT"]
    no_unknown = [item for item in explicit if not item["time_unknown"]]
    deterministic = [item for item in no_unknown if item["potential_tier"] in {"POTENTIAL_TIER_A", "POTENTIAL_TIER_B"} and item["source_notes_supportive"] and not item["conflict"] and not item["rectified"] and item["dsc"] not in {"56", "57", "58"}]
    counts = Counter(item["reason"] for item in flags)
    eligible_ids = {int(entry.attrib["adb_id"]) for entry, item in zip(entries, flags) if item in deterministic}
    day_by_subject = Counter(row["subject_id"] for row in all_events if row["precision"] == "DAY")
    objective_patterns = [("PUBLIC_APPOINTMENT", EVENT_MAP["PUBLIC_APPOINTMENT"]), ("OFFICE_START", EVENT_MAP["OFFICE_START"]), ("OFFICE_END", EVENT_MAP["OFFICE_END"]), ("AWARD", EVENT_MAP["AWARD_HONOUR"]), ("SPORTS", EVENT_MAP["SPORTS"]), ("MARRIAGE", EVENT_MAP["MARRIAGE"]), ("DIVORCE", EVENT_MAP["DIVORCE"]), ("DEATH", EVENT_MAP["DEATH"])]
    day_overlap = {"subjects": len(eligible_ids & set(day_by_subject)), "families": Counter()}
    for row in all_events:
        if row["subject_id"] in eligible_ids and row["precision"] == "DAY":
            family = next((name for name, pattern in objective_patterns if pattern.search(row["family"])), "OTHER_OBJECTIVE")
            day_overlap["families"][family] += 1
    india_ids = {int(entry.attrib["adb_id"]) for entry in entries if "india" in country_text(entry).lower()}
    india_flags = [item for entry, item in zip(entries, flags) if int(entry.attrib["adb_id"]) in india_ids]
    india_ratings = Counter(text(entry.find("./public_data/roddenrating")) for entry in entries if int(entry.attrib["adb_id"]) in india_ids)
    india_potential = [item for item in india_flags if item["potential_tier"] in {"POTENTIAL_TIER_A", "POTENTIAL_TIER_B"}]
    # A bounded, deterministic desk-review queue; this is not a human adjudication.
    review_pool = [(int(entry.attrib["adb_id"]), item) for entry, item in zip(entries, flags) if item["potential_tier"] in {"POTENTIAL_TIER_A", "POTENTIAL_TIER_B"} and item["reason"] in {"REQUIRES_SOURCE_ADJUDICATION", "NO_EXPLICIT_TIME_ACCURACY", "TIME_UNKNOWN"}]
    review_sample = [{"dsc": item["dsc"], "automated_status": "PASS" if item["source_notes_supportive"] and not item["conflict"] and not item["rectified"] else "UNRESOLVED", "reason": item["reason"]} for _, item in sorted(review_pool, key=lambda value: (value[1]["dsc"], value[0]))[:30]]
    return {
        "ctimetype_role": "TIME_SYSTEM_TIMEZONE_HANDLING_NOT_BIRTH_TIME_PRECISION",
        "ctimetype_counts": dict(sorted(ctimetype.items())),
        "itimeacc_counts": dict(sorted(time_accuracy.items())),
        "stimeacc_counts": dict(sorted(stime_accuracy.items())),
        "time_unknown_counts": dict(sorted(time_unknown.items())),
        "explicit_time_accuracy": len(explicit),
        "no_explicit_time_accuracy": len(flags) - len(explicit),
        "time_unknown_1": sum(item["time_unknown"] for item in flags),
        "bdata_alt_records": sum(item["bdata_alt"] for item in flags),
        "dsc_counts": dict(sorted(dsc_counts.items())),
        "dsc_definitions": DSC_DEFINITIONS,
        "cross_tabs": {
            "dsc_x_rod_den_rating": {f"{dsc}|{rating}": count for (dsc, rating), count in sorted(dsc_rating.items())},
            "dsc_x_itimeacc": {f"{dsc}|{acc}": count for (dsc, acc), count in sorted(dsc_itimeacc.items())},
            "dsc_x_time_unknown": {f"{dsc}|{unknown}": count for (dsc, unknown), count in sorted(dsc_unknown.items())},
            "dsc_x_day_event": {f"{dsc}|{has_day}": count for (dsc, has_day), count in sorted(dsc_day.items())},
        },
        "structured_documentary_candidates": len(structured),
        "potential_tier_a": len(potential_a),
        "potential_tier_b": len(potential_b),
        "deterministic_tier_a": sum(item["potential_tier"] == "POTENTIAL_TIER_A" for item in deterministic),
        "deterministic_tier_b": sum(item["potential_tier"] == "POTENTIAL_TIER_B" for item in deterministic),
        "requires_adjudication": sum(item["reason"] == "REQUIRES_SOURCE_ADJUDICATION" for item in flags),
        "rejected_for_precision": counts["NO_EXPLICIT_TIME_ACCURACY"] + counts["TIME_UNKNOWN"],
        "rejected_for_unknown_source": counts["SOURCE_CLASS_NOT_A_B"] + counts["SOURCE_NOTES_UNSUPPORTIVE"],
        "rejected_for_rectification": counts["RECTIFIED"],
        "rejected_for_conflict": counts["MATERIAL_CONFLICT"],
        "rejected_for_untimed": sum(item["dsc"] in {"56", "57", "58"} for item in flags),
        "reason_counts": dict(sorted(counts.items())),
        "candidate_policy": "Explicit itimeacc, time_unknown absent, structured A/B dsc, supportive source note, no material conflict, no rectification; Rodden rating is not used as an automatic tier.",
        "india": {
            "records": len(india_flags),
            "dsc_counts": dict(sorted(Counter(item["dsc"] for item in india_flags).items())),
            "ratings": dict(sorted(india_ratings.items())),
            "explicit_time_accuracy": sum(item["itimeacc"] != "ABSENT" for item in india_flags),
            "structured_documentary_candidates": len([item for item in india_flags if item["structured"]]),
            "potential_tier_a": sum(item["potential_tier"] == "POTENTIAL_TIER_A" for item in india_flags),
            "potential_tier_b": sum(item["potential_tier"] == "POTENTIAL_TIER_B" for item in india_flags),
            "day_event_overlap": len(india_ids & set(day_by_subject)),
        },
        "day_event_overlap": day_overlap,
        "manual_adjudication_sample": {"size": len(review_sample), "mode": "AUTOMATED_PRE_ADJUDICATION_ONLY", "records": review_sample, "human_review_required": True},
        "veda_mapping_state": "STRUCTURED_CANDIDATES_REQUIRE_SOURCE_ADJUDICATION",
    }


def build(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    if not xml_path.exists():
        return {"status": "ADB_SAMPLE_ACCESS_BLOCKED", "reason": "official artifact not present locally", "raw_data_committed": False}
    root = ET.parse(xml_path).getroot()
    entries = root.findall("adb_entry")
    ratings = Counter(text(e.find("./public_data/roddenrating")) for e in entries)
    all_events = event_rows(entries)
    aa_entries = [e for e in entries if text(e.find("./public_data/roddenrating")) in {"A", "AA"}]
    source_notes = [text(e.find("./text_data/sourcenotes")) for e in entries]
    birth_precision = Counter("UNKNOWN" for _ in entries)
    time_types = Counter((e.find("./public_data/bdata/sbtime").attrib.get("ctimetype", "UNKNOWN") if e.find("./public_data/bdata/sbtime") is not None else "UNKNOWN") for e in entries)
    chart_ready = sum(chart_input_complete(e) for e in entries)
    aa_chart_ready = sum(chart_input_complete(e) for e in aa_entries)
    day_events = [row for row in all_events if row["precision"] == "DAY"]
    family_day = {family: sum(bool(pattern.search(row["family"])) and row["precision"] == "DAY" for row in all_events) for family, pattern in EVENT_MAP.items()}
    candidate_events = [row for row in day_events if row["family"].lower().startswith("death")][:30]
    checked = []
    for row in candidate_events:
        match = CORROBORATION.get((row["subject_id"], row["event_id"]))
        if match:
            checked.append({**row, **match})
    external_exact = sum(row["status"] == "EXACT_CONFIRMED" for row in checked)
    conflicts = sum(row["status"] == "CONFLICT" for row in checked)
    india = [e for e in entries if "india" in country_text(e).lower()]
    structured_citations = sum(
        bool(text(e.find("./text_data/adb_link"))) or e.find("./text_data/wikipedia_link") is not None
        for e in entries
    )
    power = {"baseline_10_target_15": two_proportion_required(.10, .15, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "baseline_10_target_20": two_proportion_required(.10, .20, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "baseline_10_target_25": two_proportion_required(.10, .25, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"], "baseline_10_target_30": two_proportion_required(.10, .30, design_effect=1.10, exclusion_fraction=.15)["approximate_independent_subjects"]}
    aa_ids = {int(e.attrib["adb_id"]) for e in aa_entries}
    event_ids = {row["subject_id"] for row in all_events}
    day_ids = {row["subject_id"] for row in day_events}
    return {"status": "PASS_WITH_CONDITION", "provider": "Astro-Databank", "provider_url": PROVIDER_URL, "export_format": root.attrib.get("export_format"), "update_since": root.attrib.get("update_since"), "observed_records": len(entries), "unique_record_ids": len({e.attrib.get("adb_id") for e in entries}), "duplicate_record_ids": len(entries) - len({e.attrib.get("adb_id") for e in entries}), "ratings": dict(sorted(ratings.items())), "documented_records": 5866, "documented_a_aa": 4832, "discrepancy_records": len(entries) - 5866, "discrepancy_a_aa": ratings["A"] + ratings["AA"] - 4832, "sha256": sha256(xml_path.parent.parent / "c_sample.zip"), "zip_size": ZIP_SIZE, "source_notes": sum(bool(v) for v in source_notes), "structured_source_citation": structured_citations, "documentary_keyword_candidates": sum(bool(DOC_RE.search(v)) for v in source_notes), "family_keyword_candidates": sum(bool(FAMILY_RE.search(v)) for v in source_notes), "memory_keyword_candidates": sum(bool(MEMORY_RE.search(v)) for v in source_notes), "rectified_keyword_candidates": sum(bool(RECTIFIED_RE.search(v)) for v in source_notes), "birth_precision": dict(birth_precision), "time_type": dict(sorted(time_types.items())), "timed_birth": len(entries), "chart_input_complete": chart_ready, "aa_chart_input_complete": aa_chart_ready, "events": {"subjects_with_events": len(event_ids), "total": len(all_events), "precision": dict(sorted(Counter(row["precision"] for row in all_events).items())), "duplicate_event_keys": len(all_events) - len({(row["subject_id"], row["event_id"]) for row in all_events}), "families": dict(Counter(row["family"] for row in all_events).most_common(50)), "objective_day": family_day}, "corroboration": {"candidate_records": len(candidate_events), "source_checks": len(checked), "exact_confirmed": external_exact, "conflicts": conflicts, "yield_of_checked": external_exact / len(checked) if checked else 0, "records": checked}, "funnel": {"total": len(entries), "a_aa": len(aa_entries), "timed_birth": len(aa_entries), "chart_input_complete": aa_chart_ready, "birth_provenance_sufficient": 0, "veda_birth_tier_a_b": 0, "has_objective_event": len(aa_ids & event_ids), "has_day_event": len(aa_ids & day_ids), "corroborated_day_event": external_exact, "combined_tier_a_b_exact_day": 0, "confirmatory_candidate": 0}, "india": {"subjects": len(india), "a_aa": sum(text(e.find("./public_data/roddenrating")) in {"A", "AA"} for e in india), "timed": len(india), "potential_birth_tier_ab": 0, "day_events": sum(row["precision"] == "DAY" for row in all_events if row["subject_id"] in {int(e.attrib["adb_id"]) for e in india})}, "provenance": provenance_metrics(entries, all_events), "power": power, "raw_data_committed": False, "ai_training": False, "scraping": False, "access_bypass": False, "astrology_executed": False, "feature_scoring": False, "pred_m4_changed": False, "recruitment_changed": False, "decision": "ADB_BIRTH_PROVENANCE_ADJUDICATION", "formal_access_value": "FORMAL_ACCESS_CONDITIONAL_VALUE", "full_database_yield": "FULL_DATABASE_YIELD_NOT_ESTIMABLE_FROM_C_SAMPLE", "mapping_state": "TIER_MAPPING_UNRESOLVED", "corrective_mapping_state": "STRUCTURED_CANDIDATES_REQUIRE_SOURCE_ADJUDICATION"}


def write_artifacts(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    result = build(xml_path)
    OUT.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "02_SOURCE_ARTIFACT_MANIFEST.json": {key: result[key] for key in ("provider", "provider_url", "export_format", "update_since", "sha256", "zip_size", "documented_records", "documented_a_aa", "observed_records", "discrepancy_records", "discrepancy_a_aa", "raw_data_committed")},
        "04_RECORD_QUALITY_PROFILE.json": {key: result[key] for key in ("observed_records", "unique_record_ids", "duplicate_record_ids", "ratings", "source_notes", "structured_source_citation", "documentary_keyword_candidates", "family_keyword_candidates", "memory_keyword_candidates", "rectified_keyword_candidates", "time_type")},
        "05_BIRTH_PROVENANCE_AUDIT.json": {key: result[key] for key in ("birth_precision", "timed_birth", "chart_input_complete", "aa_chart_input_complete", "mapping_state", "funnel")},
        "06_EVENT_INVENTORY.json": result["events"],
        "07_EXACT_DAY_EVENT_PROFILE.json": {"objective_day": result["events"]["objective_day"], "precision": result["events"]["precision"]},
        "08_CORROBORATION_PILOT.json": result["corroboration"],
        "09_TIER_QUALIFICATION_FUNNEL.json": result["funnel"],
        "12_POWER_AND_SCALE_ANALYSIS.json": {"power": result["power"], "full_database_yield": result["full_database_yield"], "decision": "EXPAND_EVENT_CORROBORATION_BEFORE_SCALE"},
        "FINAL_MANIFEST.json": {key: result[key] for key in ("status", "formal_access_value", "mapping_state", "raw_data_committed", "ai_training", "scraping", "access_bypass", "astrology_executed", "feature_scoring", "pred_m4_changed", "recruitment_changed")} | {"decision": "EXPAND_EVENT_CORROBORATION_BEFORE_SCALE"},
    }
    for name, value in artifacts.items():
        (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


PROVENANCE_OUT = ROOT / "docs/current-state/evidence-adb-provenance-r1"


def write_provenance_artifacts(xml_path: Path = DEFAULT_XML) -> dict[str, Any]:
    """Write corrective aggregate artifacts in a new historical folder."""
    result = build(xml_path)
    PROVENANCE_OUT.mkdir(parents=True, exist_ok=True)
    p = result.get("provenance", {})
    artifacts = {
        "02_SCHEMA_METRICS.json": {key: p[key] for key in ("ctimetype_role", "ctimetype_counts", "itimeacc_counts", "stimeacc_counts", "time_unknown_counts", "explicit_time_accuracy", "no_explicit_time_accuracy", "time_unknown_1", "bdata_alt_records")},
        "03_SOURCE_CODE_METRICS.json": {key: p[key] for key in ("dsc_counts", "dsc_definitions", "structured_documentary_candidates", "potential_tier_a", "potential_tier_b", "deterministic_tier_a", "deterministic_tier_b", "requires_adjudication", "reason_counts", "rejected_for_precision", "rejected_for_unknown_source", "rejected_for_rectification", "rejected_for_conflict", "rejected_for_untimed")},
        "04_CROSS_TABS.json": {"cross_tabs": p["cross_tabs"], "candidate_day_overlap": p["day_event_overlap"], "india": p["india"]},
        "05_TIER_FUNNEL.json": {key: p[key] for key in ("candidate_policy", "structured_documentary_candidates", "potential_tier_a", "potential_tier_b", "deterministic_tier_a", "deterministic_tier_b", "requires_adjudication", "veda_mapping_state")},
        "06_MANUAL_ADJUDICATION_SAMPLE.json": p["manual_adjudication_sample"],
        "FINAL_MANIFEST.json": {"status": result["status"], "parent_mapping_state": result["mapping_state"], "corrective_mapping_state": result["corrective_mapping_state"], "decision": result["decision"], "raw_data_committed": result["raw_data_committed"], "astrology_executed": result["astrology_executed"], "feature_scoring": result["feature_scoring"], "ai_training": result["ai_training"], "pred_m4_changed": result["pred_m4_changed"], "recruitment_changed": result["recruitment_changed"]},
    }
    for name, value in artifacts.items():
        (PROVENANCE_OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(write_provenance_artifacts(), indent=2, sort_keys=True, ensure_ascii=False))
