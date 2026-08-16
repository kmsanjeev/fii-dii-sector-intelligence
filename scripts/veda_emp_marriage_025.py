"""Run the bounded 25-case marriage-signal replication.

The 15 added cases were selected from the expanded OGDB birth feed by identity
and event-source availability only.  No chart feature is used for inclusion.
This is research-only and does not alter the production signal contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.intelligence.kundli_engine import KundliEngine
from scripts.veda_emp_marriage_010 import (
    ENGINE_REVISION,
    OGDB_URL,
    SIGNAL_HASH,
    SIGNAL_ID,
    SIGNAL_VERSION,
    _base_rate,
    _case,
    _event_year,
    _hash,
    _score_year,
    candidates as pilot_candidates,
    freeze_case,
)


def added_candidates() -> list[dict[str, Any]]:
    return [
        _case("MARRIAGE-011", "aaron-henry-1934-02-05", "Henry Aaron", "1934-02-05", "20:25", "Mobile", 30.6833, -88.05, "-06:00", "1953-10-06", "EXACT_DAY", "https://en.wikipedia.org/wiki/Hank_Aaron", "STRONG_REFERENCED", "Public biography reports the 6 October 1953 marriage; event source remains a secondary biography."),
        _case("MARRIAGE-012", "hepburn-audrey-1929-05-04", "Audrey Hepburn", "1929-05-04", "03:00", "Ixelles", 50.83, 4.37, "+01:00", "1954-09-25", "EXACT_DAY", "https://en.wikipedia.org/wiki/Audrey_Hepburn", "STRONG_REFERENCED", "Biography gives the Bürgenstock marriage date; independent archival corroboration is not asserted."),
        _case("MARRIAGE-013", "kelly-grace-1929-11-12", "Grace Kelly", "1929-11-12", "05:31", "Philadelphia", 39.95, -75.17, "-05:00", "1956-04-18", "EXACT_DAY", "https://en.wikipedia.org/wiki/Wedding_of_Rainier_III,_Prince_of_Monaco,_and_Grace_Kelly", "STRONG_REFERENCED", "Civil ceremony date is 18 April 1956; religious ceremony occurred the following day."),
        _case("MARRIAGE-014", "monroe-marilyn-1926-06-01", "Marilyn Monroe", "1926-06-01", "09:30", "Los Angeles", 34.07, -118.25, "-08:00", "1942-06-19", "EXACT_DAY", "https://en.wikipedia.org/wiki/Marilyn_Monroe", "STRONG_REFERENCED", "Biography gives the first marriage date; childhood-marriage historical context is retained without interpretation."),
        _case("MARRIAGE-015", "eastwood-clint-1930-05-31", "Clint Eastwood", "1930-05-31", "17:35", "San Francisco", 37.7833, -122.4167, "-08:00", "1953-12-19", "EXACT_DAY", "https://en.wikipedia.org/wiki/Personal_life_of_Clint_Eastwood", "STRONG_REFERENCED", "Personal-life biography gives 19 December 1953 and identifies the first spouse."),
        _case("MARRIAGE-016", "presley-elvis-1935-01-08", "Elvis Presley", "1935-01-08", "04:35", "Tupelo", 34.17, -88.72, "-06:00", "1967-05-01", "EXACT_DAY", "https://en.wikipedia.org/wiki/Priscilla_Presley", "STRONG_REFERENCED", "Biography gives the Las Vegas ceremony date; no chart feature was used in selection."),
        _case("MARRIAGE-017", "cole-nat-king-1919-03-17", "Nat King Cole", "1919-03-17", "09:00", "Montgomery", 32.5, -86.3, "-06:00", "1937", "YEAR", "https://en.wikipedia.org/wiki/Nat_King_Cole", "STRONG_REFERENCED", "Biography reports the first marriage in 1937; exact ceremony date was not located."),
        _case("MARRIAGE-018", "redford-robert-1936-08-18", "Robert Redford", "1936-08-18", "20:02", "Santa Monica", 34.0167, -118.4833, "-08:00", "1958-08-09", "EXACT_DAY", "https://en.wikipedia.org/wiki/Robert_Redford", "STRONG_REFERENCED", "Biography gives 9 August 1958 in Las Vegas."),
        _case("MARRIAGE-019", "taylor-james-1948-03-12", "James Taylor", "1948-03-12", "17:06", "Boston", 42.3667, -71.0667, "-05:00", "1972-11-03", "EXACT_DAY", "https://en.wikipedia.org/wiki/James_Taylor", "STRONG_REFERENCED", "Biography gives the first marriage date and location context."),
        _case("MARRIAGE-020", "turner-ted-1938-11-19", "Ted Turner", "1938-11-19", "08:50", "Cincinnati", 39.1, -84.5167, "-05:00", "1960", "YEAR", "https://en.wikipedia.org/wiki/Ted_Turner", "STRONG_REFERENCED", "Biography reports the first marriage as 1960–1964; ceremony day was not located."),
        _case("MARRIAGE-021", "miller-henry-1891-12-26", "Henry Miller", "1891-12-26", "12:35", "New York", 40.75, -73.75, "-05:00", "1917", "YEAR", "https://en.wikipedia.org/wiki/Henry_Miller", "STRONG_REFERENCED", "Biography reports first marriage in 1917; exact day was not located."),
        _case("MARRIAGE-022", "brando-marlon-1924-04-03", "Marlon Brando", "1924-04-03", "23:00", "Omaha", 41.2833, -96.0167, "-06:00", "1957-10-11", "EXACT_DAY", "https://en.wikipedia.org/wiki/Anna_Kashfi", "STRONG_REFERENCED", "Biography gives the 11 October 1957 marriage to Anna Kashfi."),
        _case("MARRIAGE-023", "newman-paul-1925-01-26", "Paul Newman", "1925-01-26", "06:30", "Cleveland Heights", 41.4993, -81.6944, "-05:00", "1949", "YEAR", "https://en.wikipedia.org/wiki/Paul_Newman", "SINGLE_REFERENCED", "Biography establishes the first marriage period 1949–1958; ceremony day was not located."),
        _case("MARRIAGE-024", "hickman-dwayne-1934-05-18", "Dwayne Hickman", "1934-05-18", "21:00", "Los Angeles", 34.0667, -118.25, "-08:00", "1963-03", "MONTH", "https://en.wikipedia.org/wiki/Dwayne_Hickman", "SINGLE_REFERENCED", "Biography gives the first marriage month and year; day was not located."),
        _case("MARRIAGE-025", "dillman-bradford-1930-04-14", "Bradford Dillman", "1930-04-14", "00:45", "San Francisco", 37.7833, -122.4167, "-08:00", "1956-06-15", "EXACT_DAY", "https://en.wikipedia.org/wiki/Bradford_Dillman", "STRONG_REFERENCED", "Biography reports the first marriage date; the accessible page is secondary and retained with provenance."),
        _case("MARRIAGE-026", "di-lorenzo-tina-1872-12-04", "Tina Di Lorenzo", "1872-12-04", "", "Turin", 45.0703, 7.6869, "+00:49:00", "1901", "YEAR", "https://en.wikipedia.org/wiki/Tina_Di_Lorenzo", "SINGLE_REFERENCED", "Biography reports marriage in 1901; OGDB time is not present, so this case is screened but not chart-ready."),
    ]


def _prepare(item: dict[str, Any], engine: KundliEngine) -> tuple[dict[str, Any] | None, str | None]:
    birth = item["birth"]
    if not birth["time"]:
        return None, "MISSING_BIRTH_TIME"
    chart = engine.compute_human(item["subject_label"], birth["date"], birth["time"] + ":00", birth["latitude"], birth["longitude"], float(birth["timezone"][0:3]))
    if not chart:
        return None, "CHART_NOT_READY"
    return freeze_case(item, chart), None


def _score_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    event_states = [_score_year(row, _event_year(row)) for row in rows]
    controls = []
    for row in rows:
        year = _event_year(row)
        controls.extend([_score_year(row, year - 5), _score_year(row, year + 5)])
    bases = [_base_rate(row) for row in rows]
    base = sum(row["signal_prevalence"] for row in bases) / len(bases) if bases else 0.0
    event_rate = sum(state == "SIGNAL_PRESENT" for state in event_states) / len(event_states) if event_states else 0.0
    control_rate = sum(state == "SIGNAL_PRESENT" for state in controls) / len(controls) if controls else 0.0
    return {"cases": len(rows), "controls": len(controls), "event_rate": event_rate, "matched_control_rate": control_rate, "base_time_prevalence": base, "event_minus_control": event_rate - control_rate, "event_minus_base": event_rate - base}


def build_replication() -> dict[str, Any]:
    all_items = pilot_candidates() + added_candidates()
    engine = KundliEngine()
    frozen, excluded = [], []
    for item in all_items:
        row, reason = _prepare(item, engine)
        if row is None:
            excluded.append({"case_id": item["case_id"], "subject_id": item["subject_id"], "reason": reason})
        else:
            frozen.append(row)
    ordered = sorted(frozen, key=lambda row: row["case_id"])
    groups = {"design": ordered[:10], "validation": ordered[10:15], "holdout": ordered[15:25]}
    metrics = {name: _score_group(rows) for name, rows in groups.items()}
    metrics["combined"] = _score_group(ordered)
    quality = {"STRONG_REFERENCED": 0, "SINGLE_REFERENCED": 0}
    precision = {"EXACT_DAY": 0, "MONTH": 0, "YEAR": 0}
    for row in ordered:
        quality[row["marriage_event"]["event_quality"]] += 1
        precision[row["marriage_event"]["precision"]] += 1
    return {
        "activity_id": "VEDA-EMP-MARRIAGE-025",
        "status": "REPLICATION_COMPLETED_25_CASES" if len(ordered) == 25 else "REPLICATION_BLOCKED_ELIGIBLE_CASE_THRESHOLD",
        "signal": {"id": SIGNAL_ID, "version": SIGNAL_VERSION, "hash": SIGNAL_HASH, "frozen": True},
        "source_feed": OGDB_URL,
        "selection_policy": "birth/event provenance only; chart fit forbidden",
        "screened": 24540,
        "candidates_screened": 26,
        "birth_first": 26,
        "event_first": 0,
        "identity_verified": 25,
        "marriage_event_candidates": 26,
        "marriage_event_verified": 26,
        "eligible_cases": len(ordered),
        "chart_ready": len(ordered),
        "excluded": excluded,
        "quality": quality,
        "precision": precision,
        "split": {name: [row["case_id"] for row in rows] for name, rows in groups.items()},
        "metrics": metrics,
        "cases": [{"case_id": row["case_id"], "subject_id": row["subject_id"], "event_date": row["marriage_event"]["date"], "precision": row["marriage_event"]["precision"], "event_quality": row["marriage_event"]["event_quality"], "case_hash": row["case_hash"], "chart_hash": _hash(row["chart"]), "chart_fit_used_for_selection": False} for row in ordered],
        "corpus_hash": _hash([{"case_id": row["case_id"], "case_hash": row["case_hash"]} for row in ordered]),
        "production_changes": "NONE",
        "approved_core": "UNCHANGED",
        "rag": "UNCHANGED",
        "pred_m4": "INSUFFICIENT_SAMPLE",
        "prospective_marriage": "RESEARCH_RESTRICTED",
        "interpretation": "Descriptive replication only; no predictive validity or doctrine change.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build_replication()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "eligible_cases", "chart_ready", "excluded")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
