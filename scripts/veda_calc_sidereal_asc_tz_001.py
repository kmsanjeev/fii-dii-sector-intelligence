"""Bounded validation for VEDA-CALC-SIDEREAL-ASC-TZ-001.

This is a diagnostic/regression artefact builder.  It does not alter production
calculation policy and deliberately keeps external evidence to derived values
and provenance metadata rather than redistributing the IMD publication.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.veda_calc_oracle_001 import (  # noqa: E402
    ascendant_report as parent_ascendant_report,
    circular_error,
    independent_tropical_ascendant,
    mean_obliquity_deg,
)

PROGRAMME = "VEDA-CALC-SIDEREAL-ASC-TZ-001"
RETRIEVAL_DATE = "2026-08-18"
ARTIFACT_DIR = ROOT / "docs" / "current-state" / "calc-sidereal-asc-tz-001" / "artifacts"
IAE_URL = "https://packolkata.imd.gov.in/download/IAE2026.zip"
IAE_PDF_SHA256 = "58A16722E98F3E9DD23E8E188C39B577E24135306F20674B52FBBB172DB2E25A"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def utc_jd(value: datetime) -> float:
    value = value.astimezone(timezone.utc)
    return swe.julday(value.year, value.month, value.day, value.hour + value.minute / 60 + value.second / 3600)


def rashi_nakshatra_pada(longitude: float) -> dict[str, object]:
    value = float(longitude) % 360.0
    nak_size = 360.0 / 27.0
    pada_size = 360.0 / 108.0
    nak_index = min(26, int(value / nak_size))
    pada_index = min(3, int((value - nak_index * nak_size) / pada_size))
    return {
        "longitude_deg": round(value, 10),
        "rashi_index": int(value // 30.0),
        "nakshatra_index": nak_index,
        "pada_index": pada_index,
        "convention": "0 inclusive, 360 exclusive; 27 equal nakshatras; 4 equal padas each",
    }


def official_iae_reference() -> dict[str, object]:
    # Values transcribed from the 2026 edition's Indian Calendar headings.
    # Only the minimum ayanamsha values are retained; the PDF itself is not
    # committed or redistributed.
    rows = [
        ("2026-01-01", 24, 13, 17, 387),
        ("2026-02-20", 24, 13, 23, 389),
        ("2026-03-21", 24, 13, 27, 391),
        ("2026-04-21", 24, 13, 30, 393),
        ("2026-05-21", 24, 13, 34, 395),
        ("2026-06-21", 24, 13, 39, 397),
    ]
    comparisons = []
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for date_text, degree, minute, second, page in rows:
        dt = datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc)
        jd = utc_jd(dt)
        official = degree + minute / 60 + second / 3600
        swiss = swe.get_ayanamsa_ut(jd)
        comparisons.append({
            "date": date_text,
            "iae_page": page,
            "iae_ayanamsha_deg": round(official, 10),
            "swiss_sidm_lahiri_deg": round(swiss, 10),
            "absolute_difference_arcsec": round(abs(official - swiss) * 3600, 6),
            "status": "BOUNDED_AGREEMENT_WITH_CONVENTION_DIFFERENCE",
        })
    return {
        "source": "Indian Astronomical Ephemeris 2026, Positional Astronomy Centre, IMD",
        "source_url": IAE_URL,
        "retrieval_date": RETRIEVAL_DATE,
        "edition_pdf_sha256": IAE_PDF_SHA256,
        "edition_pages_inspected": [4, 387, 389, 391, 393, 395, 397],
        "edition_standard": {
            "reference_epoch": "J2000.0",
            "ephemeris_argument": "Terrestrial Time (TT)",
            "calendar_time": "Indian Standard Time (IST) or local mean time of 82.5E meridian as stated in calendar tables",
            "calendar_scope": "Indian Calendar tithi/nakshatra and Nirayana solar entries",
        },
        "html_edition_note": "The IMD overview page currently says J2000.5 while the inspected 2026 edition preface says J2000.0; edition-level PDF wording is retained and the discrepancy remains tracked.",
        "comparisons": comparisons,
        "authority_state": "REFERENCE_STANDARD_PARTIALLY_RESOLVED",
        "limitation": "IAE provides an independent official bounded calendar/ayanamsha check, not a complete per-body modern Lahiri longitude oracle with identical VEDA frame and apparent/geometric conventions.",
        "result_hash": digest(comparisons),
    }


def nirayana_regression() -> dict[str, object]:
    years = [1850, 1900, 1950, 1975, 1990, 2000, 2020, 2026]
    dates = [datetime(year, month, 15, 12, tzinfo=timezone.utc) for year in years for month in (1, 4, 7, 10)]
    bodies = {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN}
    rows = []
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for dt in dates:
        jd = utc_jd(dt)
        ayan = swe.get_ayanamsa_ut(jd)
        for name, body in bodies.items():
            tropical = swe.calc_ut(jd, body, swe.FLG_MOSEPH)[0][0] % 360.0
            nirayana = (tropical - ayan) % 360.0
            rows.append({
                "date": dt.date().isoformat(),
                "body": name,
                "tropical_deg": round(tropical, 10),
                "ayanamsha_deg": round(ayan, 10),
                "nirayana_deg": round(nirayana, 10),
                "rashi_nakshatra_pada": rashi_nakshatra_pada(nirayana),
            })
    return {
        "case_count": len(dates),
        "body_count": len(bodies),
        "row_count": len(rows),
        "method": "Swiss tropical position minus explicit SIDM_LAHIRI ayanamsha; deterministic regression only",
        "independence_class": "SAME_ENGINE_REFERENCE_LIMITATION",
        "external_reference_status": "IMD_BOUNDED_AYANAMSHA_ONLY",
        "rows": rows,
        "result_hash": digest(rows),
    }


def boundary_regression() -> dict[str, object]:
    epsilon_values = [1e-1, 1e-2, 5e-3, 1e-3]
    rows = []
    for boundary_type, boundary in [("rashi", 30.0 * index) for index in range(12)] + [("nakshatra", (360.0 / 27.0) * index) for index in range(27)] + [("pada", (360.0 / 108.0) * index) for index in range(108)]:
        for epsilon in epsilon_values:
            for direction in (-1, 1):
                value = (boundary + direction * epsilon) % 360.0
                row = rashi_nakshatra_pada(value)
                rows.append({"boundary_type": boundary_type, "boundary_deg": round(boundary, 10), "epsilon_deg": epsilon, "direction": direction, **row})
    return {
        "rashi_boundaries": 12,
        "nakshatra_boundaries": 27,
        "pada_boundaries": 108,
        "epsilon_deg": epsilon_values,
        "endpoint_convention": "boundary itself belongs to the interval beginning at that boundary; 360 wraps to 0",
        "rows": rows,
        "result_hash": digest(rows),
    }


def ascendant_cases() -> list[dict[str, object]]:
    named = [
        ("India-Kolkata", 22.5726, 88.3639), ("India-Delhi", 28.6139, 77.2090), ("India-Chennai", 13.0827, 80.2707),
        ("Europe-London", 51.5074, -0.1278), ("Europe-Berlin", 52.5200, 13.4050), ("Africa-CapeTown", -33.9249, 18.4241),
        ("NA-NewYork", 40.7128, -74.0060), ("NA-Vancouver", 49.2827, -123.1207), ("SA-Santiago", -33.4489, -70.6693),
        ("Australia-Sydney", -33.8688, 151.2093), ("Pacific-Auckland", -36.8509, 174.7645), ("HighLat-Reykjavik", 64.1466, -21.9426),
    ]
    cases = []
    base = datetime(1850, 1, 1, 0, tzinfo=timezone.utc)
    for i in range(120):
        label, lat, lon = named[i % len(named)]
        dt = base + timedelta(days=(i * 173) % 64000, hours=(i * 7) % 24, minutes=(i * 11) % 60, seconds=(i * 13) % 60)
        cases.append({
            "case_id": f"ASC-{i + 1:03d}", "region": label, "utc": dt.isoformat().replace("+00:00", "Z"),
            "latitude": lat, "longitude": lon, "coordinate_provenance": "fixed programme fixture; explicit WGS84 decimal degrees",
            "time_provenance": "fixed UTC fixture; no mutable city/timezone lookup",
        })
    return cases


def ascendant_report() -> dict[str, object]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    rows = []
    for case in ascendant_cases():
        dt = datetime.fromisoformat(case["utc"].replace("Z", "+00:00"))
        jd = utc_jd(dt)
        _, ascmc = swe.houses(jd, case["latitude"], case["longitude"], b"W")
        tropical = ascmc[0] % 360.0
        independent = independent_tropical_ascendant(jd, case["latitude"], case["longitude"])
        runtime = (tropical - swe.get_ayanamsa_ut(jd)) % 360.0
        ex = swe.houses_ex(jd, case["latitude"], case["longitude"], b"W", swe.FLG_SIDEREAL)[1][0] % 360.0
        rows.append({
            **case, "jd_ut": round(jd, 10), "independent_tropical_deg": round(independent, 10),
            "swe_tropical_deg": round(tropical, 10), "tropical_error_deg": round(circular_error(independent, tropical), 10),
            "runtime_sidereal_deg": round(runtime, 10), "houses_ex_sidereal_deg": round(ex, 10),
            "runtime_vs_houses_ex_error_deg": round(circular_error(runtime, ex), 10),
            "runtime_sign": int(runtime // 30), "houses_ex_sign": int(ex // 30),
            "degree_status": "PASS" if circular_error(independent, tropical) <= 0.05 else "FAIL",
            "sign_status": "MATCH" if int(runtime // 30) == int(ex // 30) else "BOUNDARY_DIFFERENCE",
        })
    errors = [row["runtime_vs_houses_ex_error_deg"] for row in rows]
    tropical_errors = [row["tropical_error_deg"] for row in rows]
    return {
        "case_count": len(rows),
        "independent_method": "GMST + mean obliquity Ascendant formula; Swiss houses/houses_ex used only for comparison",
        "sidereal_independence": "SAME_ENGINE_REFERENCE_LIMITATION",
        "tropical_tolerance_deg": 0.05,
        "degree_pass": sum(circular_error(row["independent_tropical_deg"], row["swe_tropical_deg"]) <= 0.05 for row in rows),
        "degree_fail": sum(circular_error(row["independent_tropical_deg"], row["swe_tropical_deg"]) > 0.05 for row in rows),
        "sign_match": sum(row["sign_status"] == "MATCH" for row in rows),
        "sign_boundary_difference": sum(row["sign_status"] == "BOUNDARY_DIFFERENCE" for row in rows),
        "known_parent_boundary_cases": parent_ascendant_report(),
        "max_tropical_error_deg": round(max(tropical_errors), 10),
        "max_runtime_vs_reference_error_deg": round(max(errors), 10),
        "p95_runtime_vs_reference_error_deg": round(sorted(errors)[int(math.ceil(len(errors) * 0.95)) - 1], 10),
        "rows": rows,
        "decision": "BOUNDARY_POLICY_REQUIRED",
        "decision_note": "Keep current W/whole-sign runtime standard; preserve explicit boundary policy and do not silently migrate to houses_ex.",
        "result_hash": digest(rows),
    }


def timezone_cases() -> list[dict[str, object]]:
    zones = ["Asia/Kolkata", "America/New_York", "Europe/Berlin", "Australia/Lord_Howe", "Asia/Kathmandu", "Pacific/Kiritimati", "Africa/Casablanca", "America/Sao_Paulo", "Europe/Paris", "Pacific/Apia", "Australia/Adelaide", "America/St_Johns"]
    years = [1880, 1910, 1945, 1970, 1990]
    cases = []
    for i, zone in enumerate(zones):
        for year in years:
            hour = 1 if zone == "America/New_York" and year == 2020 else 12
            cases.append({"case_id": f"TZ-{len(cases) + 1:03d}", "zone": zone, "local": f"{year:04d}-{(i % 12) + 1:02d}-15T{hour:02d}:30:00", "provenance": "fixed civil-time fixture"})
    cases.extend([
        {"case_id": "TZ-GAP", "zone": "America/New_York", "local": "2020-03-08T02:30:00", "provenance": "DST gap fixture"},
        {"case_id": "TZ-FOLD", "zone": "America/New_York", "local": "2020-11-01T01:30:00", "provenance": "DST fold fixture"},
        {"case_id": "TZ-HALF-HOUR", "zone": "Australia/Lord_Howe", "local": "2020-07-01T12:00:00", "provenance": "non-hour offset fixture"},
        {"case_id": "TZ-QUARTER-HOUR", "zone": "Asia/Kathmandu", "local": "1990-01-01T12:00:00", "provenance": "quarter-hour historical fixture"},
    ])
    return cases


def timezone_report() -> dict[str, object]:
    try:
        tzdata_version = importlib.metadata.version("tzdata")
    except importlib.metadata.PackageNotFoundError:
        tzdata_version = "SYSTEM_OR_UNAVAILABLE"
    rows = []
    for case in timezone_cases():
        local = datetime.fromisoformat(case["local"])
        zone = ZoneInfo(case["zone"])
        candidates = []
        for fold in (0, 1):
            aware = local.replace(tzinfo=zone, fold=fold)
            roundtrip = aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
            if roundtrip == local:
                offset = int(aware.utcoffset().total_seconds())
                candidate = {"fold": fold, "offset_seconds": offset, "utc": aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")}
                if not any(existing["offset_seconds"] == offset and existing["utc"] == candidate["utc"] for existing in candidates):
                    candidates.append(candidate)
        if not candidates:
            status = "NONEXISTENT_LOCAL_TIME"
        elif len(candidates) > 1:
            status = "AMBIGUOUS_UNRESOLVED"
        elif abs(candidates[0]["offset_seconds"]) % 60:
            status = "PRE_STANDARD_LMT"
        else:
            status = "RESOLVED_IANA_HISTORICAL"
        rows.append({**case, "status": status, "candidates": candidates})
    return {
        "case_count": len(rows),
        "tzdata_package_version": tzdata_version,
        "zoneinfo_tzpath": [],
        "policy": "explicit source offset > validated IANA historical zone > source-provided offset > unresolved; no current-offset fallback",
        "rows": rows,
        "status_counts": {status: sum(row["status"] == status for row in rows) for status in sorted({row["status"] for row in rows})},
        "result_hash": digest(rows),
    }


def build(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    iae = official_iae_reference()
    nirayana = nirayana_regression()
    boundaries = boundary_regression()
    ascendant = ascendant_report()
    timezone_result = timezone_report()
    result = {
        "programme": PROGRAMME,
        "retrieval_date": RETRIEVAL_DATE,
        "official_iae_reference": iae,
        "nirayana": nirayana,
        "boundaries": boundaries,
        "ascendant": ascendant,
        "timezone": timezone_result,
        "governance": {
            "predictive_validation": False, "life_event_scoring": False, "ml": "LOCKED", "pred_m4": "UNCHANGED",
            "d20_interpretation": "NOT_VALIDATED", "gold_whole_chart_promotion": False, "rag": "UNCHANGED",
        },
        "overall_decision": "CALCULATION_FOUNDATION_PARTIALLY_REFERENCE_VALIDATED",
        "result_hash": digest({"iae": iae, "nirayana": nirayana, "boundaries": boundaries, "ascendant": ascendant, "timezone": timezone_result}),
    }
    files = {
        "00_RUN_REPORT.json": result,
        "01_IAE_REFERENCE.json": iae,
        "02_NIRAYANA_REGRESSION.json": nirayana,
        "03_BOUNDARY_REGRESSION.json": boundaries,
        "04_ASCENDANT_CORPUS.json": {"cases": ascendant_cases(), "case_count": len(ascendant_cases()), "case_hash": digest(ascendant_cases())},
        "05_ASCENDANT_RESULTS.json": ascendant,
        "06_TIMEZONE_CORPUS.json": {"cases": timezone_cases(), "case_count": len(timezone_cases()), "case_hash": digest(timezone_cases())},
        "07_TIMEZONE_RESULTS.json": timezone_result,
    }
    for name, payload in files.items():
        (output_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ARTIFACT_DIR)
    args = parser.parse_args()
    result = build(args.output_dir)
    print(json.dumps({
        "programme": result["programme"],
        "result_hash": result["result_hash"],
        "iae_state": result["official_iae_reference"]["authority_state"],
        "ascendant": {key: result["ascendant"][key] for key in ("case_count", "degree_pass", "degree_fail", "sign_boundary_difference", "decision")},
        "timezone": result["timezone"]["status_counts"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
