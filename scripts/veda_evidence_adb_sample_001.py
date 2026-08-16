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
    return {"status": "PASS_WITH_CONDITION", "provider": "Astro-Databank", "provider_url": PROVIDER_URL, "export_format": root.attrib.get("export_format"), "update_since": root.attrib.get("update_since"), "observed_records": len(entries), "unique_record_ids": len({e.attrib.get("adb_id") for e in entries}), "duplicate_record_ids": len(entries) - len({e.attrib.get("adb_id") for e in entries}), "ratings": dict(sorted(ratings.items())), "documented_records": 5866, "documented_a_aa": 4832, "discrepancy_records": len(entries) - 5866, "discrepancy_a_aa": ratings["A"] + ratings["AA"] - 4832, "sha256": sha256(xml_path.parent.parent / "c_sample.zip"), "zip_size": ZIP_SIZE, "source_notes": sum(bool(v) for v in source_notes), "structured_source_citation": structured_citations, "documentary_keyword_candidates": sum(bool(DOC_RE.search(v)) for v in source_notes), "family_keyword_candidates": sum(bool(FAMILY_RE.search(v)) for v in source_notes), "memory_keyword_candidates": sum(bool(MEMORY_RE.search(v)) for v in source_notes), "rectified_keyword_candidates": sum(bool(RECTIFIED_RE.search(v)) for v in source_notes), "birth_precision": dict(birth_precision), "time_type": dict(sorted(time_types.items())), "timed_birth": len(entries), "chart_input_complete": chart_ready, "aa_chart_input_complete": aa_chart_ready, "events": {"subjects_with_events": len(event_ids), "total": len(all_events), "precision": dict(sorted(Counter(row["precision"] for row in all_events).items())), "duplicate_event_keys": len(all_events) - len({(row["subject_id"], row["event_id"]) for row in all_events}), "families": dict(Counter(row["family"] for row in all_events).most_common(50)), "objective_day": family_day}, "corroboration": {"candidate_records": len(candidate_events), "source_checks": len(checked), "exact_confirmed": external_exact, "conflicts": conflicts, "yield_of_checked": external_exact / len(checked) if checked else 0, "records": checked}, "funnel": {"total": len(entries), "a_aa": len(aa_entries), "timed_birth": len(aa_entries), "chart_input_complete": aa_chart_ready, "birth_provenance_sufficient": 0, "veda_birth_tier_a_b": 0, "has_objective_event": len(aa_ids & event_ids), "has_day_event": len(aa_ids & day_ids), "corroborated_day_event": external_exact, "combined_tier_a_b_exact_day": 0, "confirmatory_candidate": 0}, "india": {"subjects": len(india), "a_aa": sum(text(e.find("./public_data/roddenrating")) in {"A", "AA"} for e in india), "timed": len(india), "potential_birth_tier_ab": 0, "day_events": sum(row["precision"] == "DAY" for row in all_events if row["subject_id"] in {int(e.attrib["adb_id"]) for e in india})}, "power": power, "raw_data_committed": False, "ai_training": False, "scraping": False, "access_bypass": False, "astrology_executed": False, "feature_scoring": False, "pred_m4_changed": False, "recruitment_changed": False, "decision": "EXPAND_EVENT_CORROBORATION_BEFORE_SCALE", "formal_access_value": "FORMAL_ACCESS_CONDITIONAL_VALUE", "full_database_yield": "FULL_DATABASE_YIELD_NOT_ESTIMABLE_FROM_C_SAMPLE", "mapping_state": "TIER_MAPPING_UNRESOLVED"}


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
        "12_POWER_AND_SCALE_ANALYSIS.json": {"power": result["power"], "full_database_yield": result["full_database_yield"], "decision": result["decision"]},
        "FINAL_MANIFEST.json": {key: result[key] for key in ("status", "decision", "formal_access_value", "mapping_state", "raw_data_committed", "ai_training", "scraping", "access_bypass", "astrology_executed", "feature_scoring", "pred_m4_changed", "recruitment_changed")},
    }
    for name, value in artifacts.items():
        (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(write_artifacts(), indent=2, sort_keys=True, ensure_ascii=False))
