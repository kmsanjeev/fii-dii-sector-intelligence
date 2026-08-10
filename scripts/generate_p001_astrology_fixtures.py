from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.chatbot.tools.kundli_calculator import compute_personal_kundli
from engines.intelligence.kundli_engine import KundliEngine

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "veda_p001"
GOLDEN_PATH = FIXTURE_DIR / "astrology_golden.json"
DIVERGENCE_PATH = FIXTURE_DIR / "divergence_register.json"

PERSONAL_CASES = [
    {
        "id": "personal_mumbai_1984_morning",
        "input": {
            "date_of_birth": "1984-11-03",
            "time_of_birth": "06:30",
            "place_name": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timezone_offset_hours": 5.5,
        },
    },
    {
        "id": "personal_london_2001_late_night",
        "input": {
            "date_of_birth": "2001-01-15",
            "time_of_birth": "23:45",
            "place_name": "London",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "timezone_offset_hours": 0.0,
        },
    },
    {
        "id": "personal_sydney_2000_boundary_midnight",
        "input": {
            "date_of_birth": "2000-01-01",
            "time_of_birth": "00:05",
            "place_name": "Sydney",
            "latitude": -33.8688,
            "longitude": 151.2093,
            "timezone_offset_hours": 11.0,
        },
    },
    {
        "id": "personal_newyork_1969_evening",
        "input": {
            "date_of_birth": "1969-07-20",
            "time_of_birth": "20:17",
            "place_name": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timezone_offset_hours": -4.0,
        },
    },
]

REST_HUMAN_CASES = [
    {
        "id": "rest_human_mumbai_1984_morning",
        "input": {
            "name": "Fixture Mumbai 1984",
            "date_str": "1984-11-03",
            "time_str": "06:30:00",
            "lat": 19.0760,
            "lon": 72.8777,
            "tz_offset": 5.5,
        },
    },
    {
        "id": "rest_human_london_2001_late_night",
        "input": {
            "name": "Fixture London 2001",
            "date_str": "2001-01-15",
            "time_str": "23:45:00",
            "lat": 51.5074,
            "lon": -0.1278,
            "tz_offset": 0.0,
        },
    },
]

STOCK_CASES = [
    {"id": "stock_reliance", "input": {"symbol": "RELIANCE", "listing_date": "1995-11-29", "exchange": "NSE"}},
    {"id": "stock_tcs", "input": {"symbol": "TCS", "listing_date": "2004-08-25", "exchange": "NSE"}},
    {"id": "stock_hdfcbank", "input": {"symbol": "HDFCBANK", "listing_date": "1995-05-19", "exchange": "NSE"}},
]

COUNTRY_CASES = [
    {"id": "country_india", "input": {"country_name": "India"}},
    {"id": "country_usa", "input": {"country_name": "USA"}},
]

DIVERGENCE_CASES = [
    {
        "id": "mumbai_1984",
        "shared_input": {
            "date": "1984-11-03",
            "time": "06:30:00",
            "place": "Mumbai",
            "lat": 19.0760,
            "lon": 72.8777,
            "tz_offset": 5.5,
        },
    },
    {
        "id": "london_2001",
        "shared_input": {
            "date": "2001-01-15",
            "time": "23:45:00",
            "place": "London",
            "lat": 51.5074,
            "lon": -0.1278,
            "tz_offset": 0.0,
        },
    },
]


def _planet_subset(planets: dict[str, dict], *, include_combust: bool) -> dict[str, dict]:
    subset = {}
    for planet, details in planets.items():
        item = {
            "longitude": details["longitude"],
            "sign": details["sign"],
            "degree": details["degree"],
            "house": details["house"],
            "nakshatra": details["nakshatra"],
            "nakshatra_lord": details["nakshatra_lord"],
            "pada": details["pada"],
            "dignity": details["dignity"],
            "retrograde": details["retrograde"],
        }
        if include_combust:
            item["combust"] = details.get("combust", False)
        subset[planet] = item
    return subset


def _extract_dasha_block(block: dict | None) -> dict | None:
    if not block:
        return None
    result = {"planet": block.get("planet")}
    for key in ["start_date", "end_date", "years"]:
        if key in block:
            result[key] = block[key]
    return result


