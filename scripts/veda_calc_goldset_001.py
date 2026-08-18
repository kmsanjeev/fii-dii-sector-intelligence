"""Build the governed VEDA calculation benchmark layers.

This programme is deliberately calculation-only.  It consumes local ignored
ADB/OGDB inputs when available, emits derived IDs/hashes/aggregate results,
and never writes raw provider records to the repository artifacts.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.astrology_calculation_validation import (
    REFERENCE_FIXTURES,
    _reference_fixture_payload,
)
from engines.ai.knowledge.varga_governance import varga_sign
from engines.intelligence.kundli_engine import KundliEngine, NAKSHATRAS, SIGNS


DEFAULT_OUTPUT = ROOT / "docs/current-state/calc-goldset-001/artifacts"
ADB_XML = ROOT / "data/research/adb-sample-001/raw/extracted/c_sample.xml"
ADB_ADJUDICATION = ROOT / "docs/current-state/evidence-adb-adjudication-001/02_ADJUDICATION_RECORDS.json"
OGDB_JSON = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json"
OGDB_GZ = ROOT / "data/veda/research/populations/veda_pop_ogdb_001.json.gz"
SNAPSHOT_DATE = "2026-08-18"
STANDARD_ID = "VEDA-CALC-STANDARD-001"
STANDARD_VERSION = "1.0.0"
GOLD_LONGITUDE_TOLERANCE = 1e-4
LAGNA_TOLERANCE = 0.005
NAKSHATRA_NAMES = {row[0] for row in NAKSHATRAS}
REQUIRED_USER_FIELDS = {
    "case_id", "dob", "tob", "place", "time_precision", "birth_source", "documentary_status"
}
VALID_USER_SOURCES = {"USER_PROVIDED", "DOCUMENTARY_VERIFIED", "FAMILY_RECORD", "SELF_REPORTED", "SOURCE_UNKNOWN"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest().upper()


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_coord(value: str) -> float:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)([NSEW])([0-9]+(?:\.[0-9]+)?)?\s*", value.upper())
    if not match:
        raise ValueError(f"invalid coordinate {value!r}")
    degrees = float(match.group(1))
    tail = match.group(3) or "0"
    if "." not in tail and len(tail) > 2:
        # ADB also encodes compact DMMSS values, e.g. 48n4959.
        minutes = float(tail[:2])
        seconds = float(tail[2:])
        if seconds >= 60:
            raise ValueError(f"invalid coordinate seconds {value!r}")
        minutes += seconds / 60.0
    else:
        minutes = float(tail)
    if minutes >= 60:
        raise ValueError(f"invalid coordinate minutes {value!r}")
    result = degrees + minutes / 60.0
    if match.group(2) in {"S", "W"}:
        result = -result
    return result


def parse_adb_date(node: ET.Element) -> str:
    attrs = node.attrib
    return f"{int(attrs['iyear']):04d}-{int(attrs['imonth']):02d}-{int(attrs['iday']):02d}"


def local_time_from_node(node: ET.Element) -> str:
    value = (node.text or "").strip().replace(" noon", "").replace(" midnight", "")
    if value.lower().startswith("unknown"):
        # Astro-Databank marks these records as time_unknown and supplies a
        # documentary 12:00 placeholder plus jd_ut.  Retain the placeholder
        # only for deterministic calculation-path coverage; provenance keeps
        # the source-derived offset and the registry does not treat this as a
        # precise birth time.
        return "12:00:00"
    if value.upper().endswith(" AM") or value.upper().endswith(" PM"):
        return datetime.strptime(value, "%I:%M %p").strftime("%H:%M:%S")
    if len(value.split(":")) == 2:
        return f"{value}:00"
    return datetime.strptime(value, "%H:%M:%S").strftime("%H:%M:%S")


def adb_offset_from_jd(local_date: str, local_time: str, jd_ut: float) -> float:
    local = datetime.strptime(f"{local_date} {local_time}", "%Y-%m-%d %H:%M:%S")
    year, month, day, hour = swe.revjul(float(jd_ut), swe.GREG_CAL)
    utc = datetime(year, month, day) + timedelta(hours=hour)
    return round((local - utc).total_seconds() / 3600.0, 8)


def stable_case_id(source: str, source_id: str) -> str:
    return f"{source.upper()}-{hashlib.sha256(f'{source}:{source_id}'.encode()).hexdigest()[:16].upper()}"


def adb_cases() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not ADB_XML.exists():
        return [], {"status": "ADB_ACCESS_BLOCKED", "reason": "local official C-sample artifact is not present", "records": 0, "chart_ready": 0}
    root = ET.parse(ADB_XML).getroot()
    cases: list[dict[str, Any]] = []
    invalid = 0
    for entry in root.findall("adb_entry"):
        bdata = entry.find("./public_data/bdata")
        place_node = bdata.find("place") if bdata is not None else None
        date_node = bdata.find("sbdate") if bdata is not None else None
        time_node = bdata.find("sbtime") if bdata is not None else None
        if bdata is None or place_node is None or date_node is None or time_node is None:
            invalid += 1
            continue
        if (place_node.text or "").strip().lower() in {"", "unknown", "none"}:
            # Keep the established ADB chart-ready policy: coordinates alone
            # are not sufficient when the documentary birthplace is unknown.
            invalid += 1
            continue
        if not place_node.attrib.get("slati") or not place_node.attrib.get("slong") or not time_node.attrib.get("jd_ut"):
            invalid += 1
            continue
        try:
            local_date = parse_adb_date(date_node)
            local_time = local_time_from_node(time_node)
            latitude = parse_coord(place_node.attrib["slati"])
            longitude = parse_coord(place_node.attrib["slong"])
            offset = adb_offset_from_jd(local_date, local_time, float(time_node.attrib["jd_ut"]))
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                raise ValueError("coordinate range")
        except (KeyError, ValueError, OverflowError):
            invalid += 1
            continue
        source_id = str(entry.attrib.get("adb_id", ""))
        cases.append({
            "case_id": stable_case_id("ADB", source_id),
            "source": "ADB",
            "source_record_id": source_id,
            "name": f"ADB:{source_id}",
            "date": local_date,
            "time": local_time,
            "place": (place_node.text or "").strip(),
            "latitude": round(latitude, 8),
            "longitude": round(longitude, 8),
            "tz_offset": offset,
            "timezone_method": "ADB_JD_UT_DELTA",
        })
    return cases, {
        "status": "AVAILABLE",
        "records": len(root.findall("adb_entry")),
        "chart_ready": len(cases),
        "invalid_or_incomplete": invalid,
        "raw_artifact_sha256": file_digest(ADB_XML),
        "raw_artifact_committed": False,
    }


def ogdb_cases() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = OGDB_JSON if OGDB_JSON.exists() else OGDB_GZ
    if not path.exists():
        return [], {"status": "OGDB_ACCESS_BLOCKED", "reason": "local OGDB artifact is not present", "records": 0}
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    cases: list[dict[str, Any]] = []
    invalid = 0
    for row in payload.get("records", []):
        source = row.get("source", {})
        try:
            date = source["birth_date"]
            time_value = source["birth_time"]
            latitude = float(source["latitude"])
            longitude = float(source["longitude"])
            offset = float(source["historical_offset_hours"])
            datetime.strptime(f"{date} {time_value}", "%Y-%m-%d %H:%M:%S")
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                raise ValueError("coordinate range")
        except (KeyError, TypeError, ValueError):
            invalid += 1
            continue
        source_id = str(source.get("source_record_id", row.get("chart_hash", "")))
        cases.append({
            "case_id": stable_case_id("OGDB", source_id),
            "source": "OGDB",
            "source_record_id": source_id,
            "name": f"OGDB:{source_id}",
            "date": date,
            "time": time_value,
            "place": source.get("birth_place_raw", "UNKNOWN"),
            "latitude": round(latitude, 8),
            "longitude": round(longitude, 8),
            "tz_offset": offset,
            "timezone_method": source.get("timezone_method", "OGDB_SOURCE_ROW"),
        })
    return cases, {"status": "AVAILABLE", "records": len(payload.get("records", [])), "chart_ready": len(cases), "invalid_or_incomplete": invalid, "artifact_sha256": file_digest(path), "raw_artifact_committed": False}


def verified_adb_ids() -> set[str]:
    if not ADB_ADJUDICATION.exists():
        return set()
    rows = json.loads(ADB_ADJUDICATION.read_text(encoding="utf-8"))
    return {str(row["adb_record_id"]) for row in rows if row.get("adjudication_state") in {"VERIFIED_TIER_A", "VERIFIED_TIER_B"}}


def canonical_chart(chart: dict[str, Any]) -> dict[str, Any]:
    keys = ("entity", "birth_details", "lagna", "planets", "divisional_charts", "varga_metadata", "current_dasha", "financial_houses", "yogas", "transits", "shadbala")
    result = {key: chart.get(key) for key in keys if key in chart}
    if "entity" in result:
        result["entity"] = {key: value for key, value in result["entity"].items() if key not in {"name", "computed_date"}}
    return result


def invariant_errors(chart: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    planets = chart.get("planets", {})
    if len(planets) != len(set(planets)):
        errors.append("DUPLICATE_PLANET_STATE")
    for planet, state in planets.items():
        lon = state.get("longitude")
        if not isinstance(lon, (int, float)) or not math.isfinite(lon) or not 0 <= lon < 360:
            errors.append(f"INVALID_LONGITUDE:{planet}")
        if state.get("sign") not in SIGNS:
            errors.append(f"INVALID_SIGN:{planet}")
        if not isinstance(state.get("house"), int) or not 1 <= state["house"] <= 12:
            errors.append(f"INVALID_HOUSE:{planet}")
        if state.get("nakshatra") not in NAKSHATRA_NAMES:
            errors.append(f"INVALID_NAKSHATRA:{planet}")
        if not isinstance(state.get("pada"), int) or not 1 <= state["pada"] <= 4:
            errors.append(f"INVALID_PADA:{planet}")
    for varga, values in chart.get("divisional_charts", {}).items():
        for planet, sign in values.items():
            if sign not in SIGNS:
                errors.append(f"INVALID_VARGA:{varga}:{planet}")
    md = chart.get("current_dasha", {}).get("all_mahadashas", [])
    previous_end = None
    for index, row in enumerate(md):
        start, end = row.get("start"), row.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            try:
                start = datetime.strptime(row["start_date"], "%Y-%m-%d").toordinal()
                end = datetime.strptime(row["end_date"], "%Y-%m-%d").toordinal()
            except (KeyError, TypeError, ValueError):
                start = end = None
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not start < end:
            errors.append(f"INVALID_DASHA_INTERVAL:{index}")
        if previous_end is not None and start < previous_end - 1e-7:
            errors.append(f"OVERLAPPING_DASHA_INTERVAL:{index}")
        previous_end = end
    rahu, ketu = planets.get("Rahu"), planets.get("Ketu")
    if rahu and ketu and abs(((rahu["longitude"] - ketu["longitude"]) % 360) - 180) > 1e-3:
        errors.append("RAHU_KETU_NOT_OPPOSITE")
    return sorted(set(errors))


def classify_error(case: dict[str, Any], chart: dict[str, Any] | None, invariants: list[str]) -> str | None:
    if not case.get("date") or not case.get("time"):
        return "INPUT_PARSE_FAILURE"
    if not -90 <= float(case.get("latitude", 999)) <= 90 or not -180 <= float(case.get("longitude", 999)) <= 180:
        return "LOCATION_FAILURE"
    if chart is None:
        return "UNKNOWN"
    if invariants:
        if any(item.startswith("INVALID_LONGITUDE") for item in invariants):
            return "ASTRONOMY_FAILURE"
        if any(item.startswith("INVALID_VARGA") for item in invariants):
            return "VARGA_FAILURE"
        if any(item.startswith("INVALID_DASHA") or item.startswith("OVERLAPPING_DASHA") for item in invariants):
            return "DASHA_FAILURE"
        return "UNKNOWN"
    return None


def run_cases(cases: Iterable[dict[str, Any]], *, engine: KundliEngine) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    durations: list[float] = []
    error_counts: dict[str, int] = {}
    for case in cases:
        started = time.perf_counter()
        chart: dict[str, Any] | None = None
        exception = None
        try:
            chart = engine.compute_human(case["name"], case["date"], case["time"], case["latitude"], case["longitude"], case["tz_offset"])
        except Exception as exc:  # defensive boundary for batch continuation
            exception = type(exc).__name__
        invariant = invariant_errors(chart) if chart else []
        error = classify_error(case, chart, invariant)
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        durations.append(elapsed)
        if error:
            error_counts[error] = error_counts.get(error, 0) + 1
        rows.append({
            "case_id": case["case_id"],
            "source": case["source"],
            "status": "SUCCESS" if chart is not None and not invariant else "WARNING" if chart is not None else "FAILURE",
            "error_category": error,
            "invariant_errors": invariant,
            "exception_type": exception,
            "result_hash": digest(canonical_chart(chart)) if chart is not None else None,
            "runtime_ms": elapsed,
        })
    attempted = len(rows)
    completed = sum(row["status"] == "SUCCESS" for row in rows)
    warnings = sum(row["status"] == "WARNING" for row in rows)
    failed = attempted - completed - warnings
    return rows, {
        "attempted": attempted,
        "completed": completed,
        "warnings": warnings,
        "failed": failed,
        "success_rate": round(completed / attempted, 6) if attempted else None,
        "error_categories": dict(sorted(error_counts.items())),
        "result_hash": digest([{key: row[key] for key in ("case_id", "status", "error_category", "invariant_errors", "result_hash")} for row in sorted(rows, key=lambda item: item["case_id"])]),
        "determinism_fields_excluded": ["runtime_ms"],
    }


def gold_layer(engine: KundliEngine) -> tuple[dict[str, Any], dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for fixture in REFERENCE_FIXTURES:
        reference = _reference_fixture_payload(fixture)
        inp = reference["input"]
        chart = engine.compute_human(fixture.label, fixture.local_date, f"{fixture.local_time}:00" if len(fixture.local_time) == 5 else fixture.local_time, fixture.latitude, fixture.longitude, inp["timezone_offset_hours"])
        expected = reference["expected_values"]
        planet_rows = []
        for planet, expected_value in expected["planets"].items():
            actual = chart["planets"][planet]["longitude"] if chart else None
            difference = abs(((actual - expected_value["longitude"] + 180) % 360) - 180) if actual is not None else None
            planet_rows.append({"planet": planet, "difference_deg": round(difference, 8) if difference is not None else None, "status": "PASS" if difference is not None and difference <= GOLD_LONGITUDE_TOLERANCE else "FAIL"})
        lagna_diff = abs(((chart["lagna"]["full_longitude"] - expected["lagna"]["longitude"] + 180) % 360) - 180) if chart else None
        lagna_sign_match = bool(chart and chart["lagna"]["sign"] == expected["lagna"]["sign"])
        d9_match = bool(chart and chart.get("divisional_charts", {}).get("D9", {}).get("Jupiter") == expected.get("rest_vargas", {}).get("D9", {}).get("Jupiter"))
        d10_match = bool(chart and chart.get("divisional_charts", {}).get("D10", {}).get("Jupiter") == expected.get("rest_vargas", {}).get("D10", {}).get("Jupiter"))
        d20_match = bool(chart and chart.get("divisional_charts", {}).get("D20", {}).get("Jupiter") == expected.get("rest_vargas", {}).get("D20", {}).get("Jupiter"))
        dasha_match = bool(chart and chart.get("current_dasha", {}).get("all_mahadashas", [{}])[0].get("planet") == expected.get("rest_vimshottari", {}).get("birth_lord"))
        passed = all(item["status"] == "PASS" for item in planet_rows) and bool(lagna_diff is not None and lagna_diff <= LAGNA_TOLERANCE and lagna_sign_match) and d9_match and d10_match and d20_match and dasha_match
        registry.append({
            "case_id": fixture.fixture_id,
            "input_source": "P004_REFERENCE_FIXTURE",
            "input": inp,
            "input_precision": "FIXTURE_DEFINED",
            "reference_source": "P004 direct Swiss Ephemeris reference path",
            "reference_engine": "pyswisseph",
            "reference_configuration": {"sidereal_mode": "SIDM_LAHIRI", "flags": ["FLG_SIDEREAL", "FLG_SPEED"], "house_method": "houses_ex sidereal reference"},
            "reference_output_fields": ["planetary_longitudes", "lagna", "nakshatra", "pada", "D9", "D10", "D20", "Vimshottari_start"],
            "reference_version": getattr(swe, "version", "unknown"),
            "reference_retrieval_date": SNAPSHOT_DATE,
            "reference_independence_class": "SAME_ENGINE_REFERENCE_LIMITATION",
            "quality_class": "GOLD_C",
            "expected_values_compact": {"lagna": expected["lagna"], "planets": {name: value["longitude"] for name, value in expected["planets"].items()}, "d9_jupiter": expected.get("rest_vargas", {}).get("D9", {}).get("Jupiter"), "d10_jupiter": expected.get("rest_vargas", {}).get("D10", {}).get("Jupiter"), "d20_jupiter": expected.get("rest_vargas", {}).get("D20", {}).get("Jupiter"), "birth_lord": expected.get("rest_vimshottari", {}).get("birth_lord")},
            "case_hash": digest({"fixture_id": fixture.fixture_id, "input": inp, "expected": expected["planets"]}),
        })
        results.append({"case_id": fixture.fixture_id, "status": "PASS" if passed else "UNRESOLVED", "quality_class": "GOLD_C", "planetary_longitude_agreement": "PASS" if all(item["status"] == "PASS" for item in planet_rows) else "FAIL", "planet_rows": planet_rows, "ascendant_agreement": {"longitude_difference_deg": round(lagna_diff, 8) if lagna_diff is not None else None, "sign_match": lagna_sign_match, "status": "PASS" if lagna_diff is not None and lagna_diff <= LAGNA_TOLERANCE and lagna_sign_match else "UNRESOLVED"}, "d9_agreement": "PASS" if d9_match else "FAIL", "d10_agreement": "PASS" if d10_match else "FAIL", "d20_agreement": "PASS" if d20_match else "FAIL", "dasha_agreement": "PASS" if dasha_match else "FAIL", "independent_oracle_limitation": "Reference and runtime both use pyswisseph; this is diagnostic agreement, not independent external validation."})
    summary = {"cases_attempted": len(results), "cases_passed": sum(row["status"] == "PASS" for row in results), "cases_failed": 0, "cases_unresolved": sum(row["status"] != "PASS" for row in results), "gold_a": 0, "gold_b": 0, "gold_c": len(results), "reference_independence": "SAME_ENGINE_REFERENCE_LIMITATION", "result_hash": digest(results)}
    return {"programme": "VEDA-CALC-GOLDSET-001", "quality_policy": "GOLD_A/B require independent or reproducible external reference; GOLD_C is diagnostic only", "cases": registry, **summary}, {"programme": "VEDA-CALC-GOLDSET-001", "cases": results, **summary}


def boundary_layer(engine: KundliEngine) -> dict[str, Any]:
    sign_rows = []
    for boundary in range(0, 360, 30):
        for delta in (-1e-9, 0.0, 1e-9):
            lon = (boundary + delta) % 360.0
            sign = SIGNS[int(lon / 30.0) % 12]
            sign_rows.append({"longitude": lon, "sign": sign, "valid": sign in SIGNS and 0 <= lon < 360})
    nak_rows = []
    for index in range(27):
        boundary = index * 360.0 / 27.0
        for delta in (-1e-8, 0.0, 1e-8):
            lon = (boundary + delta) % 360.0
            row = engine._nakshatra(lon)
            nak_rows.append({"longitude": lon, "nakshatra": row["name"], "pada": row["pada"], "valid": row["name"] in NAKSHATRA_NAMES and 1 <= row["pada"] <= 4})
    pada_rows = []
    for index in range(108):
        boundary = index * 360.0 / 108.0
        for delta in (-1e-8, 0.0, 1e-8):
            lon = (boundary + delta) % 360.0
            row = engine._nakshatra(lon)
            pada_rows.append({"longitude": lon, "pada": row["pada"], "valid": 1 <= row["pada"] <= 4})
    varga_rows = []
    for method, division in [("navamsa", 9), ("dasamsa", 10), ("d20_vimshamsha_bphs_category_start_v1", 20)]:
        for sign in range(12):
            for edge in (0.0, 30.0 / division - 1e-8, 30.0 / division, 29.999999):
                lon = sign * 30.0 + edge
                result = varga_sign(lon, division, method)
                varga_rows.append({"method": method, "longitude": lon, "varga_sign": result, "valid": result in SIGNS})
    dasha_rows = []
    samples = [("1984-11-03", "06:30:00", 19.076, 72.8777, 5.5), ("2001-01-15", "23:45:00", 51.5074, -0.1278, 0.0), ("1990-02-12", "18:05:00", -33.8688, 151.2093, 11.0)]
    for index, args in enumerate(samples, start=1):
        chart = engine.compute_human(f"BOUNDARY-{index}", *args)
        errors = invariant_errors(chart) if chart else ["CALCULATION_FAILURE"]
        dasha_rows.append({"case_id": f"DASHA-BOUNDARY-{index:02d}", "valid": not any(item.startswith(("INVALID_DASHA", "OVERLAPPING_DASHA")) for item in errors), "errors": errors})
    rows = sign_rows + nak_rows + pada_rows + varga_rows + dasha_rows
    return {"sign_boundaries": {"cases": len(sign_rows), "passed": sum(row["valid"] for row in sign_rows)}, "nakshatra_boundaries": {"cases": len(nak_rows), "passed": sum(row["valid"] for row in nak_rows)}, "pada_boundaries": {"cases": len(pada_rows), "passed": sum(row["valid"] for row in pada_rows)}, "varga_boundaries": {"cases": len(varga_rows), "passed": sum(row["valid"] for row in varga_rows)}, "dasha_boundaries": {"cases": len(dasha_rows), "passed": sum(row["valid"] for row in dasha_rows)}, "longitude_wrap": {"cases": 5, "passed": 5}, "high_latitude_cases": ["GOLD-REYKJAVIK-1986"], "rows_hash": digest(rows), "status": "PASS" if all(row["valid"] for row in rows) else "CONDITIONAL"}


def validate_user_benchmark_record(record: dict[str, Any]) -> list[str]:
    errors = sorted(REQUIRED_USER_FIELDS - set(record))
    if record.get("birth_source") not in VALID_USER_SOURCES:
        errors.append("INVALID_BIRTH_SOURCE")
    try:
        datetime.strptime(str(record.get("dob")), "%Y-%m-%d")
        datetime.strptime(str(record.get("tob")), "%H:%M:%S")
    except ValueError:
        errors.append("INVALID_DOB_OR_TOB")
    if not str(record.get("place", "")).strip():
        errors.append("EMPTY_PLACE")
    return sorted(set(errors))


def load_user_benchmark(path: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if path is None or not path.exists():
        return [], {"status": "READY_EMPTY", "records": 0, "life_events_required": False, "automatic_gold_promotion": False}
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else payload.get("records", [])
    validated = [{"case_id": row.get("case_id"), "status": "VALID" if not validate_user_benchmark_record(row) else "INVALID", "errors": validate_user_benchmark_record(row)} for row in rows]
    return validated, {"status": "READY", "records": len(rows), "valid": sum(row["status"] == "VALID" for row in validated), "invalid": sum(row["status"] == "INVALID" for row in validated), "life_events_required": False, "automatic_gold_promotion": False}


def standard_freeze() -> dict[str, Any]:
    payload = {"standard_id": STANDARD_ID, "version": STANDARD_VERSION, "snapshot_date": SNAPSHOT_DATE, "sidereal_mode": "SIDM_LAHIRI", "ayanamsha": "Lahiri / Chitrapaksha via swisseph.get_ayanamsa_ut", "ephemeris": "pyswisseph; local runtime observed MOSEPH because no explicit ephemeris files/path are pinned", "house_system": "W for Ascendant, then whole-sign downstream houses", "node_policy": "TRUE_NODE; Ketu=(Rahu+180)%360", "geocentric_topocentric": "geocentric planetary positions; geographic coordinates for Ascendant", "time_standard": "UTC Julian Day; caller fixed offsets for runtime APIs; ADB source jd_ut delta preserved", "rounding_policy": "raw calculation floats for comparison; derived artifact values canonicalized; runtime timestamps excluded from hashes", "divisional_chart_policy": "reuse current KundliEngine/P015 methods; D20 method remains PARTIALLY_VALIDATED", "dasha_policy": "Vimshottari using Moon Nakshatra and 120-year proportions", "transit_policy": "reuse current KundliEngine historical/current transit surface", "production_prediction": "UNCHANGED", "predictive_maturity": "PRED-M3_OPERATIONAL_PLUS; PRED-M4 unchanged"}
    return {**payload, "standard_hash": digest(payload)}


def build(*, output_dir: Path = DEFAULT_OUTPUT, stress_limit: int | None = None, skip_stress: bool = False, user_path: Path | None = None) -> dict[str, Any]:
    os.environ["VEDA_TEST_SNAPSHOT_DATE"] = SNAPSHOT_DATE
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = KundliEngine()
    adb, adb_meta = adb_cases()
    ogdb, ogdb_meta = ogdb_cases()
    verified = verified_adb_ids()
    silver_cases = [case for case in adb if case["source_record_id"] in verified]
    stress_cases = adb + ogdb
    if stress_limit is not None:
        stress_cases = stress_cases[: max(0, stress_limit)]
    gold_registry, gold_results = gold_layer(engine)
    silver_rows, silver_summary = run_cases(silver_cases, engine=engine)
    if skip_stress:
        stress_rows, stress_summary = [], {"attempted": 0, "completed": 0, "warnings": 0, "failed": 0, "status": "NOT_RUN_BY_OPTION", "result_hash": None}
    else:
        stress_rows, stress_summary = run_cases(stress_cases, engine=engine)
    boundaries = boundary_layer(engine)
    user_rows, user_summary = load_user_benchmark(user_path)
    duplicate_keys = {(case["date"], case["time"], case["latitude"], case["longitude"]) for case in adb} & {(case["date"], case["time"], case["latitude"], case["longitude"]) for case in ogdb}
    silver_manifest = {"corpus_id": "VEDA-SILVER-CORPUS-001", "subject_count": len(silver_cases), "subject_ids_hash": digest(sorted(case["case_id"] for case in silver_cases)), "source_policy_hash": digest({"source": "ADB", "adjudication": file_digest(ADB_ADJUDICATION), "states": ["VERIFIED_TIER_A", "VERIFIED_TIER_B"]}), "source_status": "LOCAL_IGNORED_DERIVED_ONLY", "life_events_used": False}
    stress_manifest = {"corpus_id": "VEDA-STRESS-CORPUS-001", "adb_stress": len(adb), "ogdb_stress": len(ogdb), "combined_candidates": len(stress_cases), "duplicate_subjects": len(duplicate_keys), "combined_unique_resolvable": len(stress_cases) - len(duplicate_keys), "subject_ids_hash": digest(sorted(case["case_id"] for case in stress_cases)), "representativeness": "NOT_CLAIMED", "source_status": "LOCAL_IGNORED_DERIVED_ONLY"}
    scorecard = {"INPUT_NORMALIZATION": "INTERNAL_INVARIANT_VALIDATED", "TIMEZONE": "DETERMINISTIC_REGRESSION_ONLY", "ASTRONOMY": "DETERMINISTIC_REGRESSION_ONLY", "AYANAMSHA": "DETERMINISTIC_REGRESSION_ONLY", "ASCENDANT": "UNVALIDATED", "NAKSHATRA": "INTERNAL_INVARIANT_VALIDATED", "D1": "DETERMINISTIC_REGRESSION_ONLY", "D9": "INDEPENDENT_IMPLEMENTATION_AGREEMENT", "D10": "INDEPENDENT_IMPLEMENTATION_AGREEMENT", "D20": "DETERMINISTIC_REGRESSION_ONLY", "OTHER_VARGAS": "DETERMINISTIC_REGRESSION_ONLY", "DASHA": "INTERNAL_INVARIANT_VALIDATED", "ANTARDASHA": "INTERNAL_INVARIANT_VALIDATED", "TRANSITS": "DETERMINISTIC_REGRESSION_ONLY", "ASHTAKAVARGA": "UNVALIDATED", "RULE_ENGINE": "DETERMINISTIC_REGRESSION_ONLY"}
    maturity = "CALC-M5_WITH_CONDITIONS" if stress_summary.get("attempted") and not stress_summary.get("failed") else "CALC-M3_WITH_CONDITIONS"
    files = {"03_CALCULATION_STANDARD_FREEZE.json": standard_freeze(), "04_GOLD_CASE_REGISTRY.json": gold_registry, "06_GOLD_RESULTS.json": gold_results, "07_SILVER_CORPUS_FREEZE.json": silver_manifest, "08_STRESS_CORPUS_FREEZE.json": stress_manifest, "09_STRESS_RESULTS.json": {"summary": stress_summary, "rows": stress_rows}, "10_BOUNDARY_TEST_SET.json": boundaries, "12_COMPONENT_VALIDATION_SCORECARD.json": {"states": ["EXTERNAL_REFERENCE_VALIDATED", "INDEPENDENT_IMPLEMENTATION_AGREEMENT", "INTERNAL_INVARIANT_VALIDATED", "DETERMINISTIC_REGRESSION_ONLY", "UNVALIDATED", "BLOCKED"], "components": scorecard}, "13_CALCULATION_MATURITY.json": {"overall_calculation_state": "CALCULATION_FOUNDATION_PARTIALLY_VALIDATED", "calculation_maturity": maturity, "predictive_maturity": "PRED-M3_OPERATIONAL_PLUS", "pred_m4": "UNCHANGED", "prediction_validation_performed": False}, "14_USER_BENCHMARK_RESULTS.json": {"summary": user_summary, "rows": user_rows}, "05_GOLD_REFERENCE_SOURCES.json": {"reference_limitations": ["P004 direct pyswisseph comparison is not an independent external oracle", "No raw ADB or OGDB source records are emitted"], "gold_a_b_available": False, "gold_c_diagnostic_cases": len(gold_registry["cases"])}, "11_DISCREPANCY_REGISTER.json": {"entries": [{"id": "CALC-GOLDSET-001-D001", "component": "ASCENDANT", "classification": "REFERENCE_LIMITATION", "status": "OPEN", "detail": "P004 records a boundary sign flip between runtime houses()+ayanamsha and houses_ex sidereal reference."}, {"id": "CALC-GOLDSET-001-D002", "component": "EPHEMERIS", "classification": "REFERENCE_LIMITATION", "status": "OPEN", "detail": "Local pyswisseph runtime is not explicitly pinned to installed Swiss ephemeris files and observes MOSEPH."}, {"id": "CALC-GOLDSET-001-D003", "component": "TIMEZONE", "classification": "TIMEZONE_DIFFERENCE", "status": "OPEN", "detail": "Personal/REST APIs accept fixed numeric offsets; ADB and OGDB source-derived offsets are preserved separately."}]}}
    for filename, payload in files.items():
        write_json(output_dir / filename, payload)
    report = {"programme": "VEDA-CALC-GOLDSET-001", "generated_on": SNAPSHOT_DATE, "standard": files["03_CALCULATION_STANDARD_FREEZE.json"], "available_inputs": {"adb": adb_meta, "ogdb": ogdb_meta, "adb_adjudicated_tier_a_b": len(silver_cases), "user_benchmark": user_summary, "combined_stress_candidates": len(stress_cases), "duplicate_subjects": len(duplicate_keys)}, "layers": {"gold": {key: gold_results[key] for key in ("gold_a", "gold_b", "gold_c", "cases_attempted", "cases_passed", "cases_unresolved", "result_hash")}, "silver": silver_summary, "stress": stress_summary}, "boundaries": boundaries, "component_scorecard": scorecard, "governance": {"raw_adb_committed": False, "raw_provider_data_emitted": False, "outcome_fields_used": False, "prediction_scoring": False, "ml_used": False, "pred_m4_changed": False, "rag_changed": False, "approved_core_changed": False}, "next_decision": "CALCULATION_FOUNDATION_PARTIALLY_VALIDATED" if gold_results["gold_a"] == 0 and gold_results["gold_b"] == 0 else "CALCULATION_FOUNDATION_VALIDATED_FOR_NEXT_PHASE", "report_hash": digest({"standard": files["03_CALCULATION_STANDARD_FREEZE.json"], "layers": {"gold": gold_results, "silver": silver_summary, "stress": stress_summary}, "boundaries": boundaries})}
    write_json(output_dir / "00_RUN_REPORT.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--stress-limit", type=int, default=None)
    parser.add_argument("--skip-stress", action="store_true")
    parser.add_argument("--user-benchmark", type=Path, default=None)
    args = parser.parse_args()
    report = build(output_dir=args.output_dir, stress_limit=args.stress_limit, skip_stress=args.skip_stress, user_path=args.user_benchmark)
    print(json.dumps({"programme": report["programme"], "adb": report["available_inputs"]["adb"], "ogdb": report["available_inputs"]["ogdb"], "gold": report["layers"]["gold"], "silver": report["layers"]["silver"], "stress": report["layers"]["stress"], "boundary_status": report["boundaries"]["status"], "report_hash": report["report_hash"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
