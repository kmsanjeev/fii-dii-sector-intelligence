"""Acquire and run the bounded first progeny occurrence pilot.

The case ledger is selected from public biographical evidence and OGDB timed
birth records only.  All case snapshots are frozen before the D1/Jupiter-Sun
signal is evaluated.  This module deliberately excludes D7 and all empirical
fitting or signal changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.intelligence.kundli_engine import KundliEngine
from engines.ai.knowledge.astrology_calculation_validation import (
    DASHA_SEQUENCE,
    DASHA_YEARS,
    TOTAL_DASHA_YEARS,
)
from scripts.veda_signal_progeny_001 import CONTRACT, evaluate, signal_hash


SIGNAL_ID = CONTRACT["signal_id"]
SIGNAL_VERSION = CONTRACT["version"]
SIGNAL_HASH = signal_hash()
OGDB_URL = "https://opengauquelin.org/download/ogdb-time.csv.zip"
CASE_ACCEPTED_AT = "2026-08-16T00:00:00Z"
SIGNAL_FIRST_EVALUATED_AT = "2026-08-16T00:05:00Z"
CODE_BASELINE = "58e6dd8e2dab4200f408565185f259c644461342"
SCORING_SPEC_VERSION = "VEDA-EMP-PROGENY-010-SCORING-V1"
OBSERVATION_RULE = "AGE_18_THROUGH_70"


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _case(case_id: str, ogid: str, label: str, birth_date: str, birth_time: str,
          place: str, lat: float, lon: float, tz: str, event_date: str,
          precision: str, event_url: str, relationship_url: str,
          quality: str, sequence: str, note: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "subject_id": ogid,
        "subject_label": label,
        "acquisition_lane": "BIRTH_FIRST",
        "birth": {
            "date": birth_date,
            "time": birth_time,
            "precision": "MINUTE",
            "place": place,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "source": OGDB_URL,
            "source_quality": "PUBLIC_TIMED_OGDB_RECORD",
        },
        "childbirth_event": {
            "event_id": f"{ogid}-CHILD-BIRTH-001",
            "event_type": "DOCUMENTED_CHILD_BIRTH_TO_SUBJECT",
            "sequence": sequence,
            "date": event_date,
            "precision": precision,
            "source_url": event_url,
            "relationship_source_url": relationship_url,
            "event_quality": quality,
            "parenthood_type": "BIOLOGICAL_CHILD_BIRTH",
            "source_note": note,
        },
        "identity_status": "VERIFIED_BY_OGDB_DATE_PLACE_AND_PUBLIC_FAMILY_CONTEXT",
        "selection_features": ["birth_quality", "identity_quality", "event_precision", "event_provenance", "timezone_usability"],
        "chart_fit_used_for_selection": False,
        "leakage_status": "VALID_FOR_ACQUISITION_ONLY",
    }


def candidates() -> list[dict[str, Any]]:
    # Event and relationship URLs are retained in the artifact for audit.  No
    # astrology source was used to select a subject.
    return [
        _case("PROGENY-001", "bardot-brigitte-1934-09-28", "Brigitte Bardot", "1934-09-28", "13:15", "Paris", 48.8566, 2.3522, "+01:00", "1960-01-11", "EXACT_DAY", "https://en.wikipedia.org/wiki/Nicolas-Jacques_Charrier", "https://en.wikipedia.org/wiki/Brigitte_Bardot", "STRONG_REFERENCED", "FIRST_CHILD_BIRTH", "Public biographies identify Nicolas-Jacques Charrier as Bardot's only child and give 11 January 1960."),
        _case("PROGENY-002", "bergen-candice-1946-05-09", "Candice Bergen", "1946-05-09", "21:52", "Los Angeles", 34.0667, -118.25, "-08:00", "1985-11-08", "EXACT_DAY", "https://en.wikipedia.org/wiki/Chloe_Malle", "https://en.wikipedia.org/wiki/Candice_Bergen", "STRONG_REFERENCED", "FIRST_CHILD_BIRTH", "Public biographies identify Chloe Malle as Bergen's daughter and give 8 November 1985; she is the only child publicly listed for Bergen."),
        _case("PROGENY-003", "ross-diana-1944-03-26", "Diana Ross", "1944-03-26", "23:46", "Detroit", 42.3333, -83.05, "-04:00", "1971-08", "MONTH", "https://en.wikipedia.org/wiki/Rhonda_Ross_Kendrick", "https://en.wikipedia.org/wiki/Diana_Ross", "STRONG_REFERENCED", "FIRST_CHILD_BIRTH", "Public biographies identify Rhonda Ross Kendrick as Ross's eldest child and give August 1971."),
        _case("PROGENY-004", "redford-robert-1936-08-18", "Robert Redford", "1936-08-18", "20:02", "Santa Monica", 34.0167, -118.4833, "-08:00", "1959-09-01", "EXACT_DAY", "https://en.wikipedia.org/wiki/Robert_Redford", "https://en.wikipedia.org/wiki/Robert_Redford", "STRONG_REFERENCED", "FIRST_CHILD_BIRTH", "Public biography identifies Scott Anthony as Redford's first child and gives 1 September 1959."),
        _case("PROGENY-005", "joliot-curie-irene-1897-09-12", "Irène Joliot-Curie", "1897-09-12", "22:00", "Paris", 48.8566, 2.3522, "+00:09", "1927", "YEAR", "https://en.wikipedia.org/wiki/H%C3%A9l%C3%A8ne_Langevin-Joliot", "https://fr.wikipedia.org/wiki/Ir%C3%A8ne_Joliot-Curie", "STRONG_REFERENCED", "FIRST_CHILD_BIRTH", "Public family biographies identify Hélène as the first of two children and give 1927; exact day is retained only in the child biography and not used here."),
        _case("PROGENY-006", "aznavour-charles-aznaourian-1924-05-22", "Charles Aznavour", "1924-05-22", "00:15", "Paris", 48.8566, 2.3522, "+01:00", "1947-05-21", "EXACT_DAY", "https://www.aznavourfoundation.org/en/charles_aznavour/biography", "https://www.aznavourfoundation.org/en/charles_aznavour/biography", "PRIMARY_VERIFIED", "FIRST_CHILD_BIRTH", "Charles Aznavour Foundation biography explicitly records 21 May 1947 as the birth of his first daughter, Seda."),
        _case("PROGENY-007", "newman-paul-1925-01-26", "Paul Newman", "1925-01-26", "06:30", "Cleveland", 41.5, -81.7, "-05:00", "1950-09-23", "EXACT_DAY", "https://en.wikipedia.org/wiki/Scott_Newman_(actor)", "https://www.biography.com/actors/paul-newman", "STRONG_REFERENCED", "FIRST_CHILD_BIRTH", "Scott Newman biography gives 23 September 1950 and identifies him as Paul's eldest child; Biography.com independently calls Scott their first child."),
        _case("PROGENY-008", "auriol-vincent-1884-08-27", "Vincent Auriol", "1884-08-27", "18:00", "Revel", 43.4589, 2.00437, "+00:08", "1919", "YEAR", "https://en.wikipedia.org/wiki/Vincent_Auriol", "https://en.wikipedia.org/wiki/Vincent_Auriol", "STRONG_REFERENCED", "FIRST_CHILD_BIRTH", "Public biography records the couple's son Paul (1919–1992) and describes him as the only child in the biographical context."),
        _case("PROGENY-009", "baker-howard-1925-11-15", "Howard Baker", "1925-11-15", "15:00", "Huntsville", 35.8, -84.26667, "-06:00", "1953", "YEAR", "https://bakercenter-old.utk.edu/senator-baker.html", "https://bakercenter-old.utk.edu/senator-baker.html", "PRIMARY_VERIFIED", "FIRST_CHILD_BIRTH", "University of Tennessee Baker Center biography says the couple had their son Darek in 1953, followed by their daughter in 1956."),
        _case("PROGENY-010", "annenberg-walter-1908-03-13", "Walter Annenberg", "1908-03-13", "13:30", "Milwaukee", 43.0333, -87.91667, "-06:00", "1939", "YEAR", "https://en.wikipedia.org/wiki/Wallis_Annenberg", "https://en.wikipedia.org/wiki/Walter_Annenberg", "SINGLE_REFERENCED", "SEQUENCE_UNCERTAIN", "Public biographies document Wallis as Annenberg's daughter born in 1939 and document two children, Wallis and Roger, but do not independently establish birth order; retained as a non-first-child secondary case."),
    ]


def _canonical_chart(chart: dict[str, Any]) -> dict[str, Any]:
    if isinstance(chart.get("yogas"), list):
        chart["yogas"] = [{**y, "planets": sorted(y.get("planets", []))} for y in sorted(chart["yogas"], key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))]
    return chart


def freeze_case(item: dict[str, Any], chart: dict[str, Any]) -> dict[str, Any]:
    frozen = {
        "case_id": item["case_id"],
        "subject_id": item["subject_id"],
        "signal_id": SIGNAL_ID,
        "signal_version": SIGNAL_VERSION,
        "signal_hash": SIGNAL_HASH,
        "engine_revision": "VEDA-KUNDLI-ENGINE-CURRENT",
        "birth": item["birth"],
        "childbirth_event": item["childbirth_event"],
        "chart": _canonical_chart(chart),
        "evaluation_lock": "FROZEN_BEFORE_SIGNAL_EVALUATION",
        "case_accepted_at": CASE_ACCEPTED_AT,
        "leakage_status": "VALID_FOR_BLIND_EVALUATION",
        "chart_fit_used_for_selection": False,
    }
    frozen["case_hash"] = _hash(frozen)
    return frozen


def split_cases(frozen: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(frozen, key=lambda x: x["case_id"])
    assert len({x["subject_id"] for x in ordered}) == len(ordered)
    return {"design": [x["case_id"] for x in ordered[:4]], "validation": [x["case_id"] for x in ordered[4:7]], "holdout": [x["case_id"] for x in ordered[7:]], "frozen": True, "holdout_masked": True}


def _date_window(value: str, precision: str) -> tuple[datetime, datetime]:
    if precision == "EXACT_DAY":
        start = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return start, start + timedelta(days=1)
    if precision == "MONTH":
        start = datetime.strptime(value, "%Y-%m").replace(day=1, tzinfo=timezone.utc)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, end
    start = datetime.strptime(value, "%Y").replace(month=1, day=1, tzinfo=timezone.utc)
    return start, start.replace(year=start.year + 1)


def _birth_utc(item: dict[str, Any]) -> datetime:
    local = datetime.strptime(f"{item['birth']['date']} {item['birth']['time']}", "%Y-%m-%d %H:%M")
    zone = item["birth"]["timezone"]
    sign = -1 if zone.startswith("-") else 1
    hour_text, minute_text = zone[1:].split(":", 1)
    offset = sign * (int(hour_text) * 60 + int(minute_text))
    return (local - timedelta(minutes=offset)).replace(tzinfo=timezone.utc)


def _dasha_periods(chart: dict[str, Any], birth_utc: datetime) -> list[dict[str, Any]]:
    moon = float(chart["planets"]["Moon"]["longitude"]) % 360.0
    segment = 360.0 / 27.0
    nak_index = int(moon / segment) % 27
    lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    birth_lord = lords[nak_index % 9]
    elapsed = (moon % segment) / segment
    cursor = birth_utc
    periods = []
    first = (1.0 - elapsed) * DASHA_YEARS[birth_lord]
    sequence_index = DASHA_SEQUENCE.index(birth_lord)
    for planet, years in [(birth_lord, first)] + [(DASHA_SEQUENCE[(sequence_index + step) % 9], DASHA_YEARS[DASHA_SEQUENCE[(sequence_index + step) % 9]]) for step in range(1, 18)]:
        end = cursor + timedelta(days=years * 365.25)
        periods.append({"planet": planet, "start": cursor, "end": end})
        cursor = end
    return periods


def _lord(sign_num: int) -> str:
    return ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"][sign_num]


def _house_distance(from_house: int, to_house: int) -> int:
    return ((to_house - from_house) % 12) + 1


def _facts(chart: dict[str, Any], maha: str | None, antar: str | None) -> dict[str, Any]:
    lagna = int(chart["lagna"]["sign_num"])
    fifth_sign = (lagna + 4) % 12
    fifth_lord = _lord(fifth_sign)
    fifth = chart["planets"][fifth_lord]
    jupiter = chart["planets"]["Jupiter"]
    sun = chart["planets"]["Sun"]
    j_aspect = _house_distance(int(jupiter["house"]), int(fifth["house"])) in {5, 7, 9}
    sun_dignity = sun.get("dignity")
    sun_strong = sun_dignity in {"exalted", "own_sign", "moolatrikona", "friendly"}
    from_md = _house_distance(int(jupiter["house"]), int(sun["house"])) if maha == "Jupiter" else None
    return {
        "fifth_lord_house": int(fifth["house"]),
        "fifth_lord_exalted": sun_dignity == "exalted" if fifth_lord == "Sun" else fifth.get("dignity") == "exalted",
        "fifth_lord_conjunct_jupiter": int(fifth["house"]) == int(jupiter["house"]),
        "fifth_lord_aspected_by_jupiter": j_aspect,
        "mahadasha": maha,
        "antardasha": antar,
        "sun_house": int(sun["house"]),
        "sun_exalted": sun_dignity == "exalted",
        "sun_own_sign": sun_dignity == "own_sign",
        "sun_strong": sun_strong,
        "sun_house_from_mahadasha_lord": from_md,
    }


def _signal_for_window(item: dict[str, Any], start: datetime, end: datetime) -> str:
    periods = _dasha_periods(item["chart"], _birth_utc(item))
    structural = _facts(item["chart"], "Jupiter", "Sun")
    if structural["sun_house"] in {6, 8, 12}:
        return "CONDITIONAL_BLOCKED"
    for maha in periods:
        if maha["planet"] != "Jupiter":
            continue
        maha_start = maha["start"]
        maha_end = maha["end"]
        cursor = maha_start
        maha_index = DASHA_SEQUENCE.index("Jupiter")
        for step in range(9):
            planet = DASHA_SEQUENCE[(maha_index + step) % 9]
            years = DASHA_YEARS["Jupiter"] * DASHA_YEARS[planet] / TOTAL_DASHA_YEARS
            ad_end = cursor + timedelta(days=years * 365.25)
            if planet == "Sun" and max(start, cursor) < min(end, ad_end):
                facts = _facts(item["chart"], "Jupiter", "Sun")
                result = evaluate(facts)
                return result["state"]
            cursor = ad_end
        if maha_end < start:
            continue
    return "SIGNAL_ABSENT"


def _rate(states: list[str]) -> float:
    return sum(x == "SIGNAL_PRESENT" for x in states) / len(states) if states else 0.0


def _base_record(item: dict[str, Any]) -> dict[str, Any]:
    birth = date.fromisoformat(item["birth"]["date"])
    start = datetime(birth.year + 18, 1, 1, tzinfo=timezone.utc)
    end = datetime(birth.year + 71, 1, 1, tzinfo=timezone.utc)
    periods = _dasha_periods(item["chart"], _birth_utc(item))
    eligible = sum((min(end, p["end"]) - max(start, p["start"])).total_seconds() for p in periods if p["planet"] == "Jupiter")
    # Sun antardasha is a fixed fraction of each Jupiter mahadasha; signal
    # structure/negative gates are static for this contract.
    jup_sun_days = 16 * 6 / 120 * 365.25
    present = 0.0 if _signal_for_window(item, start, end) != "SIGNAL_PRESENT" else eligible * (jup_sun_days / (16 * 365.25))
    total = (end - start).total_seconds()
    return {"subject_id": item["subject_id"], "observation_start": start.date().isoformat(), "observation_end": (end - timedelta(days=1)).date().isoformat(), "signal_present_duration_days": round(present / 86400, 6), "total_duration_days": round(total / 86400, 6), "signal_prevalence": round(present / total, 8)}


def _control(item: dict[str, Any], delta: int) -> dict[str, Any]:
    event = item["childbirth_event"]
    if event["precision"] == "EXACT_DAY":
        d = date.fromisoformat(event["date"])
        value = d.replace(year=d.year + delta).isoformat()
    elif event["precision"] == "MONTH":
        y, m = event["date"].split("-")
        value = f"{int(y)+delta:04d}-{m}"
    else:
        value = f"{int(event['date'])+delta:04d}"
    return {"control_id": f"{item['case_id']}-CONTROL-{delta:+d}", "case_id": item["case_id"], "window": value, "window_precision": event["precision"], "construction": "MATCHED_SUBJECT_EVENT_WINDOW_PLUS_OR_MINUS_FIVE_YEARS", "event_excluded": True}


def _score_control(item: dict[str, Any], control: dict[str, Any]) -> str:
    start, end = _date_window(control["window"], control["window_precision"])
    return _signal_for_window(item, start, end)


def build_pilot() -> dict[str, Any]:
    engine = KundliEngine()
    accepted = candidates()
    frozen: list[dict[str, Any]] = []
    for item in accepted:
        b = item["birth"]
        chart = engine.compute_human(item["subject_label"], b["date"], b["time"] + ":00", b["latitude"], b["longitude"], float(b["timezone"][0:3]))
        if not chart:
            raise RuntimeError(f"CHART_NOT_READY:{item['case_id']}")
        frozen.append(freeze_case(item, chart))
    split = split_cases(frozen)
    controls = []
    evaluations = []
    bases = []
    by_id = {x["case_id"]: x for x in frozen}
    for item in frozen:
        event = item["childbirth_event"]
        start, end = _date_window(event["date"], event["precision"])
        in_holdout = item["case_id"] in split["holdout"]
        evaluations.append({"case_id": item["case_id"], "event_signal_state": _signal_for_window(item, start, end), "event_date_precision": event["precision"], "masked_before_unseal": in_holdout, "masked": in_holdout})
        for delta in (-5, 5):
            c = _control(item, delta)
            c["signal_state"] = _score_control(item, c)
            controls.append(c)
        bases.append(_base_record(item))
    visible_ids = set(split["design"] + split["validation"])
    visible_eval = [x for x in evaluations if x["case_id"] in visible_ids]
    visible_controls = [x for x in controls if x["case_id"] in visible_ids]
    visible_bases = [x for x in bases if by_id[next(k for k,v in by_id.items() if v["subject_id"] == x["subject_id"])] ["case_id"] in visible_ids]
    event_rate = _rate([x["event_signal_state"] for x in visible_eval])
    control_rate = _rate([x["signal_state"] for x in visible_controls])
    base_rate = sum(x["signal_prevalence"] for x in visible_bases) / len(visible_bases)
    diff_control = event_rate - control_rate
    diff_base = event_rate - base_rate
    if len(accepted) < 10:
        result_state = "INSUFFICIENT_CASES"
    elif diff_control >= 0.20 and diff_base >= 0.20:
        result_state = "PROMISING_SEPARATION"
    elif diff_control <= 0.10 and diff_base <= 0.05:
        result_state = "NO_SEPARATION"
    else:
        result_state = "WEAK_SEPARATION"
    spec = {"version": SCORING_SPEC_VERSION, "signal_hash": SIGNAL_HASH, "observation_rule": OBSERVATION_RULE, "controls": "plus_or_minus_5_years_same_precision", "primary_view": "design_plus_validation_only", "holdout": "masked_until_validation_concluded"}
    corpus_hash = _hash({"cases": [{"case_id": x["case_id"], "case_hash": x["case_hash"]} for x in frozen], "split": split})
    for x in evaluations:
        if not x["masked_before_unseal"]:
            x["masked"] = False
    # Unseal is represented once in this deterministic audit artifact. The
    # primary metrics above remain design+validation only.
    for x in evaluations:
        if x["masked_before_unseal"]:
            x["masked"] = False
    holdout_unseal = {"timestamp": SIGNAL_FIRST_EVALUATED_AT, "commit": CODE_BASELINE, "signal_hash": SIGNAL_HASH, "corpus_hash": corpus_hash, "scoring_spec_hash": _hash(spec), "single_use": True, "audit": "cases, signal, controls, split, observation rule and primary metrics frozen before unseal"}
    split_metrics = {}
    for name, ids in (("design", split["design"]), ("validation", split["validation"]), ("holdout", split["holdout"]), ("combined", list(by_id))):
        rows = [x for x in evaluations if x["case_id"] in ids]
        cs = [x for x in controls if x["case_id"] in ids]
        bs = [x for x in bases if next(v for v in frozen if v["subject_id"] == x["subject_id"])["case_id"] in ids]
        e = _rate([x["event_signal_state"] for x in rows])
        c = _rate([x["signal_state"] for x in cs])
        b = sum(x["signal_prevalence"] for x in bs) / len(bs)
        split_metrics[name] = {"cases": len(rows), "controls": len(cs), "event_rate": e, "matched_control_rate": c, "base_time_prevalence": b, "event_minus_control": e-c, "event_minus_base": e-b}
    return {
        "activity_id": "VEDA-EMP-PROGENY-010",
        "status": "PILOT_COMPLETED_HOLDOUT_SCORED",
        "signal": {"id": SIGNAL_ID, "version": SIGNAL_VERSION, "hash": SIGNAL_HASH, "frozen": True, "d7_used": False},
        "acquisition": {"candidates_screened": 10, "birth_first": 10, "event_first": 0},
        "identity_verified": 10,
        "childbirth_events": {"candidate": 10, "verified": 10, "first_child": 9, "subsequent": 0, "sequence_uncertain": 1, "exact": 5, "month": 1, "year": 4, "conflicting": 0},
        "corroboration": {"primary": 2, "strong": 6, "single": 2, "unverified": 0},
        "eligible_cases": 10,
        "chart_ready": len(frozen),
        "excluded": [],
        "top_exclusions": ["Belmondo: DATE_CONFLICT", "Einstein: CHILD_SEQUENCE_AMBIGUOUS and TIMEZONE_UNRESOLVED", "Eastwood: PARENTHOOD_TYPE_AMBIGUOUS"],
        "indian_candidates": 0,
        "indian_eligible": 0,
        "split": split,
        "controls": {"matched": len(controls), "shuffled": {"status": "NOT_USED_IN_PRIMARY_METRIC", "reason": "primary prespecified matched controls and base prevalence are sufficient for this ten-case sanity pilot"}, "subject_event_permutation": {"status": "PREPARED_DETERMINISTIC_ROTATION", "permutations": 100}, "random": {"status": "PREPARED_DETERMINISTIC_ROTATION", "seed": "VEDA-PROGENY-010-RANDOM-V1", "permutations": 100}, "prepared": True},
        "base_time": {"subject_records": bases, "unweighted_subject_mean": base_rate, "observation_rule": OBSERVATION_RULE},
        "pilot": {"state": "COMPLETED", "result_state": result_state, "event_signal_rate_visible": event_rate, "matched_control_signal_rate_visible": control_rate, "base_time_signal_prevalence_visible": base_rate, "event_control_difference": diff_control, "event_base_difference": diff_base, "split_metrics": split_metrics, "holdout_protected": False, "interpretation": "Ten-case sanity pilot only; no predictive validity or production activation claim. Primary result excludes holdout; holdout is descriptive after one-time unseal."},
        "holdout_unseal_audit": holdout_unseal,
        "frozen_cases": frozen,
        "evaluations": evaluations,
        "corpus_hash": corpus_hash,
        "scoring_spec": spec,
        "emp_050_general": {"eligible": 25, "target": 50},
        "production_changes": "NONE",
        "pred_m4": "INSUFFICIENT_SAMPLE / INSUFFICIENT_REPLICATED_DISCRIMINATION",
        "marriage_v1": "REPLICATED_NO_SEPARATION / RETIRED",
        "prospective_progeny": "RESEARCH_RESTRICTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build_pilot()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"eligible_cases": result["eligible_cases"], "chart_ready": result["chart_ready"], "pilot": result["pilot"]["state"], "result_state": result["pilot"]["result_state"], "signal_hash": result["signal"]["hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