def _extract_personal_vargas(vargas: dict) -> dict:
    result: dict[str, dict[str, str]] = {}
    for key, entries in vargas.items():
        if key == "d9_navamsa":
            result[key] = {entry["planet"]: entry["navamsa_sign"] for entry in entries}
        elif key == "d10_dasamsa":
            result[key] = {entry["planet"]: entry["dasamsa_sign"] for entry in entries}
    return result


def _extract_rest_divisions(divisional_charts: dict) -> dict:
    return {key: divisional_charts[key] for key in ["D9", "D10"] if key in divisional_charts}


def _extract_yoga_names(yogas) -> list[str]:
    if isinstance(yogas, list):
        names = []
        for item in yogas:
            if isinstance(item, dict):
                names.append(str(item.get("name", "")))
            else:
                names.append(str(item))
        return sorted(name for name in names if name)
    return []


def _extract_dosha_names(doshas) -> list[str]:
    if isinstance(doshas, list):
        return sorted(str(item.get("name", "")) for item in doshas if isinstance(item, dict) and item.get("name"))
    return []


def extract_personal_snapshot(payload: dict) -> dict:
    return {
        "birth_details": {
            "julian_date": payload["birth_details"]["julian_date"],
            "ayanamsha": payload["birth_details"]["ayanamsha"],
        },
        "lagna": {
            "sign": payload["lagna"]["sign"],
            "degree": payload["lagna"]["degree"],
            "full_longitude": payload["lagna"]["full_longitude"],
            "lord": payload["lagna"]["lord"],
        },
        "planets": _planet_subset(payload["planets"], include_combust=True),
        "current_dasha": {
            "mahadasha": _extract_dasha_block(payload["current_dasha"].get("mahadasha")),
            "antardasha": _extract_dasha_block(payload["current_dasha"].get("antardasha")),
            "pratyantardasha": _extract_dasha_block(payload["current_dasha"].get("pratyantardasha")),
            "has_all_antardashas": "all_antardashas" in payload["current_dasha"],
        },
        "varga_keys": sorted(payload["vargas"].keys()),
        "selected_vargas": _extract_personal_vargas(payload["vargas"]),
        "yoga_names": _extract_yoga_names(payload["yogas"]),
        "dosha_names": _extract_dosha_names(payload["doshas"]),
        "astro_score": payload["astro_score"],
        "astro_action": payload["astro_action"],
    }


def extract_rest_snapshot(payload: dict) -> dict:
    return {
        "entity": {
            "type": payload["entity"]["type"],
            "name": payload["entity"]["name"],
            "inception_date": payload["entity"]["inception_date"],
            "inception_time": payload["entity"]["inception_time"],
            "lat": payload["entity"]["lat"],
            "lon": payload["entity"]["lon"],
            "tz_offset": payload["entity"]["tz_offset"],
        },
        "lagna": {
            "sign": payload["lagna"]["sign"],
            "degree": payload["lagna"]["degree"],
            "full_longitude": payload["lagna"]["full_longitude"],
            "lord": payload["lagna"]["lord"],
        },
        "planets": _planet_subset(payload["planets"], include_combust=False),
        "current_dasha": {
            "mahadasha": _extract_dasha_block(payload["current_dasha"].get("mahadasha")),
            "antardasha": _extract_dasha_block(payload["current_dasha"].get("antardasha")),
            "pratyantardasha": _extract_dasha_block(payload["current_dasha"].get("pratyantardasha")),
            "has_all_antardashas": "all_antardashas" in payload["current_dasha"],
        },
        "divisional_chart_keys": sorted(payload["divisional_charts"].keys()),
        "selected_divisions": _extract_rest_divisions(payload["divisional_charts"]),
        "yoga_names": _extract_yoga_names(payload["yogas"]),
        "astro_score": payload["astro_score"],
        "astro_action": payload["astro_action"],
    }


