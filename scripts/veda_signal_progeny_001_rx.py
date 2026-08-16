"""Outcome-blind activation prevalence audit for the frozen progeny signal."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.ai.knowledge.astrology_calculation_validation import DASHA_SEQUENCE, DASHA_YEARS, TOTAL_DASHA_YEARS
from engines.intelligence.kundli_engine import KundliEngine
from scripts.veda_signal_progeny_001 import CONTRACT, evaluate, signal_hash


SIGNAL_ID = CONTRACT["signal_id"]
SIGNAL_VERSION = CONTRACT["version"]
SIGNAL_HASH = signal_hash()
OGDB_URL = "https://opengauquelin.org/download/ogdb-time.csv.zip"
OBSERVATION_RULE = "AGE_18_THROUGH_70"
CODE_BASELINE = "cc0ed05a634373f62ded1d8e2bba57893a53de21"
SCORING_SPEC_VERSION = "VEDA-SIGNAL-PROGENY-001-RX-SCORING-V1"
THRESHOLDS = {"NORMAL_PREVALENCE": 0.10, "LOW_PREVALENCE": 0.03, "VERY_LOW_PREVALENCE": 0.01}


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _lord(sign_num: int) -> str:
    return ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"][sign_num]


def _distance(from_house: int, to_house: int) -> int:
    return ((to_house - from_house) % 12) + 1


def _offset_minutes(value: str) -> int:
    sign = -1 if value.startswith("-") else 1
    h, m = value[1:].split(":")
    return sign * (int(h) * 60 + int(m))


def _birth_utc(row: dict[str, str]) -> datetime:
    local = datetime.strptime(row["DATE"], "%Y-%m-%d %H:%M")
    return (local - timedelta(minutes=_offset_minutes(row["TZO"]))).replace(tzinfo=timezone.utc)


def _periods(chart: dict[str, Any], birth_utc: datetime) -> list[dict[str, Any]]:
    moon = float(chart["planets"]["Moon"]["longitude"]) % 360.0
    segment = 360.0 / 27.0
    birth_lord = DASHA_SEQUENCE[int(moon / segment) % 27 % 9]
    elapsed = (moon % segment) / segment
    first = (1.0 - elapsed) * DASHA_YEARS[birth_lord]
    start_index = DASHA_SEQUENCE.index(birth_lord)
    periods = []
    cursor = birth_utc
    sequence = [(birth_lord, first)] + [(DASHA_SEQUENCE[(start_index + i) % 9], DASHA_YEARS[DASHA_SEQUENCE[(start_index + i) % 9]]) for i in range(1, 18)]
    for planet, years in sequence:
        end = cursor + timedelta(days=years * 365.25)
        periods.append({"planet": planet, "start": cursor, "end": end})
        cursor = end
    return periods


def _antardasha_intervals(maha: dict[str, Any]) -> list[dict[str, Any]]:
    start_index = DASHA_SEQUENCE.index(maha["planet"])
    cursor = maha["start"]
    result = []
    for i in range(9):
        planet = DASHA_SEQUENCE[(start_index + i) % 9]
        years = DASHA_YEARS[maha["planet"]] * DASHA_YEARS[planet] / TOTAL_DASHA_YEARS
        end = cursor + timedelta(days=years * 365.25)
        result.append({"planet": planet, "start": cursor, "end": end})
        cursor = end
    return result


def _window(row: dict[str, str]) -> tuple[datetime, datetime]:
    birth = date.fromisoformat(row["DATE"][:10])
    return datetime(birth.year + 18, 1, 1, tzinfo=timezone.utc), datetime(birth.year + 71, 1, 1, tzinfo=timezone.utc)


def _facts(chart: dict[str, Any], maha: str, antar: str) -> dict[str, Any]:
    lagna = int(chart["lagna"]["sign_num"])
    fifth_lord_name = _lord((lagna + 4) % 12)
    fifth_lord = chart["planets"][fifth_lord_name]
    jupiter = chart["planets"]["Jupiter"]
    sun = chart["planets"]["Sun"]
    sun_dignity = sun.get("dignity")
    return {
        "fifth_lord_house": int(fifth_lord["house"]),
        "fifth_lord_exalted": fifth_lord.get("dignity") == "exalted",
        "fifth_lord_conjunct_jupiter": int(fifth_lord["house"]) == int(jupiter["house"]),
        "fifth_lord_aspected_by_jupiter": _distance(int(jupiter["house"]), int(fifth_lord["house"])) in {5, 7, 9},
        "mahadasha": maha,
        "antardasha": antar,
        "sun_house": int(sun["house"]),
        "sun_exalted": sun_dignity == "exalted",
        "sun_own_sign": sun_dignity == "own_sign",
        "sun_strong": sun_dignity in {"exalted", "own_sign", "moolatrikona", "friendly"},
        "sun_house_from_mahadasha_lord": _distance(int(jupiter["house"]), int(sun["house"])) if maha == "Jupiter" else None,
    }


def _row_is_usable(row: dict[str, str]) -> bool:
    return bool(re.fullmatch(r"[+-]\d{2}:\d{2}", row.get("TZO", "")) and row.get("DATE", "").count(":") == 1 and row.get("LG") and row.get("LAT") and row.get("PLACE"))


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle, delimiter=";") if _row_is_usable(row)]
    return sorted(rows, key=lambda row: row["OGID"])


def _audit_row(row: dict[str, str], engine: KundliEngine) -> dict[str, Any] | None:
    try:
        lat, lon = float(row["LAT"]), float(row["LG"])
        tz_hours = _offset_minutes(row["TZO"]) / 60.0
        chart = engine.compute_human(row["FNAME"] + " " + row["GNAME"], row["DATE"][:10], row["DATE"][11:] + ":00", lat, lon, tz_hours)
        if not chart:
            return None
        start, end = _window(row)
        periods = _periods(chart, _birth_utc(row))
        structural_facts = _facts(chart, "Jupiter", "Sun")
        structural_state = bool(structural_facts["fifth_lord_exalted"] or structural_facts["fifth_lord_house"] in {2, 5, 9} or structural_facts["fifth_lord_conjunct_jupiter"] or structural_facts["fifth_lord_aspected_by_jupiter"])
        md_jupiter_seconds = 0.0
        js_seconds = 0.0
        signal_seconds = 0.0
        indeterminate_seconds = 0.0
        for maha in periods:
            md_overlap = max(0.0, (min(end, maha["end"]) - max(start, maha["start"])).total_seconds())
            if maha["planet"] == "Jupiter":
                md_jupiter_seconds += md_overlap
                for antar in _antardasha_intervals(maha):
                    overlap = max(0.0, (min(end, antar["end"]) - max(start, antar["start"])).total_seconds())
                    if antar["planet"] == "Sun":
                        js_seconds += overlap
                        state = evaluate(_facts(chart, "Jupiter", "Sun"))
                        if state["state"] == "SIGNAL_PRESENT" and structural_state:
                            signal_seconds += overlap
                        elif state["state"] == "INDETERMINATE":
                            indeterminate_seconds += overlap
        total_seconds = (end - start).total_seconds()
        active = signal_seconds > 0
        return {
            "ogid": row["OGID"],
            "birth_date": row["DATE"],
            "observation_start": start.date().isoformat(),
            "observation_end": (end - timedelta(days=1)).date().isoformat(),
            "structural_condition": structural_state,
            "structural_and_timing_seconds": round(js_seconds if structural_state else 0.0, 3),
            "jupiter_md_seconds": round(md_jupiter_seconds, 3),
            "jupiter_sun_ad_seconds": round(js_seconds, 3),
            "signal_present_seconds": round(signal_seconds, 3),
            "indeterminate_seconds": round(indeterminate_seconds, 3),
            "observation_seconds": round(total_seconds, 3),
            "subject_prevalence": round(signal_seconds / total_seconds, 10),
            "first_activation_age": 18 if active else None,
            "last_activation_age": 70 if active else None,
        }
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def _reachability(value: float) -> str:
    if value == 0:
        return "ZERO_PREVALENCE"
    if value < THRESHOLDS["VERY_LOW_PREVALENCE"]:
        return "NEAR_ZERO_PREVALENCE"
    if value < THRESHOLDS["LOW_PREVALENCE"]:
        return "VERY_LOW_PREVALENCE"
    if value < THRESHOLDS["NORMAL_PREVALENCE"]:
        return "LOW_PREVALENCE"
    return "NORMAL_PREVALENCE"


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(row["observation_seconds"] for row in rows)
    signal = sum(row["signal_present_seconds"] for row in rows)
    prevalences = [row["subject_prevalence"] for row in rows]
    any_signal = sum(row["signal_present_seconds"] > 0 for row in rows)
    structural = sum(row["structural_condition"] for row in rows)
    md = sum(row["jupiter_md_seconds"] > 0 for row in rows)
    js = sum(row["jupiter_sun_ad_seconds"] > 0 for row in rows)
    combined = sum(row["signal_present_seconds"] > 0 for row in rows)
    structural_timing = sum(row["structural_and_timing_seconds"] > 0 for row in rows)
    rate = any_signal / len(rows) if rows else 0.0
    return {
        "subjects_analyzed": len(rows),
        "subjects_with_any_signal": any_signal,
        "subject_activation_rate": rate,
        "total_observation_years": total / (365.25 * 86400),
        "signal_present_years": signal / (365.25 * 86400),
        "time_weighted_signal_prevalence": signal / total if total else 0.0,
        "unweighted_mean_subject_prevalence": statistics.mean(prevalences) if prevalences else 0.0,
        "median_subject_prevalence": statistics.median(prevalences) if prevalences else 0.0,
        "zero_signal_subjects": len(rows) - any_signal,
        "indeterminate_subjects": sum(row["indeterminate_seconds"] > 0 for row in rows),
        "structural_condition_rate": structural / len(rows) if rows else 0.0,
        "jupiter_md_rate": md / len(rows) if rows else 0.0,
        "jupiter_md_sun_ad_rate": js / len(rows) if rows else 0.0,
        "combined_signal_rate": combined / len(rows) if rows else 0.0,
        "structural_and_timing_rate": structural_timing / len(rows) if rows else 0.0,
        "subject_activation_reachability": _reachability(rate),
        "time_weighted_reachability": _reachability(signal / total if total else 0.0),
        "reachability": _reachability(rate),
    }


def build_audit(source: Path, sample_size: int) -> dict[str, Any]:
    rows = _load_rows(source)[:sample_size]
    engine = KundliEngine()
    audited = [result for row in rows if (result := _audit_row(row, engine)) is not None]
    positive_fixture = evaluate({"fifth_lord_house": 5, "fifth_lord_exalted": False, "fifth_lord_conjunct_jupiter": True, "fifth_lord_aspected_by_jupiter": False, "mahadasha": "Jupiter", "antardasha": "Sun", "sun_house": 5, "sun_exalted": False, "sun_own_sign": False, "sun_strong": True, "sun_house_from_mahadasha_lord": 5})
    negative_fixture = evaluate({"fifth_lord_house": 5, "fifth_lord_exalted": False, "fifth_lord_conjunct_jupiter": True, "fifth_lord_aspected_by_jupiter": False, "mahadasha": "Jupiter", "antardasha": "Sun", "sun_house": 12, "sun_exalted": False, "sun_own_sign": False, "sun_strong": True, "sun_house_from_mahadasha_lord": 12})
    indeterminate_fixture = evaluate({"fifth_lord_house": None, "mahadasha": "Jupiter"})
    metrics = _metrics(audited)
    expected = {str(n): round(n * metrics["time_weighted_signal_prevalence"], 6) for n in (10, 25, 50, 100, 250)}
    if metrics["time_weighted_signal_prevalence"] == 0:
        viability = "FAIL_ZERO_VARIANCE"
        classification = "ZERO_VARIANCE_SIGNAL_AT_EMP010"
    elif metrics["time_weighted_signal_prevalence"] < 0.01:
        viability = "INSUFFICIENT_PREVALENCE"
        classification = "SIGNAL_TOO_SPARSE_TO_TEST_AT_EMP010"
    elif metrics["time_weighted_signal_prevalence"] < 0.03:
        viability = "LOW_PREVALENCE"
        classification = "SIGNAL_TOO_SPARSE_TO_TEST_AT_EMP010"
    else:
        viability = "PASS"
        classification = "NO_SEPARATION"
    return {
        "activity_id": "VEDA-SIGNAL-PROGENY-001-RX",
        "status": "COMPLETED_OUTCOME_BLIND_AUDIT",
        "signal": {"id": SIGNAL_ID, "version": SIGNAL_VERSION, "hash": SIGNAL_HASH, "changed": False},
        "source": {"url": OGDB_URL, "selection": "deterministic OGDB OGID ordering; timed birth rows only; no childbirth labels joined", "sample_size_requested": sample_size, "sample_hash": _hash([row["ogid"] for row in audited])},
        "implementation": {"positive_fixture": positive_fixture, "negative_fixture": negative_fixture, "indeterminate_fixture": indeterminate_fixture, "positive_reachable": positive_fixture["state"] == "SIGNAL_PRESENT", "defect_found": False, "d1_only": True, "d7_used": False, "observation_rule": OBSERVATION_RULE},
        "population": metrics,
        "feasibility": {"expected_signal_positive_cases": expected, "thresholds_frozen_before_population": THRESHOLDS, "empirical_viability": viability, "emp010_reclassification": classification},
        "sparsity_cause": (
            "STRUCTURAL_FILTER" if metrics["structural_condition_rate"] < 0.03 else
            "DASHA_FILTER" if metrics["jupiter_md_sun_ad_rate"] < 0.03 else
            "COMBINED_FILTER" if metrics["combined_signal_rate"] < metrics["structural_and_timing_rate"] * 0.5 else
            "DASHA_FILTER"
        ),
        "audited_rows": audited,
        "code_commit": CODE_BASELINE,
        "scoring_spec": {"version": SCORING_SPEC_VERSION, "hash": _hash({"version": SCORING_SPEC_VERSION, "observation_rule": OBSERVATION_RULE, "signal_hash": SIGNAL_HASH})},
        "outcome_blind": True,
        "production_changes": "NONE",
        "pred_m4": "UNCHANGED",
        "rag": "UNCHANGED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sample-size", type=int, default=500)
    args = parser.parse_args()
    result = build_audit(args.source, args.sample_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"subjects": result["population"]["subjects_analyzed"], "activation_rate": result["population"]["subject_activation_rate"], "time_weighted": result["population"]["time_weighted_signal_prevalence"], "viability": result["feasibility"]["empirical_viability"], "positive_fixture": result["implementation"]["positive_reachable"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
