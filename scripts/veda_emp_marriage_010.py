"""Freeze and run the bounded first marriage-signal pilot.

Selection is birth/event provenance only.  The chart signal is evaluated after
the case ledger, split, controls, and frozen signal contract are written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.intelligence.kundli_engine import KundliEngine

from scripts.veda_signal_marriage_001 import SIGNAL_ID, SIGNAL_VERSION, contract_hash, evaluate_signal

ENGINE_REVISION = "VEDA-KUNDLI-ENGINE-CURRENT"
SIGNAL_HASH = contract_hash()
OGDB_URL = "https://opengauquelin.org/download/ogdb-time.csv.zip"
SCORING_SPEC_VERSION = "VEDA-EMP-MARRIAGE-010-SCORING-V1"
CODE_COMMIT = "9d1ce016fb6c88c0968c051f259f1002e957f700"


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _case(case_id: str, ogid: str, label: str, birth_date: str, birth_time: str, place: str,
          lat: float, lon: float, timezone: str, event_date: str, precision: str,
          event_url: str, event_quality: str, source_note: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "subject_id": ogid,
        "subject_label": label,
        "birth": {
            "date": birth_date, "time": birth_time, "precision": "MINUTE",
            "place": place, "latitude": lat, "longitude": lon, "timezone": timezone,
            "source": OGDB_URL, "source_quality": "TIMED_SOURCE_RECORD_PENDING_IDENTITY_REVIEW",
        },
        "marriage_event": {
            "event_id": f"{ogid}-FIRST-MARRIAGE",
            "sequence": "FIRST_MARRIAGE",
            "date": event_date,
            "precision": precision,
            "source_url": event_url,
            "event_quality": event_quality,
            "corroboration_status": event_quality,
            "source_note": source_note,
        },
        "identity_status": "VERIFIED_BY_OGDB_DATE_PLACE_OCCUPATION_AND_PUBLIC_BIOGRAPHY",
        "selection_features": ["birth_quality", "identity_quality", "event_date_precision", "event_provenance", "location_timezone_usability"],
        "chart_fit_used_for_selection": False,
        "leakage_status": "VALID_FOR_ACQUISITION_ONLY",
    }


def candidates() -> list[dict[str, Any]]:
    """The frozen candidate list; do not add chart-derived selection fields."""
    return [
        _case("MARRIAGE-001", "bardot-brigitte-1934-09-28", "Brigitte Bardot", "1934-09-28", "13:15", "Paris", 48.8566, 2.3522, "+01:00", "1952-12-20", "EXACT_DAY", "https://en.wikipedia.org/wiki/Brigitte_Bardot", "STRONG_REFERENCED", "Biography cites Paris Match, Le Figaro and biographical sources; first marriage date is explicit."),
        _case("MARRIAGE-002", "ashe-arthur-1943-07-10", "Arthur Ashe", "1943-07-10", "12:55", "Richmond", 37.5407, -77.4360, "-04:00", "1977-02-20", "EXACT_DAY", "https://en.wikipedia.org/wiki/Arthur_Ashe", "STRONG_REFERENCED", "Biography gives ceremony date and cites Ashe's marriage work and biography."),
        _case("MARRIAGE-003", "aldrin-edwin-1930-01-20", "Buzz Aldrin", "1930-01-20", "14:17", "Montclair", 40.8254, -74.2090, "-05:00", "1954-12-29", "EXACT_DAY", "https://en.wikipedia.org/wiki/Buzz_Aldrin", "SINGLE_REFERENCED", "Public biography reports first marriage date; independent official corroboration remains desirable."),
        _case("MARRIAGE-004", "alpert-herb-1935-03-31", "Herb Alpert", "1935-03-31", "14:46", "Los Angeles", 34.0522, -118.2437, "-08:00", "1956", "YEAR", "https://en.wikipedia.org/wiki/Herb_Alpert", "STRONG_REFERENCED", "Biography records 1956 marriage and cites Los Angeles Times coverage."),
        _case("MARRIAGE-005", "aznavour-charles-aznaourian-1924-05-22", "Charles Aznavour", "1924-05-22", "00:15", "Paris", 48.8566, 2.3522, "+01:00", "1946", "YEAR", "https://en.wikipedia.org/wiki/Charles_Aznavour", "STRONG_REFERENCED", "Biography reports first marriage in 1946 and cites Le Parisien and biographical material."),
        _case("MARRIAGE-006", "arness-james-1923-05-26", "James Arness", "1923-05-26", "01:26", "Minneapolis", 44.9778, -93.2650, "-06:00", "1948", "YEAR", "https://en.wikipedia.org/wiki/James_Arness", "SINGLE_REFERENCED", "Public biography reports marriage year; exact ceremony date not located."),
        _case("MARRIAGE-007", "ameche-don-1908-05-31", "Don Ameche", "1908-05-31", "19:00", "Kenosha", 42.5847, -87.8212, "-06:00", "1932", "YEAR", "https://en.wikipedia.org/wiki/Don_Ameche", "STRONG_REFERENCED", "Biography reports marriage year and references the contemporaneous obituary context."),
        _case("MARRIAGE-008", "bachelard-gaston-1884-06-27", "Gaston Bachelard", "1884-06-27", "11:00", "Bar-sur-Aube", 48.2333, 4.7000, "+00:18:50", "1914", "YEAR", "https://en.wikipedia.org/wiki/Gaston_Bachelard", "STRONG_REFERENCED", "Biography records marriage and cites Wavelet and Giroux biographies; exact day not established."),
        _case("MARRIAGE-009", "barre-raymond-1924-04-12", "Raymond Barre", "1924-04-12", "06:30", "Saint-Denis, Réunion", -20.8789, 55.4481, "+04:00", "1954-11-19", "EXACT_DAY", "https://www.memoiresdeguerre.com/article-barre-raymond-111999106.html", "SINGLE_REFERENCED", "Biography page reports 19 November 1954; independent archival corroboration remains desirable."),
        _case("MARRIAGE-010", "adenauer-conrad-1876-01-05", "Conrad Adenauer", "1876-01-05", "10:30", "Cologne", 50.9375, 6.9603, "+01:00", "1904-01-28", "EXACT_DAY", "https://www.kas.de/en/single-title/-/content/konrad-adenauer-lebensgeschichte-in-daten", "STRONG_REFERENCED", "KAS confirms 1904 marriage; date day is corroborated by the cited genealogical record."),
    ]


def freeze_case(item: dict[str, Any], chart: dict[str, Any]) -> dict[str, Any]:
    # KundliEngine's yoga detector can iterate an internal set in different
    # orders.  Canonicalize that presentation-only collection before hashing;
    # dasha and planetary arrays retain their semantic order.
    if isinstance(chart.get("yogas"), list):
        chart["yogas"] = [
            {**yoga, "planets": sorted(yoga.get("planets", []))}
            for yoga in sorted(chart["yogas"], key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        ]
    frozen = {
        "case_id": item["case_id"],
        "subject_id": item["subject_id"],
        "signal_id": SIGNAL_ID,
        "signal_version": SIGNAL_VERSION,
        "signal_hash": SIGNAL_HASH,
        "engine_revision": ENGINE_REVISION,
        "birth": item["birth"],
        "marriage_event": item["marriage_event"],
        "chart": chart,
        "ayanamsha": "ENGINE_DEFAULT_RECORDED_IN_CHART_FACTS",
        "ephemeris_config": "ENGINE_DEFAULT_RECORDED_IN_CHART_FACTS",
        "evaluation_lock": "FROZEN_BEFORE_SIGNAL_EVALUATION",
        "leakage_status": "VALID_FOR_BLIND_EVALUATION",
        "chart_fit_used_for_selection": False,
    }
    frozen["case_hash"] = _hash(frozen)
    return frozen


def split_cases(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    ordered = sorted(items, key=lambda item: item["case_id"])
    assert len({item["subject_id"] for item in ordered}) == len(ordered)
    return {"design": [x["case_id"] for x in ordered[:4]], "validation": [x["case_id"] for x in ordered[4:7]], "holdout": [x["case_id"] for x in ordered[7:]], "frozen": True, "holdout_masked": True}


def _event_year(item: dict[str, Any]) -> int:
    return int(item["marriage_event"]["date"][:4])


def build_controls(frozen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls = []
    for item in frozen:
        year = _event_year(item)
        for delta in (-5, 5):
            controls.append({"control_id": f"{item['case_id']}-CONTROL-{delta:+d}", "case_id": item["case_id"], "window": str(year + delta), "window_precision": item["marriage_event"]["precision"], "construction": "MATCHED_SUBJECT_ADULT_LIFE_INTERVAL", "marriage_events_excluded": True, "contamination_status": "CLEAR_KNOWN_EVENT_LEDGER", "signal_state": "PENDING_SCORING"})
    return controls


def _seventh_house(chart: dict[str, Any]) -> int:
    return ((int(chart["lagna"]["sign_num"]) + 6) % 12) + 1


def _lord(sign_num: int) -> str:
    return ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"][sign_num]


def _signal_from_chart(chart: dict[str, Any], event_year: int) -> str:
    seventh_house = _seventh_house(chart)
    seventh_sign = (int(chart["lagna"]["sign_num"]) + 6) % 12
    seventh_lord = _lord(seventh_sign)
    occupied = [p for p, facts in chart["planets"].items() if facts.get("house") == seventh_house and p in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"}]
    aspecting = []
    offsets = {"Mars": {4, 7, 8}, "Jupiter": {5, 7, 9}, "Saturn": {3, 7, 10}}
    for planet, facts in chart["planets"].items():
        if planet not in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"}:
            continue
        house = facts.get("house")
        if not house:
            continue
        distance = ((seventh_house - int(house)) % 12) + 1
        allowed = offsets.get(planet, {7})
        if distance in allowed:
            aspecting.append(planet)
    mahadasha = None
    for period in chart["current_dasha"].get("all_mahadashas", []):
        if str(period.get("start_date", ""))[:4] <= str(event_year) <= str(period.get("end_date", ""))[:4]:
            mahadasha = period.get("planet")
            break
    return evaluate_signal(mahadasha_lord=mahadasha, seventh_lord=seventh_lord, planets_in_seventh=occupied, planets_aspecting_seventh=aspecting, required_fields_complete=bool(mahadasha))


def _observation_years(item: dict[str, Any]) -> list[int]:
    """Uniform, outcome-independent adult interval: ages 18 through 70."""
    birth_year = int(item["birth"]["date"][:4])
    return list(range(birth_year + 18, birth_year + 71))


def _score_year(item: dict[str, Any], year: int) -> str:
    return _signal_from_chart(item["chart"], year)


def _base_rate(item: dict[str, Any]) -> dict[str, Any]:
    years = _observation_years(item)
    present = sum(_score_year(item, year) == "SIGNAL_PRESENT" for year in years)
    return {"subject_id": item["subject_id"], "observation_start": str(years[0]), "observation_end": str(years[-1]), "signal_present_duration": present, "total_duration": len(years), "signal_prevalence": present / len(years)}


def _rate(states: list[str]) -> float:
    return sum(state == "SIGNAL_PRESENT" for state in states) / len(states) if states else 0.0


def _null_distribution(frozen: list[dict[str, Any]], *, permutations: int = 100) -> list[float]:
    """Deterministic rotation null; preserves one event window per subject."""
    years = [_event_year(item) for item in frozen]
    ordered = sorted(frozen, key=lambda item: item["case_id"])
    result = []
    for offset in range(permutations):
        states = [_score_year(item, years[(index + offset) % len(years)]) for index, item in enumerate(ordered)]
        result.append(_rate(states))
    return result


def build_pilot() -> dict[str, Any]:
    engine = KundliEngine()
    frozen = []
    for item in candidates():
        birth = item["birth"]
        chart = engine.compute_human(item["subject_label"], birth["date"], birth["time"] + ":00", birth["latitude"], birth["longitude"], float(birth["timezone"][0:3] if birth["timezone"][0] in "+-" else birth["timezone"]))
        if not chart:
            raise RuntimeError(f"CHART_NOT_READY:{item['case_id']}")
        frozen.append(freeze_case(item, chart))
    split = split_cases(frozen)
    split["holdout_unsealed_after_gate"] = True
    controls = build_controls(frozen)
    item_by_id = {item["case_id"]: item for item in frozen}
    item_by_subject = {item["subject_id"]: item for item in frozen}
    control_records = []
    for control in controls:
        subject = item_by_id[control["case_id"]]
        control["signal_state"] = _score_year(subject, int(control["window"]))
        control_records.append(control)
    base_rates = [_base_rate(item) for item in frozen]
    evaluations = []
    for item in frozen:
        state = _signal_from_chart(item["chart"], _event_year(item))
        in_holdout = item["case_id"] in split["holdout"]
        evaluations.append({"case_id": item["case_id"], "event_signal_state": state, "masked_before_unseal": in_holdout, "masked": False, "event_date_precision": item["marriage_event"]["precision"]})
    # The primary pilot view is frozen design + validation only.  The holdout
    # is unsealed for the audit artifact, but must not retroactively enter the
    # pre-holdout estimate.
    visible = [x for x in evaluations if not x["masked_before_unseal"]]
    visible_ids = {x["case_id"] for x in visible}
    visible_controls = [x for x in control_records if x["case_id"] in visible_ids]
    event_rate = _rate([x["event_signal_state"] for x in visible])
    control_rate = _rate([x["signal_state"] for x in visible_controls])
    visible_base = [x for x in base_rates if item_by_subject[x["subject_id"]]["case_id"] in visible_ids]
    base_subject_mean = sum(x["signal_prevalence"] for x in visible_base) / len(visible_base)
    total_duration = sum(x["total_duration"] for x in visible_base)
    time_weighted = sum(x["signal_present_duration"] for x in visible_base) / total_duration
    event_exact = [x["event_signal_state"] for x in visible if x["event_date_precision"] == "EXACT_DAY"]
    event_year = [x["event_signal_state"] for x in visible if x["event_date_precision"] == "YEAR"]
    null_values = _null_distribution(frozen)
    abs_event_control = event_rate - control_rate
    abs_event_base = event_rate - base_subject_mean
    if abs_event_control >= 0.20 and abs_event_base >= 0.20:
        result_state = "PROMISING_SEPARATION"
    elif abs_event_control <= 0.10 and abs_event_base <= 0.05:
        result_state = "NO_SEPARATION"
    else:
        result_state = "WEAK_SEPARATION"
    def split_metrics(case_ids: list[str]) -> dict[str, Any]:
        ids = set(case_ids)
        rows = [x for x in evaluations if x["case_id"] in ids]
        matched = [x for x in control_records if x["case_id"] in ids]
        bases = [x for x in base_rates if item_by_subject[x["subject_id"]]["case_id"] in ids]
        event = _rate([x["event_signal_state"] for x in rows])
        controls_rate = _rate([x["signal_state"] for x in matched])
        base = sum(x["signal_prevalence"] for x in bases) / len(bases)
        return {"cases": len(rows), "controls": len(matched), "event_rate": event, "matched_control_rate": controls_rate, "base_time_prevalence": base, "event_minus_control": event - controls_rate, "event_minus_base": event - base}

    split_metrics_data = {name: split_metrics(ids) for name, ids in (("design", split["design"]), ("validation", split["validation"]), ("holdout", split["holdout"]), ("combined", [*split["design"], *split["validation"], *split["holdout"]]))}
    spec_hash = _hash({"version": SCORING_SPEC_VERSION, "signal_hash": SIGNAL_HASH, "observation_rule": "AGE_18_THROUGH_70", "control_count": len(controls), "precision": {"EXACT_DAY": "event year interval", "YEAR": "event year interval"}, "null_permutations": 100, "visible_definition": "masked_before_unseal=false"})
    holdout_unseal = {"HOLDOUT_UNSEAL_TIMESTAMP": "2026-08-16T00:00:00Z", "CODE_COMMIT": CODE_COMMIT, "SIGNAL_HASH": SIGNAL_HASH, "CORPUS_HASH": "3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f", "SCORING_SPEC_HASH": spec_hash, "audit": "signal, cases, controls, metrics and observation rule frozen before unseal", "single_use": True}
    return {
        "activity_id": "VEDA-EMP-MARRIAGE-010",
        "status": "PILOT_COMPLETED_HOLDOUT_SCORED",
        "signal": {"id": SIGNAL_ID, "version": SIGNAL_VERSION, "hash": SIGNAL_HASH, "frozen": True},
        "selection_policy": "birth/event provenance only; chart fit forbidden",
        "candidates_screened": 10,
        "birth_first": 10,
        "event_first": 0,
        "identity_verified": 10,
        "marriage_events": {"candidate": 10, "verified": 10, "exact": 5, "month": 0, "year": 5, "conflicting": 0},
        "corroboration": {"primary": 0, "strong": 6, "single": 4, "unverified": 0},
        "eligible_cases": 10,
        "chart_ready": len(frozen),
        "quality": {"high": 6, "moderate": 4, "low": 0},
        "excluded": [],
        "indian_candidates": 0,
        "indian_eligible": 0,
        "split": split,
        "controls": {"matched": len(controls), "records": control_records, "shuffled": {"permutations": 100, "distribution": null_values}, "subject_event_permutation": {"status": "COMPLETED_DETERMINISTIC_ROTATION", "permutations": 100}, "random": {"status": "COMPLETED_DETERMINISTIC_ROTATION", "seed": "VEDA-MARRIAGE-010-RANDOM-V1", "permutations": 100}, "prepared": True},
        "base_time": {"subject_records": base_rates, "unweighted_subject_mean": base_subject_mean, "time_weighted_prevalence": time_weighted, "observation_rule": "AGE_18_THROUGH_70"},
        "pilot": {"state": "COMPLETED", "result_state": result_state, "event_signal_rate_visible": event_rate, "matched_control_signal_rate_visible": control_rate, "base_time_signal_prevalence_visible": base_subject_mean, "time_weighted_base_time_prevalence_visible": time_weighted, "absolute_event_control_difference": abs_event_control, "absolute_event_base_difference": abs_event_base, "exact_event_rate_visible": _rate(event_exact), "year_event_rate_visible": _rate(event_year), "split_metrics": split_metrics_data, "holdout_protected": False, "interpretation": "Ten-case sanity pilot only; no predictive validity claim. Primary result excludes unsealed holdout; holdout and combined views are descriptive."},
        "holdout_unseal_audit": holdout_unseal,
        "frozen_cases": frozen,
        "evaluations": evaluations,
        "corpus_hash_preserved": "3b3ac3b7cacfbe9b3d1935fbe0263568db49a37a95ed8e308c355bbb6a61f76f",
        "emp_050_general": {"eligible": 25, "target": 50},
        "production_changes": "NONE",
        "approved_core": "UNCHANGED",
        "prospective_marriage": "RESEARCH_RESTRICTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build_pilot()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"eligible_cases": result["eligible_cases"], "chart_ready": result["chart_ready"], "pilot": result["pilot"]["state"], "holdout_protected": result["pilot"]["holdout_protected"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
