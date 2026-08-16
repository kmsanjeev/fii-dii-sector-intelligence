"""Independent 25-case extension and combined 50-case marriage replication."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.intelligence.kundli_engine import KundliEngine
from scripts.veda_emp_marriage_010 import _base_rate, _case, _event_year, _score_year, freeze_case
from scripts.veda_emp_marriage_025 import added_candidates
from scripts.veda_emp_marriage_010 import candidates as initial_candidates


def extension_candidates() -> list[dict[str, Any]]:
    return [
        _case("MARRIAGE-027", "stewart-james-1921-04-02", "James Stewart", "1921-04-02", "21:00", "St Louis", 38.6167, -90.2, "-06:00", "1949-08-09", "EXACT_DAY", "https://en.wikipedia.org/wiki/James_Stewart", "STRONG_REFERENCED", "Biography gives the first marriage ceremony date."),
        _case("MARRIAGE-028", "russell-jane-1921-06-21", "Jane Russell", "1921-06-21", "06:15", "Bemidji", 47.4667, -94.8833, "-06:00", "1943-04-24", "EXACT_DAY", "https://en.wikipedia.org/wiki/Jane_Russell", "STRONG_REFERENCED", "Biography gives the Las Vegas marriage date."),
        _case("MARRIAGE-029", "travolta-john-1954-02-18", "John Travolta", "1954-02-18", "14:53", "Englewood", 40.9, -73.9833, "-05:00", "1991-09-05", "EXACT_DAY", "https://en.wikipedia.org/wiki/Kelly_Preston", "STRONG_REFERENCED", "Biography gives the first Paris ceremony date and notes the second ceremony."),
        _case("MARRIAGE-030", "walker-clint-1927-05-30", "Clint Walker", "1927-05-30", "13:15", "Hartford", 38.8333, -90.1, "-06:00", "1948", "YEAR", "https://en.wikipedia.org/wiki/Clint_Walker", "STRONG_REFERENCED", "Biography reports first marriage in 1948; day was not located."),
        _case("MARRIAGE-031", "leigh-janet-1927-07-06", "Janet Leigh", "1927-07-06", "14:15", "Merced", 37.3, -120.4833, "-08:00", "1942-08-01", "EXACT_DAY", "https://en.wikipedia.org/wiki/Janet_Leigh", "STRONG_REFERENCED", "Biography gives the Reno marriage date and annulment date."),
        _case("MARRIAGE-032", "mason-marsha-1942-04-03", "Marsha Mason", "1942-04-03", "11:12", "St Louis", 38.6167, -90.2, "-05:00", "1965", "YEAR", "https://en.wikipedia.org/wiki/Marsha_Mason", "SINGLE_REFERENCED", "Biography reports first marriage as 1965–1970; exact day was not located."),
        _case("MARRIAGE-033", "williams-cindy-1947-08-22", "Cindy Williams", "1947-08-22", "16:35", "Van Nuys", 34.1833, -118.4333, "-08:00", "1982", "YEAR", "https://en.wikipedia.org/wiki/Cindy_Williams", "STRONG_REFERENCED", "Biography reports marriage in 1982; exact day was not located."),
        _case("MARRIAGE-034", "annenberg-walter-1908-03-13", "Walter Annenberg", "1908-03-13", "13:30", "Milwaukee", 43.0333, -87.9167, "-06:00", "1939", "YEAR", "https://en.wikipedia.org/wiki/Walter_Annenberg", "STRONG_REFERENCED", "Biography reports first marriage in 1939."),
        _case("MARRIAGE-035", "baker-howard-1925-11-15", "Howard Baker", "1925-11-15", "15:00", "Huntsville", 35.8, -84.2667, "-06:00", "1951", "YEAR", "https://en.wikipedia.org/wiki/Howard_Baker", "STRONG_REFERENCED", "Biography reports first marriage in 1951."),
        _case("MARRIAGE-036", "ariyoshi-george-1926-03-12", "George Ariyoshi", "1926-03-12", "05:00", "Honolulu", 21.3167, -157.8667, "-10:30", "1955", "YEAR", "https://en.wikipedia.org/wiki/George_Ariyoshi", "STRONG_REFERENCED", "Biography reports marriage in 1955."),
        _case("MARRIAGE-037", "andrus-cecil-1931-08-25", "Cecil Andrus", "1931-08-25", "08:20", "Hood River", 45.7167, -121.5167, "-08:00", "1949", "YEAR", "https://en.wikipedia.org/wiki/Cecil_Andrus", "STRONG_REFERENCED", "Biography reports a late-August 1949 elopement; exact day was not located."),
        _case("MARRIAGE-038", "anouk-aimee-dreyfus-nic-1932-04-27", "Anouk Aimée", "1932-04-27", "12:00", "Paris", 48.8534, 2.3488, "+01:00", "1949", "YEAR", "https://en.wikipedia.org/wiki/Anouk_Aim%C3%A9e", "STRONG_REFERENCED", "Biography reports first marriage in 1949."),
        _case("MARRIAGE-039", "arendt-hannah-1906-10-14", "Hannah Arendt", "1906-10-14", "21:15", "Hannover-Linden", 52.38, 9.73, "+01:00", "1929-09-26", "EXACT_DAY", "https://en.wikipedia.org/wiki/Hannah_Arendt", "STRONG_REFERENCED", "Biography gives the Potsdam marriage date."),
        _case("MARRIAGE-040", "antonioni-michelangelo-1912-09-29", "Michelangelo Antonioni", "1912-09-29", "21:45", "Ferrara", 44.7, 12.5, "+01:00", "1942", "YEAR", "https://en.wikipedia.org/wiki/Michelangelo_Antonioni", "SINGLE_REFERENCED", "Biography reports first marriage in 1942; exact day was not located."),
        _case("MARRIAGE-041", "baeyer-adolf-1835-10-31", "Adolf von Baeyer", "1835-10-31", "22:30", "Berlin", 52.53, 13.3, "+01:00", "1868", "YEAR", "https://en.wikipedia.org/wiki/Adolf_von_Baeyer", "STRONG_REFERENCED", "Biography reports marriage in 1868; timezone is inferred because OGDB omits it."),
        _case("MARRIAGE-042", "anquetil-jacques-1934-01-08", "Jacques Anquetil", "1934-01-08", "10:30", "Mont-Saint-Aignan", 49.4631, 1.0936, "+00:00", "1958-12-22", "EXACT_DAY", "https://en.wikipedia.org/wiki/Jacques_Anquetil", "STRONG_REFERENCED", "Biography gives the 22 December 1958 marriage date."),
        _case("MARRIAGE-043", "auriol-vincent-1884-08-27", "Vincent Auriol", "1884-08-27", "18:00", "Revel", 43.4589, 2.0044, "+00:08", "1911-06-01", "EXACT_DAY", "https://en.wikipedia.org/wiki/Vincent_Auriol", "STRONG_REFERENCED", "Biography gives the 1 June 1911 marriage date."),
        _case("MARRIAGE-044", "alvarez-luis-1911-06-13", "Luis Walter Alvarez", "1911-06-13", "02:45", "San Francisco", 37.7833, -122.4167, "-08:00", "1936", "YEAR", "https://en.wikipedia.org/wiki/Luis_Walter_Alvarez", "SINGLE_REFERENCED", "Biography establishes the first marriage after the 1936 engagement; exact day was not located."),
        _case("MARRIAGE-045", "morgan-michele-1920-02-29", "Michèle Morgan", "1920-02-29", "09:20", "Neuilly-sur-Seine", 48.8333, 2.1833, "+01:00", "1942", "YEAR", "https://en.wikipedia.org/wiki/Mich%C3%A8le_Morgan", "STRONG_REFERENCED", "Biography reports marriage in 1942."),
        _case("MARRIAGE-046", "ammann-lukas-1912-09-29", "Lukas Ammann", "1912-09-29", "", "Basel", 47.55, 7.5833, "+01:00", "1959", "YEAR", "https://en.wikipedia.org/wiki/Lukas_Ammann", "SINGLE_REFERENCED", "Biography reports marriage to Liselotte Ebnet in 1959; OGDB time is absent, so this case is excluded from chart-ready scoring."),
        _case("MARRIAGE-047", "austin-tracy-1962-12-12", "Tracy Austin", "1962-12-12", "06:18", "Redondo Beach", 33.8333, -118.3833, "-08:00", "1993-04-17", "EXACT_DAY", "https://www.imdb.com/name/nm1286221/bio/", "SINGLE_REFERENCED", "Biography record reports 17 April 1993; independent archival corroboration remains desirable."),
        _case("MARRIAGE-048", "langevin-paul-1872-01-23", "Paul Langevin", "1872-01-23", "21:00", "Paris", 48.8534, 2.3488, "+00:09:24", "1898", "YEAR", "https://en.wikipedia.org/wiki/Paul_Langevin", "STRONG_REFERENCED", "Biography reports marriage in 1898."),
        _case("MARRIAGE-049", "appell-paul-1855-09-27", "Paul Émile Appell", "1855-09-27", "07:00", "Strasbourg", 48.5839, 7.7455, "+00:30:59", "1881", "YEAR", "https://en.wikipedia.org/wiki/Paul_%C3%89mile_Appell", "SINGLE_REFERENCED", "Biography reports marriage in 1881; exact day was not located."),
        _case("MARRIAGE-050", "achille-fould-aymar-1925-07-17", "Aymar Achille-Fould", "1925-07-17", "10:45", "Tarbes", 43.2341, 0.0714, "+01:00", "1947-04-12", "EXACT_DAY", "https://gw.geneanet.org/wikifrat?lang=fr&n=achille+fould&p=aymar", "SINGLE_REFERENCED", "Genealogical record reports 12 April 1947; independent official corroboration remains desirable."),
        _case("MARRIAGE-051", "abbe-ernst-1840-01-23", "Ernst Abbe", "1840-01-23", "21:30", "Eisenach", 50.98, 10.32, "+01:00", "1871", "YEAR", "https://de.wikipedia.org/wiki/Ernst_Abbe", "STRONG_REFERENCED", "Institutional/biographical record reports marriage in 1871; timezone is inferred because OGDB omits it."),
        _case("MARRIAGE-052", "bardoux-jacques-1874-05-27", "Jacques Bardoux", "1874-05-27", "14:30", "Versailles", 48.80359, 2.13424, "+00:08", "1899-02-07", "EXACT_DAY", "https://de.wikipedia.org/wiki/Jacques_Bardoux", "SINGLE_REFERENCED", "Biographical record reports the Paris marriage on 7 February 1899; OGDB supplies the recorded birth time and historical local offset."),
    ]


def _score_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    event = [_score_year(row, _event_year(row)) for row in rows]
    controls = [_score_year(row, _event_year(row) + delta) for row in rows for delta in (-5, 5)]
    bases = [_base_rate(row) for row in rows]
    event_rate = sum(x == "SIGNAL_PRESENT" for x in event) / len(event) if event else 0.0
    control_rate = sum(x == "SIGNAL_PRESENT" for x in controls) / len(controls) if controls else 0.0
    base = sum(x["signal_prevalence"] for x in bases) / len(bases) if bases else 0.0
    return {"cases": len(rows), "controls": len(controls), "event_rate": event_rate, "matched_control_rate": control_rate, "base_time_prevalence": base, "event_minus_control": event_rate - control_rate, "event_minus_base": event_rate - base}


def build_replication() -> dict[str, Any]:
    initial = initial_candidates() + [x for x in added_candidates() if x["case_id"] != "MARRIAGE-026"]
    extension = extension_candidates()
    engine = KundliEngine()
    prepared: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for cohort, items in (("INITIAL_EMPIRICAL_COHORT", initial), ("REPLICATION_EXTENSION", extension)):
        for item in items:
            if not item["birth"]["time"]:
                excluded.append({"case_id": item["case_id"], "cohort": cohort, "reason": "MISSING_BIRTH_TIME"})
                continue
            chart = engine.compute_human(item["subject_label"], item["birth"]["date"], item["birth"]["time"] + ":00", item["birth"]["latitude"], item["birth"]["longitude"], float(item["birth"]["timezone"][0:3]))
            if not chart:
                excluded.append({"case_id": item["case_id"], "cohort": cohort, "reason": "CHART_NOT_READY"})
                continue
            row = freeze_case(item, chart)
            row["cohort"] = cohort
            prepared.append(row)
    original = sorted([x for x in prepared if x["cohort"] == "INITIAL_EMPIRICAL_COHORT"], key=lambda x: x["case_id"])
    new = sorted([x for x in prepared if x["cohort"] == "REPLICATION_EXTENSION"], key=lambda x: x["case_id"])
    metrics = {
        "original_25": _score_group(original),
        "new_25": _score_group(new),
        "new_25_design": _score_group(new[:10]),
        "new_25_validation": _score_group(new[10:15]),
        "new_25_holdout": _score_group(new[15:25]),
        "combined_50": _score_group(original + new),
    }
    return {"activity_id": "VEDA-EMP-050-REPLICATION-SIGNAL-002", "status": "MARRIAGE_50_COMPLETED" if len(original) == 25 and len(new) == 25 else "MARRIAGE_50_BLOCKED", "signal": {"id": "VEDA-SIGNAL-MARRIAGE-OCCURRENCE-001", "version": "1.0.0", "hash": "b09f7ed42632c900c1ccc65899e7e7a065c6d24b78f6b0627701f0007518d080", "immutable": True}, "initial_25": len(original), "new_25": len(new), "combined_50": len(original) + len(new), "excluded": excluded, "metrics": metrics, "cases": [{"case_id": x["case_id"], "subject_id": x["subject_id"], "cohort": x["cohort"], "event_date": x["marriage_event"]["date"], "precision": x["marriage_event"]["precision"], "event_quality": x["marriage_event"]["event_quality"], "case_hash": x["case_hash"]} for x in original + new], "production_changes": "NONE", "approved_core": "UNCHANGED", "rag": "UNCHANGED", "pred_m4": "INSUFFICIENT_SAMPLE", "prospective_marriage": "RESEARCH_RESTRICTED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build_replication()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "initial_25", "new_25", "combined_50", "excluded")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
