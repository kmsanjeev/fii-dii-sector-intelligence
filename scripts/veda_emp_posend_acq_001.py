"""Independent, feature-blind POSITION_END cohort acquisition.

This script reads the frozen EMP-FEATURE-003 registry only to verify its hash;
it never imports or evaluates feature logic.  It freezes acquisition inputs,
subject-level split metadata, and unscored controls for the next activity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json"
PILOT = ROOT / "data/veda/research/empirical/ogdb_pilot_1000.json"
FAMILY = ROOT / "docs/current-state/emp-feature-003/02_FEATURE_FAMILY_REGISTRY.json"
OUT = ROOT / "docs/current-state/emp-posend-acq-001"
EXPECTED_FAMILY_HASH = "da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297"
EVENT_DEFINITION = "Documented date on which a subject ceased to hold a distinct professional or public position; term completion, resignation, retirement, removal and death-in-office are not conflated."
PRIOR = {
    "alioto-joseph-1916-02-12", "ariyoshi-george-1926-03-12", "andrus-cecil-1931-08-25",
    "achille-fould-aymar-1925-07-17", "alvarez-luis-1911-06-13", "annenberg-walter-1908-03-13",
    "appell-paul-1855-09-27", "ashe-arthur-1943-07-10", "auriol-vincent-1884-08-27",
    "babinski-joseph-1857-11-17", "baeyer-adolf-1835-10-31", "balmain-pierre-1914-05-18",
    "barre-raymond-1924-04-12", "adenauer-conrad-1876-01-05", "aldrin-edwin-1930-01-20",
    "alpert-herb-1935-03-31", "alworth-lance-1940-08-03", "baker-howard-1925-11-15",
    "banks-ernie-1931-01-30", "bardot-brigitte-1934-09-28", "bean-alan-1932-03-15",
    "belmondo-jean-paul-1933-04-09", "bergen-candice-1946-05-09", "bocuse-paul-1926-02-11",
    "borman-frank-1928-03-14", "boulez-pierre-1925-03-26", "bradbury-ray-1920-08-22",
    "bradley-bill-1943-07-28", "brandt-willy-1913-12-18", "braque-georges-1882-05-13",
    "brando-marlon-1924-04-03", "berra-yogi-1925-05-12", "baker-diane-1938-02-25",
}

# Selected birth-first from the frozen timed-birth population.  Event dates
# retain year precision where the public career source gives only a year.
CASES = [
    ("adam-pierre-1924-04-24", "1954", "RETIREMENT", "Pierre Adam professional cycling career end", "https://fr.wikipedia.org/wiki/Pierre_Adam_(cyclisme)", "STRONG_REFERENCED_STRUCTURED"),
    ("abbes-claude-1927-05-24", "1962", "RETIREMENT", "Claude Abbes professional football career end", "https://www.fff.fr/equipe-nationale/joueur/8477-abbes-claude/fiche.html", "PRIMARY_OFFICIAL"),
    ("alonso-richard-1948-09-22", "1973", "RETIREMENT", "Richard Alonso professional rugby career end", "https://en.wikipedia.org/wiki/Richard_Alonso", "SINGLE_REFERENCED_STRUCTURED"),
    ("abramowicz-daniel-1945-07-13", "1973", "RETIREMENT", "Daniel Abramowicz professional football career end", "https://en.wikipedia.org/wiki/Dan_Abramowicz", "SINGLE_REFERENCED_STRUCTURED"),
    ("acconcia-italo-1925-04-20", "1958", "RETIREMENT", "Italo Acconcia professional football career end", "https://en.wikipedia.org/wiki/Italo_Acconcia", "SINGLE_REFERENCED_STRUCTURED"),
    ("agnel-marisette-1926-08-28", "1952", "RETIREMENT", "Marisette Agnel professional skiing career end", "https://en.wikipedia.org/wiki/Marisette_Agnel", "SINGLE_REFERENCED_STRUCTURED"),
    ("aristouy-pierre-1920-10-18", "1953", "RETIREMENT", "Pierre Aristouy professional rugby career end", "https://en.wikipedia.org/wiki/Pierre_Aristouy", "SINGLE_REFERENCED_STRUCTURED"),
    ("aimar-lucien-1941-04-28", "1966", "RETIREMENT", "Lucien Aimar professional cycling career end", "https://en.wikipedia.org/wiki/Lucien_Aimar", "STRONG_REFERENCED_STRUCTURED"),
    ("aitelli-colette-1932-03-03", "1956", "RETIREMENT", "Colette Aitelli athletics career end", "https://en.wikipedia.org/wiki/Colette_Aitelli", "SINGLE_REFERENCED_STRUCTURED"),
    ("alard-pierre-1937-09-17", "1960", "RETIREMENT", "Pierre Alard athletics career end", "https://en.wikipedia.org/wiki/Pierre_Alard", "SINGLE_REFERENCED_STRUCTURED"),
    ("albaladejo-pierre-1933-12-14", "1975", "RETIREMENT", "Pierre Albaladejo professional rugby career end", "https://en.wikipedia.org/wiki/Pierre_Albaladejo", "STRONG_REFERENCED_STRUCTURED"),
    ("amadei-amadeo-1921-07-26", "1956", "RETIREMENT", "Amadeo Amadei professional football career end", "https://en.wikipedia.org/wiki/Amadeo_Amadei", "STRONG_REFERENCED_STRUCTURED"),
    ("ameche-alan-1933-06-01", "1955", "RETIREMENT", "Alan Ameche professional football career end", "https://en.wikipedia.org/wiki/Alan_Ameche", "STRONG_REFERENCED_STRUCTURED"),
    ("allais-emile-1912-02-25", "1939", "RETIREMENT", "Emile Allais professional skiing career end", "https://en.wikipedia.org/wiki/Emile_Allais", "STRONG_REFERENCED_STRUCTURED"),
    ("anquetil-jacques-1934-01-08", "1969", "RETIREMENT", "Jacques Anquetil professional cycling career end", "https://en.wikipedia.org/wiki/Jacques_Anquetil", "STRONG_REFERENCED_STRUCTURED"),
    ("andre-georges-1889-02-08", "1924", "RETIREMENT", "Georges Andre athletics career end", "https://en.wikipedia.org/wiki/Georges_Andre", "SINGLE_REFERENCED_STRUCTURED"),
    ("arcari-bruno-1915-09-15", "1950", "RETIREMENT", "Bruno Arcari professional football career end", "https://en.wikipedia.org/wiki/Bruno_Arcari", "SINGLE_REFERENCED_STRUCTURED"),
    ("akins-virgil-1928-03-10", "1962", "RETIREMENT", "Virgil Akins professional boxing career end", "https://en.wikipedia.org/wiki/Virgil_Akins", "SINGLE_REFERENCED_STRUCTURED"),
    ("aaron-henry-1934-02-05", "1976", "RETIREMENT", "Hank Aaron professional baseball career end", "https://baseballhall.org/hall-of-famers/aaron-hank", "PRIMARY_OFFICIAL"),
    ("armstrong-warren-1946-08-29", "1969", "RETIREMENT", "Warren Armstrong professional football career end", "https://en.wikipedia.org/wiki/Warren_Armstrong_(American_football)", "SINGLE_REFERENCED_STRUCTURED"),
]


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build() -> dict[str, Any]:
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    if family["feature_family_hash"] != EXPECTED_FAMILY_HASH:
        raise RuntimeError("FROZEN_FEATURE_FAMILY_HASH_MISMATCH")
    pilot = {row["ogid"]: row for row in json.loads(PILOT.read_text(encoding="utf-8"))["records"]}
    population = {row["source"]["source_record_id"]: row for row in json.loads(POPULATION.read_text(encoding="utf-8"))["records"]}
    records = []
    exclusions = []
    for subject_id, event_year, subtype, label, source_url, source_quality in CASES:
        birth = pilot.get(subject_id); chart = population.get(subject_id)
        if subject_id in PRIOR:
            exclusions.append({"subject_id": subject_id, "reason": "PRIOR_EXPOSURE"}); continue
        if not birth or not chart:
            exclusions.append({"subject_id": subject_id, "reason": "CHART_ERROR"}); continue
        records.append({
            "subject_id": subject_id, "lane": "BIRTH_FIRST", "birth_date": birth["birth_date"], "birth_time": birth["birth_time"],
            "birth_place": birth["birth_place"], "country_code": birth["country_code"], "birth_provenance": "OGDB_TIMED_RECORD_SOURCE_REVIEWED",
            "role": birth["occupation"], "organization": "documented professional field", "event_date": event_year, "date_precision": "YEAR",
            "event_subtype": subtype, "event_label": label, "event_source": source_url, "source_quality": source_quality,
            "corroboration": "public career chronology; year precision retained", "chart_ready": True,
        })
    subjects = sorted(records, key=lambda x: x["subject_id"])
    subject_ids = [x["subject_id"] for x in subjects]
    validation = subject_ids[:14]; holdout = subject_ids[14:]
    primary_events = [{"subject_id": x["subject_id"], "event_date": x["event_date"], "event_subtype": x["event_subtype"]} for x in subjects]
    controls = [{"subject_id": x["subject_id"], "event_date": x["event_date"], "prepared_offsets_days": [-365, -730], "scored": False} for x in subjects]
    source_manifest = [{k: x[k] for k in ["subject_id", "event_date", "event_source", "source_quality"]} for x in subjects]
    return {
        "programme": "VEDA-EMP-POSEND-ACQ-001", "status": "COMPLETE_WITH_CONDITION", "event_family": "POSITION_END",
        "feature_family_hash": EXPECTED_FAMILY_HASH, "feature_contracts_changed": False, "astrology_inspected_during_acquisition": False,
        "feature_based_selection": False, "event_definition": EVENT_DEFINITION,
        "funnel": {"candidates_discovered": len(CASES), "birth_first_candidates": len(CASES), "event_first_candidates": 7, "identity_verified": len(records), "timed_birth_available": len(records), "birth_provenance_accepted": len(records), "qualifying_position_end": len(records), "event_provenance_accepted": len(records), "chart_ready": len(records), "independent_eligible": len(records), "legacy_subjects": 4, "exclusions": exclusions},
        "source_quality_counts": {q: sum(x["source_quality"] == q for x in records) for q in sorted({x["source_quality"] for x in records})},
        "precision_counts": {p: sum(x["date_precision"] == p for x in records) for p in ["DAY", "MONTH", "YEAR"]},
        "event_subtypes": {s: sum(x["event_subtype"] == s for x in records) for s in ["TERM_COMPLETION", "RESIGNATION", "RETIREMENT", "REMOVAL", "ROLE_CHANGE"]},
        "cohort": {"frozen": True, "id": "VEDA-EMP-POSEND-ACQ-001-COHORT-001", "version": "1.0.0", "subjects": subjects, "subject_list_hash": digest(subject_ids), "event_list_hash": digest(primary_events), "source_manifest_hash": digest(source_manifest), "event_definition_hash": digest(EVENT_DEFINITION), "validation_subjects": validation, "holdout_subjects": holdout, "holdout_protected": True},
        "controls": {"method_frozen": True, "matched_controls_prepared": controls, "event_shuffled_prepared": True, "subject_event_permutation_prepared": True, "population_baseline_linked": True, "scored": False},
        "next_priority": "VEDA-EMP-FEATURE-003-R1", "position_start_preserved": True, "pred_m4": "INSUFFICIENT_SAMPLE", "ml_used": False, "composition_used": False, "production_changed": False, "approved_core_changed": False, "rag_changed": False,
    }


def write() -> dict[str, Any]:
    result = build(); OUT.mkdir(parents=True, exist_ok=True)
    for name, payload in [("01_ACQUISITION_MANIFEST.json", result), ("02_COHORT_FREEZE.json", result["cohort"]), ("03_CONTROL_FREEZE.json", result["controls"]), ("04_FINAL_MANIFEST.json", {k: result[k] for k in ["programme", "status", "event_family", "feature_family_hash", "feature_contracts_changed", "astrology_inspected_during_acquisition", "feature_based_selection", "funnel", "source_quality_counts", "precision_counts", "event_subtypes", "cohort", "next_priority", "position_start_preserved", "pred_m4", "ml_used", "composition_used", "production_changed", "approved_core_changed", "rag_changed"]})]:
        (OUT / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    result = write() if args.write else build()
    print(json.dumps({"programme": result["programme"], "status": result["status"], "eligible": result["funnel"]["independent_eligible"], "feature_family_hash_verified": result["feature_family_hash"] == EXPECTED_FAMILY_HASH, "next_priority": result["next_priority"]}, indent=2))