def _divergence_values(personal: dict, rest: dict) -> list[dict]:
    return [
        {
            "field": "planets_present",
            "output_a": sorted(personal["planets"].keys()),
            "output_b": sorted(rest["planets"].keys()),
            "known_reason": "personal path returns 9 grahas plus nodes; REST human path also returns Uranus and Neptune",
        },
        {
            "field": "rahu_dignity",
            "output_a": personal["planets"]["Rahu"]["dignity"],
            "output_b": rest["planets"]["Rahu"]["dignity"],
            "known_reason": "personal and REST paths use different dignity tables for node interpretation",
        },
        {
            "field": "yoga_names",
            "output_a": _extract_yoga_names(personal["yogas"]),
            "output_b": _extract_yoga_names(rest["yogas"]),
            "known_reason": "personal path applies life-reading yoga logic; REST path applies finance-oriented yoga detection",
        },
        {
            "field": "available_varga_surface",
            "output_a": sorted(personal["vargas"].keys()),
            "output_b": sorted(rest["divisional_charts"].keys()),
            "known_reason": "personal path exposes D9 and D10 only; REST path exposes a broader divisional chart set",
        },
        {
            "field": "all_antardashas_presence",
            "output_a": "all_antardashas" in personal["current_dasha"],
            "output_b": "all_antardashas" in rest["current_dasha"],
            "known_reason": "personal path returns a deeper dasha breakdown than the REST human path",
        },
    ]


def build_golden_payload() -> dict:
    ke = KundliEngine()

    payload = {
        "meta": {
            "baseline_id": "VEDA-P001-M002",
            "generated_on": "2026-08-10",
            "tolerance_policy": {
                "julian_date": 0.0002,
                "longitude": 0.001,
                "degree": 0.01,
                "ayanamsha": 0.0002,
                "astro_score": 0.1,
            },
            "stock_cache_symbols": [case["input"]["symbol"] for case in STOCK_CASES],
        },
        "personal": [],
        "rest_human": [],
        "stock": [],
        "country": [],
    }

    for case in PERSONAL_CASES:
        result = compute_personal_kundli(**case["input"])
        payload["personal"].append({"id": case["id"], "input": case["input"], "expected": extract_personal_snapshot(result)})

    for case in REST_HUMAN_CASES:
        result = ke.compute_human(**case["input"])
        payload["rest_human"].append({"id": case["id"], "input": case["input"], "expected": extract_rest_snapshot(result)})

    for case in STOCK_CASES:
        result = ke.compute_stock(**case["input"])
        payload["stock"].append({"id": case["id"], "input": case["input"], "expected": extract_rest_snapshot(result)})

    for case in COUNTRY_CASES:
        result = ke.compute_country(**case["input"])
        payload["country"].append({"id": case["id"], "input": case["input"], "expected": extract_rest_snapshot(result)})

    return payload


def build_divergence_payload() -> dict:
    ke = KundliEngine()
    rows = []
    for case in DIVERGENCE_CASES:
        shared = case["shared_input"]
        personal = compute_personal_kundli(
            shared["date"],
            shared["time"][:5],
            shared["place"],
            latitude=shared["lat"],
            longitude=shared["lon"],
            timezone_offset_hours=shared["tz_offset"],
        )
        rest = ke.compute_human(
            case["id"],
            shared["date"],
            shared["time"],
            shared["lat"],
            shared["lon"],
            shared["tz_offset"],
        )
        for idx, diff in enumerate(_divergence_values(personal, rest), start=1):
            rows.append(
                {
                    "divergence_id": f"{case['id'].upper()}-D{idx:02d}",
                    "input": shared,
                    "path_a": "personal_kundli_chat_path",
                    "path_b": "rest_human_kundli_path",
                    "field": diff["field"],
                    "output_a": diff["output_a"],
                    "output_b": diff["output_b"],
                    "known_reason": diff["known_reason"],
                    "status": "KNOWN",
                }
            )
    return {"generated_on": "2026-08-10", "divergences": rows}


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    GOLDEN_PATH.write_text(json.dumps(build_golden_payload(), indent=2), encoding="utf-8")
    DIVERGENCE_PATH.write_text(json.dumps(build_divergence_payload(), indent=2), encoding="utf-8")
    print(GOLDEN_PATH)
    print(DIVERGENCE_PATH)


if __name__ == "__main__":
    main()
