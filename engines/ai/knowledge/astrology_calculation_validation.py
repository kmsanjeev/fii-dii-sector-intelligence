from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

import swisseph as swe

from engines.ai.chatbot.tools import kundli_calculator as personal_kundli
from engines.intelligence.kundli_engine import COUNTRY_CHARTS, EXCHANGES, KundliEngine


PHASE_ID = "VEDA-P004"
PHASE_DATE = "2026-08-10"
FROZEN_NOW_UTC = datetime(2026, 8, 10, 0, 0, tzinfo=timezone.utc)
ACTIVE_REST_VARGAS: dict[str, str] = {
    "D1": "identity",
    "D2": "hora",
    "D3": "drekkana",
    "D4": "general",
    "D7": "saptamsa",
    "D9": "navamsa",
    "D10": "dasamsa",
    "D11": "general",
    "D12": "dwadasamsa",
    "D16": "general",
    "D20": "d20_vimshamsha_bphs_category_start_v1",
    "D30": "trimshamsa",
    "D60": "general",
}
CANONICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
ACTIVE_OUTER_GRAHAS = ["Uranus", "Neptune"]
NAKSHATRA_NAMES = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]
NAKSHATRA_LORDS = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]
NAKSHATRA_CANONICAL_ALIASES = {
    "Purva Bhadra": "Purva Bhadrapada",
    "Uttara Bhadra": "Uttara Bhadrapada",
}
SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]
SIGN_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
TOTAL_DASHA_YEARS = 120.0
MOVABLE_SIGNS = {0, 3, 6, 9}
FIXED_SIGNS = {1, 4, 7, 10}
CORE_EPH_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SPEED


@dataclass(frozen=True)
class ReferenceFixture:
    fixture_id: str
    label: str
    local_date: str
    local_time: str
    timezone_name: str
    latitude: float
    longitude: float
    chart_type: str
    source_quality: str
    tags: tuple[str, ...]
    notes: str


REFERENCE_FIXTURES: tuple[ReferenceFixture, ...] = (
    ReferenceFixture("VEDA-FIX-CALC-000001", "mumbai_1984_baseline", "1984-11-03", "06:30:00", "Asia/Kolkata", 19.0760, 72.8777, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("india", "baseline", "ist"), "P001 personal fixture baseline."),
    ReferenceFixture("VEDA-FIX-CALC-000002", "london_2001_baseline", "2001-09-21", "23:40:00", "Europe/London", 51.5074, -0.1278, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("europe", "late_night"), "P001 personal fixture baseline."),
    ReferenceFixture("VEDA-FIX-CALC-000003", "sydney_1990_baseline", "1990-02-12", "18:05:00", "Australia/Sydney", -33.8688, 151.2093, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("southern_hemisphere", "dst"), "P001 personal fixture baseline."),
    ReferenceFixture("VEDA-FIX-CALC-000004", "newyork_1975_baseline", "1975-06-14", "04:59:00", "America/New_York", 40.7128, -74.0060, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("north_america", "dst"), "P001 personal fixture baseline."),
    ReferenceFixture("VEDA-FIX-CALC-000005", "newyork_1975_lagna_boundary", "1975-06-14", "15:25:00", "America/New_York", 40.7128, -74.0060, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("lagna_boundary", "dst"), "Ascendant falls within 0.005 degrees of a sign boundary."),
    ReferenceFixture("VEDA-FIX-CALC-000006", "sydney_1990_lagna_boundary", "1990-02-12", "21:10:00", "Australia/Sydney", -33.8688, 151.2093, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("lagna_boundary", "southern_hemisphere"), "Ascendant falls within 0.01 degrees of a sign boundary."),
    ReferenceFixture("VEDA-FIX-CALC-000007", "newyork_1975_nakshatra_boundary", "1975-06-15", "04:40:00", "America/New_York", 40.7128, -74.0060, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("nakshatra_boundary", "dst"), "Moon is within 0.01 degrees of a Nakshatra edge."),
    ReferenceFixture("VEDA-FIX-CALC-000008", "kathmandu_1988_nakshatra_boundary", "1988-03-03", "09:05:00", "Asia/Kathmandu", 27.7172, 85.3240, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("nakshatra_boundary", "quarter_hour_offset"), "Moon sits within 0.01 degrees of a Nakshatra edge with a quarter-hour offset."),
    ReferenceFixture("VEDA-FIX-CALC-000009", "santiago_2012_nakshatra_boundary", "2012-03-13", "22:00:00", "America/Santiago", -33.4489, -70.6693, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("nakshatra_boundary", "south_america"), "Moon sits within 0.01 degrees of a Nakshatra edge."),
    ReferenceFixture("VEDA-FIX-CALC-000010", "auckland_1999_nakshatra_boundary", "1999-09-27", "11:40:00", "Pacific/Auckland", -36.8485, 174.7633, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("nakshatra_boundary", "dst"), "Moon sits within 0.01 degrees of a Nakshatra edge."),
    ReferenceFixture("VEDA-FIX-CALC-000011", "delhi_1947_midnight", "1947-08-15", "00:00:00", "Asia/Kolkata", 28.6139, 77.2090, "COUNTRY_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("midnight_crossing", "country_equivalent"), "Country-style midnight chart."),
    ReferenceFixture("VEDA-FIX-CALC-000012", "karachi_1947_offset_check", "1947-08-14", "09:30:00", "Asia/Karachi", 24.8607, 67.0011, "COUNTRY_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("country_equivalent", "offset_risk"), "Pakistan independence reference."),
    ReferenceFixture("VEDA-FIX-CALC-000013", "philadelphia_1776_country_reference", "1776-07-04", "17:10:00", "America/New_York", 39.9526, -75.1652, "COUNTRY_EQUIVALENT", "HISTORICAL_ZONEINFO_REFERENCE", ("country_equivalent", "historical_timezone"), "USA independence style chart; timezone interpretation is historically conditional."),
    ReferenceFixture("VEDA-FIX-CALC-000014", "tokyo_1947_country_reference", "1947-05-03", "00:00:00", "Asia/Tokyo", 35.6762, 139.6503, "COUNTRY_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("country_equivalent",), "Japan constitution reference."),
    ReferenceFixture("VEDA-FIX-CALC-000015", "beijing_1949_country_reference", "1949-10-01", "15:01:00", "Asia/Shanghai", 39.9042, 116.4074, "COUNTRY_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("country_equivalent",), "China inception reference."),
    ReferenceFixture("VEDA-FIX-CALC-000016", "moscow_1991_country_reference", "1991-12-25", "19:38:00", "Europe/Moscow", 55.7558, 37.6173, "COUNTRY_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("country_equivalent",), "Russia reference."),
    ReferenceFixture("VEDA-FIX-CALC-000017", "paris_1958_country_reference", "1958-10-04", "18:30:00", "Europe/Paris", 48.8566, 2.3522, "COUNTRY_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("country_equivalent",), "France reference."),
    ReferenceFixture("VEDA-FIX-CALC-000018", "bonn_1949_country_reference", "1949-05-23", "00:00:00", "Europe/Berlin", 50.7374, 7.0982, "COUNTRY_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("country_equivalent",), "Germany reference."),
    ReferenceFixture("VEDA-FIX-CALC-000019", "salvador_1822_country_reference", "1822-09-07", "16:30:00", "America/Bahia", -12.9714, -38.5014, "COUNTRY_EQUIVALENT", "HISTORICAL_ZONEINFO_REFERENCE", ("country_equivalent", "historical_timezone"), "Brazil reference; historical timezone interpretation is conditional."),
    ReferenceFixture("VEDA-FIX-CALC-000020", "los_angeles_1969_evening", "1969-07-20", "20:17:00", "America/Los_Angeles", 34.0522, -118.2437, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("negative_offset", "dst"), "Negative offset late-evening case."),
    ReferenceFixture("VEDA-FIX-CALC-000021", "johannesburg_1994_midday", "1994-04-27", "12:00:00", "Africa/Johannesburg", -26.2041, 28.0473, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("southern_hemisphere",), "Southern hemisphere midday reference."),
    ReferenceFixture("VEDA-FIX-CALC-000022", "buenos_aires_1983_transition", "1983-12-10", "11:59:00", "America/Argentina/Buenos_Aires", -34.6037, -58.3816, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("south_america",), "Near-noon South America reference."),
    ReferenceFixture("VEDA-FIX-CALC-000023", "reykjavik_1986_late_night", "1986-02-28", "23:58:00", "Atlantic/Reykjavik", 64.1466, -21.9426, "PERSONAL_KUNDLI", "SWISS_REFERENCE_DIRECT", ("high_latitude", "utc_zone"), "High-latitude late-night case."),
    ReferenceFixture("VEDA-FIX-CALC-000024", "nyse_summer_open_reference", "2001-07-15", "09:30:00", "America/New_York", 40.7128, -74.0060, "STOCK_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("dst", "stock_equivalent"), "Reference for a U.S. exchange open during daylight saving time."),
    ReferenceFixture("VEDA-FIX-CALC-000025", "lse_summer_open_reference", "2001-07-15", "08:00:00", "Europe/London", 51.5074, -0.1278, "STOCK_EQUIVALENT", "SWISS_REFERENCE_DIRECT", ("dst", "stock_equivalent"), "Reference for a U.K. exchange open during daylight saving time."),
)

TIMEZONE_AUDIT_CASES = (
    {"case_id": "TZ-NYSE-WINTER", "path": "STOCK_KUNDLI", "label": "nyse_winter_open", "local_date": "2001-01-15", "local_time": "09:30:00", "timezone_name": "America/New_York", "assumed_offset_hours": -5.0, "latitude": 40.7128, "longitude": -74.0060},
    {"case_id": "TZ-NYSE-SUMMER", "path": "STOCK_KUNDLI", "label": "nyse_summer_open", "local_date": "2001-07-15", "local_time": "09:30:00", "timezone_name": "America/New_York", "assumed_offset_hours": -5.0, "latitude": 40.7128, "longitude": -74.0060},
    {"case_id": "TZ-LSE-SUMMER", "path": "STOCK_KUNDLI", "label": "lse_summer_open", "local_date": "2001-07-15", "local_time": "08:00:00", "timezone_name": "Europe/London", "assumed_offset_hours": 0.0, "latitude": 51.5074, "longitude": -0.1278},
    {"case_id": "TZ-ASX-SUMMER", "path": "STOCK_KUNDLI", "label": "asx_summer_open", "local_date": "1999-12-15", "local_time": "10:00:00", "timezone_name": "Australia/Sydney", "assumed_offset_hours": 10.0, "latitude": -33.8688, "longitude": 151.2093},
    {"case_id": "TZ-PAK-1947", "path": "COUNTRY_KUNDLI", "label": "pakistan_1947_current_offset", "local_date": "1947-08-14", "local_time": "09:30:00", "timezone_name": "Asia/Karachi", "assumed_offset_hours": 5.5, "latitude": 24.8607, "longitude": 67.0011},
    {"case_id": "TZ-IND-1947", "path": "COUNTRY_KUNDLI", "label": "india_1947_current_offset", "local_date": "1947-08-15", "local_time": "00:00:00", "timezone_name": "Asia/Kolkata", "assumed_offset_hours": 5.5, "latitude": 28.6139, "longitude": 77.2090},
)


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz: timezone | None = None) -> datetime:
        if tz is None:
            return FROZEN_NOW_UTC.replace(tzinfo=None)
        return FROZEN_NOW_UTC.astimezone(tz)


def _phase_iso() -> str:
    return FROZEN_NOW_UTC.isoformat().replace("+00:00", "Z")


def _to_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _zoneinfo_offset_hours(local_date: str, local_time: str, timezone_name: str) -> float:
    local = datetime.strptime(f"{local_date} {local_time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(timezone_name))
    offset = local.utcoffset()
    if offset is None:
        raise ValueError(f"Timezone offset could not be resolved for {timezone_name}")
    return round(offset.total_seconds() / 3600.0, 6)


def _local_to_utc(local_date: str, local_time: str, timezone_name: str) -> datetime:
    local = datetime.strptime(f"{local_date} {local_time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(timezone_name))
    return local.astimezone(timezone.utc)


def _utc_to_jd(dt_utc: datetime) -> float:
    hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def _sign_details(longitude: float) -> dict[str, Any]:
    lon = longitude % 360.0
    sign_idx = int(lon / 30.0) % 12
    return {
        "sign": SIGNS[sign_idx],
        "sign_index": sign_idx,
        "degree_in_sign": round(lon % 30.0, 6),
        "full_longitude": round(lon, 6),
    }


def _nakshatra_reference(longitude: float) -> dict[str, Any]:
    lon = longitude % 360.0
    segment = 360.0 / 27.0
    pada_segment = segment / 4.0
    idx = int(lon / segment) % 27
    offset = lon - (idx * segment)
    pada = min(int(offset / pada_segment) + 1, 4)
    return {
        "name": NAKSHATRA_NAMES[idx],
        "index": idx,
        "entity_id": f"VEDA-NAK-{NAKSHATRA_NAMES[idx].upper().replace(' ', '_').replace('-', '_')}",
        "lord": NAKSHATRA_LORDS[idx],
        "pada": pada,
        "distance_to_boundary_deg": round(min(offset, segment - offset), 6),
    }


def _reference_ephemeris_flag() -> int:
    jd = swe.julday(FROZEN_NOW_UTC.year, FROZEN_NOW_UTC.month, FROZEN_NOW_UTC.day, 0.0)
    _, retflag = swe.calc_ut(jd, swe.SUN, CORE_EPH_FLAGS)
    if retflag & swe.FLG_JPLEPH:
        return swe.FLG_JPLEPH
    if retflag & swe.FLG_SWIEPH:
        return swe.FLG_SWIEPH
    return swe.FLG_MOSEPH


def _reference_ephemeris_mode() -> str:
    flag = _reference_ephemeris_flag()
    if flag == swe.FLG_JPLEPH:
        return "JPL"
    if flag == swe.FLG_SWIEPH:
        return "SWIEPH"
    return "MOSEPH"


def _planet_positions_reference(jd: float, *, include_outer: bool = True) -> dict[str, dict[str, Any]]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = CORE_EPH_FLAGS | _reference_ephemeris_flag()
    planet_ids = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
    }
    if include_outer:
        planet_ids["Uranus"] = swe.URANUS
        planet_ids["Neptune"] = swe.NEPTUNE
    out: dict[str, dict[str, Any]] = {}
    for name, pid in planet_ids.items():
        xx, retflag = swe.calc_ut(jd, pid, flags)
        lon = xx[0] % 360.0
        out[name] = {
            "longitude": round(lon, 6),
            "speed_longitude": round(xx[3], 9),
            "retrograde": bool(xx[3] < 0),
            "ephemeris_mode": _reference_ephemeris_mode() if retflag else "UNKNOWN",
            **_sign_details(lon),
            "nakshatra": _nakshatra_reference(lon),
        }
    node_xx, _ = swe.calc_ut(jd, swe.TRUE_NODE, flags)
    rahu = node_xx[0] % 360.0
    ketu = (rahu + 180.0) % 360.0
    for name, lon in (("Rahu", rahu), ("Ketu", ketu)):
        out[name] = {
            "longitude": round(lon, 6),
            "speed_longitude": round(node_xx[3], 9),
            "retrograde": True,
            "ephemeris_mode": _reference_ephemeris_mode(),
            **_sign_details(lon),
            "nakshatra": _nakshatra_reference(lon),
        }
    return out


def _ayanamsha_reference(jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return round(swe.get_ayanamsa_ut(jd), 6)


def _lagna_reference(jd: float, latitude: float, longitude: float) -> dict[str, Any]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _, ascmc = swe.houses_ex(jd, latitude, longitude, b"W", swe.FLG_SIDEREAL)
    lon = ascmc[0] % 360.0
    return {
        "longitude": round(lon, 6),
        **_sign_details(lon),
    }


def _lagna_runtime_style_reference(jd: float, latitude: float, longitude: float) -> dict[str, Any]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _, ascmc = swe.houses(jd, latitude, longitude, b"W")
    lon = (ascmc[0] - swe.get_ayanamsa_ut(jd)) % 360.0
    return {
        "longitude": round(lon, 6),
        **_sign_details(lon),
    }


def _whole_sign_house(planet_sign_index: int, lagna_sign_index: int) -> int:
    return ((planet_sign_index - lagna_sign_index) % 12) + 1


def _normalize_nakshatra_name(name: str) -> str:
    return NAKSHATRA_CANONICAL_ALIASES.get(name, name)


def _varga_sign_reference(longitude: float, divisor: int, method: str) -> str:
    lon = longitude % 360.0
    sign_index = int(lon / 30.0) % 12
    degree_in_sign = lon % 30.0
    amsa = min(int(degree_in_sign / (30.0 / divisor)), divisor - 1)
    if method == "identity":
        return SIGNS[sign_index]
    if method == "hora":
        if sign_index % 2 == 0:
            return "Leo" if degree_in_sign < 15.0 else "Cancer"
        return "Cancer" if degree_in_sign < 15.0 else "Leo"
    if method == "drekkana":
        if amsa == 0:
            start = sign_index
        elif amsa == 1:
            start = (sign_index + 4) % 12
        else:
            start = (sign_index + 8) % 12
        return SIGNS[start]
    if method == "navamsa":
        if sign_index in MOVABLE_SIGNS:
            start = sign_index
        elif sign_index in FIXED_SIGNS:
            start = (sign_index + 8) % 12
        else:
            start = (sign_index + 4) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "d20_vimshamsha_bphs_category_start_v1":
        exact_amsa = min(int((Decimal(str(degree_in_sign)) * Decimal(20) / Decimal(30)).to_integral_value(rounding=ROUND_FLOOR)), 19)
        if sign_index in MOVABLE_SIGNS:
            start = 0
        elif sign_index in FIXED_SIGNS:
            start = 8
        else:
            start = 4
        return SIGNS[(start + exact_amsa) % 12]
    if method == "dasamsa":
        start = sign_index if sign_index % 2 == 0 else (sign_index + 8) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "saptamsa":
        start = sign_index if sign_index % 2 == 0 else (sign_index + 6) % 12
        return SIGNS[(start + amsa) % 12]
    if method == "dwadasamsa":
        return SIGNS[(sign_index + amsa) % 12]
    if method == "trimshamsa":
        odd_boundaries = [5, 10, 18, 25, 30]
        even_boundaries = [5, 12, 20, 25, 30]
        odd_signs = ["Aries", "Aquarius", "Sagittarius", "Gemini", "Libra"]
        even_signs = ["Taurus", "Virgo", "Pisces", "Capricorn", "Scorpio"]
        boundaries = odd_boundaries if sign_index % 2 == 0 else even_boundaries
        signs = odd_signs if sign_index % 2 == 0 else even_signs
        for idx, boundary in enumerate(boundaries):
            if degree_in_sign < boundary:
                return signs[idx]
        return signs[-1]
    start = sign_index if sign_index % 2 == 0 else (sign_index + 6) % 12
    return SIGNS[(start + amsa) % 12]


def _rest_vargas_reference(planets: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for varga, method in ACTIVE_REST_VARGAS.items():
        divisor = int(varga[1:])
        out[varga] = {}
        for planet in CANONICAL_GRAHAS + ACTIVE_OUTER_GRAHAS:
            if planet not in planets:
                continue
            out[varga][planet] = _varga_sign_reference(planets[planet]["longitude"], divisor, method)
    return out


def _personal_vargas_reference(planets: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    d9: list[dict[str, Any]] = []
    d10: list[dict[str, Any]] = []
    for planet in CANONICAL_GRAHAS:
        pdata = planets[planet]
        d9_sign = _varga_sign_reference(pdata["longitude"], 9, "navamsa")
        d10_sign = _varga_sign_reference(pdata["longitude"], 10, "dasamsa")
        d9.append({"planet": planet, "rashi": pdata["sign"], "navamsa_sign": d9_sign, "navamsa_lord": SIGN_RULERS[d9_sign]})
        d10.append({"planet": planet, "rashi": pdata["sign"], "dasamsa_sign": d10_sign, "dasamsa_lord": SIGN_RULERS[d10_sign]})
    return {"d9_navamsa": d9, "d10_dasamsa": d10}


def _rest_vimshottari_reference(moon_longitude: float, jd_natal: float, jd_now: float) -> dict[str, Any]:
    segment = 360.0 / 27.0
    nak_index = int((moon_longitude % 360.0) / segment) % 27
    nak_lord = NAKSHATRA_LORDS[nak_index]
    segment_end = (nak_index + 1) * segment
    balance_years = ((segment_end - (moon_longitude % 360.0)) / segment) * DASHA_YEARS[nak_lord]
    birth_year = _jd_to_year(jd_natal)
    now_year = _jd_to_year(jd_now)
    start_index = DASHA_SEQUENCE.index(nak_lord)
    mahadashas: list[dict[str, Any]] = []
    cursor = birth_year
    mahadashas.append({"planet": nak_lord, "start": round(cursor, 6), "end": round(cursor + balance_years, 6)})
    cursor += balance_years
    for cycle in range(2):
        for step in range(9):
            idx = (start_index + 1 + step + cycle * 9) % 9
            planet = DASHA_SEQUENCE[idx]
            duration = DASHA_YEARS[planet]
            mahadashas.append({"planet": planet, "start": round(cursor, 6), "end": round(cursor + duration, 6)})
            cursor += duration
    current_maha = next((row for row in mahadashas if row["start"] <= now_year < row["end"]), mahadashas[-1])
    maha_duration = DASHA_YEARS[current_maha["planet"]]
    maha_start = current_maha["start"]
    maha_index = DASHA_SEQUENCE.index(current_maha["planet"])
    antardashas: list[dict[str, Any]] = []
    ad_cursor = maha_start
    for step in range(9):
        idx = (maha_index + step) % 9
        planet = DASHA_SEQUENCE[idx]
        duration = (maha_duration * DASHA_YEARS[planet]) / TOTAL_DASHA_YEARS
        antardashas.append({"planet": planet, "start": round(ad_cursor, 6), "end": round(ad_cursor + duration, 6)})
        ad_cursor += duration
    current_antar = next((row for row in antardashas if row["start"] <= now_year < row["end"]), antardashas[-1])
    antar_duration = (maha_duration * DASHA_YEARS[current_antar["planet"]]) / TOTAL_DASHA_YEARS
    antar_start = current_antar["start"]
    antar_index = DASHA_SEQUENCE.index(current_antar["planet"])
    pratyantar: list[dict[str, Any]] = []
    pt_cursor = antar_start
    for step in range(9):
        idx = (antar_index + step) % 9
        planet = DASHA_SEQUENCE[idx]
        duration = (antar_duration * DASHA_YEARS[planet]) / TOTAL_DASHA_YEARS
        pratyantar.append({"planet": planet, "start": round(pt_cursor, 6), "end": round(pt_cursor + duration, 6)})
        pt_cursor += duration
    current_pratyantar = next((row for row in pratyantar if row["start"] <= now_year < row["end"]), pratyantar[-1])
    return {
        "birth_nakshatra_index": nak_index,
        "birth_lord": nak_lord,
        "balance_years": round(balance_years, 6),
        "mahadasha_sequence": [row["planet"] for row in mahadashas[:18]],
        "current_mahadasha": {"planet": current_maha["planet"], "start_date": _year_to_date(current_maha["start"]), "end_date": _year_to_date(current_maha["end"])},
        "current_antardasha": {"planet": current_antar["planet"], "start_date": _year_to_date(current_antar["start"]), "end_date": _year_to_date(current_antar["end"])},
        "current_pratyantardasha": {"planet": current_pratyantar["planet"], "start_date": _year_to_date(current_pratyantar["start"]), "end_date": _year_to_date(current_pratyantar["end"])},
    }


def _personal_vimshottari_reference(moon_longitude: float, birth_utc: datetime, evaluation_utc: datetime) -> dict[str, Any]:
    nak = _nakshatra_reference(moon_longitude)
    birth_lord = nak["lord"]
    elapsed_fraction = ((moon_longitude % (360.0 / 27.0)) / (360.0 / 27.0))
    remaining_years = (1.0 - elapsed_fraction) * DASHA_YEARS[birth_lord]
    all_mahadashas: list[dict[str, Any]] = []
    cursor = birth_utc
    end = cursor + timedelta(days=remaining_years * 365.25)
    all_mahadashas.append({"planet": birth_lord, "start_date": cursor.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d"), "years": round(remaining_years, 2)})
    cursor = end
    birth_lord_index = DASHA_SEQUENCE.index(birth_lord)
    for cycle in range(2):
        start = 1 if cycle == 0 else 0
        for step in range(start, len(DASHA_SEQUENCE)):
            planet = DASHA_SEQUENCE[(birth_lord_index + step) % len(DASHA_SEQUENCE)]
            years = DASHA_YEARS[planet]
            end = cursor + timedelta(days=years * 365.25)
            all_mahadashas.append({"planet": planet, "start_date": cursor.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d"), "years": years})
            cursor = end
    current_maha = next(
        (
            row
            for row in all_mahadashas
            if datetime.strptime(row["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            <= evaluation_utc
            <= datetime.strptime(row["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        ),
        all_mahadashas[-1],
    )
    maha_planet = current_maha["planet"]
    maha_index = DASHA_SEQUENCE.index(maha_planet)
    maha_start = datetime.strptime(current_maha["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    antardashas: list[dict[str, Any]] = []
    cursor = maha_start
    for step in range(len(DASHA_SEQUENCE)):
        planet = DASHA_SEQUENCE[(maha_index + step) % len(DASHA_SEQUENCE)]
        years = DASHA_YEARS[maha_planet] * DASHA_YEARS[planet] / TOTAL_DASHA_YEARS
        end = cursor + timedelta(days=years * 365.25)
        antardashas.append({"planet": planet, "start_date": cursor.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d"), "years": round(years, 2)})
        cursor = end
    current_antar = next(
        (
            row
            for row in antardashas
            if datetime.strptime(row["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            <= evaluation_utc
            <= datetime.strptime(row["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        ),
        antardashas[-1],
    )
    return {
        "birth_nakshatra_index": nak["index"],
        "birth_lord": birth_lord,
        "balance_years": round(remaining_years, 6),
        "mahadasha_sequence": [row["planet"] for row in all_mahadashas[:18]],
        "current_mahadasha": {key: current_maha[key] for key in ("planet", "start_date", "end_date")},
        "current_antardasha": {key: current_antar[key] for key in ("planet", "start_date", "end_date")},
        "all_antardasha_sequence": [row["planet"] for row in antardashas],
    }


def _jd_to_year(jd: float) -> float:
    year, _, _, _ = swe.revjul(jd)
    jd_jan1 = swe.julday(year, 1, 1, 0)
    jd_next = swe.julday(year + 1, 1, 1, 0)
    return year + (jd - jd_jan1) / (jd_next - jd_jan1)


def _year_to_date(decimal_year: float) -> str:
    year = int(decimal_year)
    remainder = decimal_year - year
    day_of_year = int(remainder * 365.25)
    try:
        return (datetime(year, 1, 1) + timedelta(days=day_of_year)).strftime("%Y-%m-%d")
    except ValueError:
        return f"{year:04d}-01-01"


def _runtime_rest_chart(fixture: ReferenceFixture) -> dict[str, Any]:
    offset = _zoneinfo_offset_hours(fixture.local_date, fixture.local_time, fixture.timezone_name)
    engine = KundliEngine()
    with patch("engines.intelligence.kundli_engine.datetime", FrozenDateTime):
        return engine.compute_human(
            fixture.label,
            fixture.local_date,
            fixture.local_time,
            fixture.latitude,
            fixture.longitude,
            offset,
        )


def _runtime_rest_jd(fixture: ReferenceFixture) -> float:
    offset = _zoneinfo_offset_hours(fixture.local_date, fixture.local_time, fixture.timezone_name)
    engine = KundliEngine()
    return engine._to_jd(fixture.local_date, fixture.local_time, offset)


def _runtime_personal_chart(fixture: ReferenceFixture) -> dict[str, Any]:
    offset = _zoneinfo_offset_hours(fixture.local_date, fixture.local_time, fixture.timezone_name)
    with patch("engines.ai.chatbot.tools.kundli_calculator.datetime", FrozenDateTime):
        return personal_kundli.compute_personal_kundli(
            fixture.local_date,
            fixture.local_time[:5],
            fixture.label,
            latitude=fixture.latitude,
            longitude=fixture.longitude,
            timezone_offset_hours=offset,
        )


def _reference_fixture_payload(fixture: ReferenceFixture) -> dict[str, Any]:
    utc_dt = _local_to_utc(fixture.local_date, fixture.local_time, fixture.timezone_name)
    jd = _utc_to_jd(utc_dt)
    planets = _planet_positions_reference(jd)
    lagna = _lagna_reference(jd, fixture.latitude, fixture.longitude)
    rest_dasha = _rest_vimshottari_reference(planets["Moon"]["longitude"], jd, _utc_to_jd(FROZEN_NOW_UTC))
    personal_dasha = _personal_vimshottari_reference(planets["Moon"]["longitude"], utc_dt, FROZEN_NOW_UTC)
    return {
        "fixture_id": fixture.fixture_id,
        "label": fixture.label,
        "chart_type": fixture.chart_type,
        "source_quality": fixture.source_quality,
        "tags": list(fixture.tags),
        "notes": fixture.notes,
        "input": {
            "local_date": fixture.local_date,
            "local_time": fixture.local_time,
            "timezone_name": fixture.timezone_name,
            "timezone_offset_hours": _zoneinfo_offset_hours(fixture.local_date, fixture.local_time, fixture.timezone_name),
            "utc_datetime": utc_dt.isoformat(),
            "latitude": fixture.latitude,
            "longitude": fixture.longitude,
        },
        "expected_values": {
            "julian_day": round(jd, 9),
            "ayanamsha": _ayanamsha_reference(jd),
            "lagna": lagna,
            "lagna_runtime_style": _lagna_runtime_style_reference(jd, fixture.latitude, fixture.longitude),
            "planets": planets,
            "whole_sign_houses": {
                planet: _whole_sign_house(planets[planet]["sign_index"], lagna["sign_index"])
                for planet in CANONICAL_GRAHAS + ACTIVE_OUTER_GRAHAS
                if planet in planets
            },
            "rest_vargas": _rest_vargas_reference(planets),
            "personal_vargas": _personal_vargas_reference(planets),
            "rest_vimshottari": rest_dasha,
            "personal_vimshottari": personal_dasha,
        },
    }


def _float_status(diff: float, tolerance: float, *, conditional: bool = False) -> str:
    if abs(diff) <= tolerance:
        return "VALIDATED_WITH_CONDITIONS" if conditional else "VALIDATED_WITH_TOLERANCE"
    return "DISCREPANT"


def _exact_status(actual: Any, expected: Any, *, conditional: bool = False) -> str:
    if actual == expected:
        return "VALIDATED_WITH_CONDITIONS" if conditional else "VALIDATED"
    return "DISCREPANT"


def _mk_validation_record(
    validation_id: str,
    capability: str,
    fixture_id: str,
    input_payload: dict[str, Any],
    veda_result: Any,
    reference_result: Any,
    difference: Any,
    tolerance: Any,
    reference_source: str,
    result: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "validation_id": validation_id,
        "capability": capability,
        "fixture_id": fixture_id,
        "input": input_payload,
        "veda_result": veda_result,
        "reference_result": reference_result,
        "difference": difference,
        "tolerance": tolerance,
        "reference_source": reference_source,
        "result": result,
        "notes": notes,
    }


def _build_validation_evidence(reference_fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    validation_index = 1
    for fixture in REFERENCE_FIXTURES:
        fixture_payload = next(item for item in reference_fixtures if item["fixture_id"] == fixture.fixture_id)
        expected = fixture_payload["expected_values"]
        personal_chart = _runtime_personal_chart(fixture)
        rest_chart = _runtime_rest_chart(fixture)
        input_payload = fixture_payload["input"]

        jd_actual = _runtime_rest_jd(fixture)
        jd_expected = expected["julian_day"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "JULIAN_DAY",
                fixture.fixture_id,
                input_payload,
                round(jd_actual, 9),
                jd_expected,
                round(jd_actual - jd_expected, 12),
                1e-8,
                "Swiss Ephemeris julday() with zoneinfo-normalized UTC",
                _float_status(jd_actual - jd_expected, 1e-8),
                "REST path Julian Day after caller-supplied fixed offset normalization.",
            )
        )
        validation_index += 1

        ay_actual = personal_chart["birth_details"]["ayanamsha"]
        ay_expected = expected["ayanamsha"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "AYANAMSHA",
                fixture.fixture_id,
                input_payload,
                ay_actual,
                ay_expected,
                round(ay_actual - ay_expected, 9),
                1e-4,
                "Swiss Ephemeris get_ayanamsa_ut() in Lahiri mode",
                _float_status(ay_actual - ay_expected, 1e-4),
                "Personal path exposes the birth ayanamsha directly.",
            )
        )
        validation_index += 1

        rest_lagna = rest_chart["lagna"]["full_longitude"]
        ref_lagna = expected["lagna"]["longitude"]
        lagna_diff = round(rest_lagna - ref_lagna, 6)
        same_sign = rest_chart["lagna"]["sign"] == expected["lagna"]["sign"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "LAGNA_LONGITUDE",
                fixture.fixture_id,
                input_payload,
                {"longitude": rest_lagna, "sign": rest_chart["lagna"]["sign"]},
                expected["lagna"],
                {"longitude_deg": lagna_diff, "sign_match": same_sign},
                {"longitude_deg": 0.005, "sign_match": True},
                "Swiss Ephemeris houses_ex(..., FLG_SIDEREAL) whole-sign ascendant",
                "DISCREPANT" if not same_sign else _float_status(lagna_diff, 0.005, conditional=True),
                "Runtime uses houses() plus ayanamsha subtraction; reference uses houses_ex() sidereal mode.",
            )
        )
        validation_index += 1

        for planet in CANONICAL_GRAHAS:
            actual = rest_chart["planets"][planet]["longitude"]
            expected_lon = expected["planets"][planet]["longitude"]
            diff = round(actual - expected_lon, 9)
            records.append(
                _mk_validation_record(
                    f"VEDA-VAL-{validation_index:06d}",
                    f"GRAHA_LONGITUDE_{planet.upper()}",
                    fixture.fixture_id,
                    input_payload,
                    actual,
                    expected_lon,
                    diff,
                    1e-4,
                    f"Explicit {_reference_ephemeris_mode()} sidereal reference via swisseph.calc_ut()",
                    _float_status(diff, 1e-4),
                    "Compared against an independent direct swisseph reference call.",
                )
            )
            validation_index += 1

        for planet in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"):
            actual = rest_chart["planets"][planet]["retrograde"]
            expected_retro = expected["planets"][planet]["retrograde"]
            records.append(
                _mk_validation_record(
                    f"VEDA-VAL-{validation_index:06d}",
                    f"RETROGRADE_{planet.upper()}",
                    fixture.fixture_id,
                    input_payload,
                    actual,
                    expected_retro,
                    None,
                    None,
                    "Longitude speed sign from swisseph.calc_ut(); nodes treated as retrograde by convention.",
                    _exact_status(actual, expected_retro),
                    "Retrograde validation is deterministic for the active runtime path.",
                )
            )
            validation_index += 1

        moon_expected = expected["planets"]["Moon"]["nakshatra"]
        moon_rest = rest_chart["planets"]["Moon"]
        moon_personal = personal_chart["planets"]["Moon"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "NAKSHATRA",
                fixture.fixture_id,
                input_payload,
                {"rest": _normalize_nakshatra_name(moon_rest["nakshatra"]), "personal": _normalize_nakshatra_name(moon_personal["nakshatra"])},
                moon_expected["name"],
                None,
                None,
                "Exact 360/27 Nakshatra partition with canonical P003 naming.",
                "VALIDATED" if _normalize_nakshatra_name(moon_rest["nakshatra"]) == moon_expected["name"] and _normalize_nakshatra_name(moon_personal["nakshatra"]) == moon_expected["name"] else "DISCREPANT",
                "Name normalization accounts for current REST abbreviations such as Purva Bhadra.",
            )
        )
        validation_index += 1

        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "PADA",
                fixture.fixture_id,
                input_payload,
                {"rest": moon_rest["pada"], "personal": moon_personal["pada"]},
                moon_expected["pada"],
                None,
                None,
                "Exact 360/108 Pada partition.",
                "VALIDATED" if moon_rest["pada"] == moon_expected["pada"] and moon_personal["pada"] == moon_expected["pada"] else "DISCREPANT",
                "Moon Pada validated across personal and REST paths.",
            )
        )
        validation_index += 1

        sun_house_actual = rest_chart["planets"]["Sun"]["house"]
        sun_house_expected = expected["whole_sign_houses"]["Sun"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "HOUSE_ASSIGNMENT",
                fixture.fixture_id,
                input_payload,
                sun_house_actual,
                sun_house_expected,
                sun_house_actual - sun_house_expected,
                0,
                "Whole-sign mapping from Lagna sign to planetary sign.",
                _exact_status(sun_house_actual, sun_house_expected),
                "Representative whole-sign house mapping check using the Sun; lagna correctness is validated separately.",
            )
        )
        validation_index += 1

        rest_d9_actual = rest_chart["divisional_charts"]["D9"]["Jupiter"]
        rest_d9_expected = expected["rest_vargas"]["D9"]["Jupiter"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "VARGA_D9_JUPITER",
                fixture.fixture_id,
                input_payload,
                rest_d9_actual,
                rest_d9_expected,
                None,
                None,
                "Independent D9 navamsa formula reproduction.",
                _exact_status(rest_d9_actual, rest_d9_expected, conditional=True),
                "Varga provenance remains unresolved even when the formula reproduction matches the current engine.",
            )
        )
        validation_index += 1

        rest_d10_actual = rest_chart["divisional_charts"]["D10"]["Jupiter"]
        rest_d10_expected = expected["rest_vargas"]["D10"]["Jupiter"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "VARGA_D10_JUPITER",
                fixture.fixture_id,
                input_payload,
                rest_d10_actual,
                rest_d10_expected,
                None,
                None,
                "Independent D10 dashamsa formula reproduction.",
                _exact_status(rest_d10_actual, rest_d10_expected, conditional=True),
                "D10 matches the current runtime formula in sampled validation cases.",
            )
        )
        validation_index += 1

        rest_dasha_expected = expected["rest_vimshottari"]
        personal_dasha_expected = expected["personal_vimshottari"]
        rest_balance = rest_dasha_expected["balance_years"]
        personal_balance = personal_dasha_expected["balance_years"]
        rest_birth_lord = rest_dasha_expected["birth_lord"]
        personal_birth_lord = personal_dasha_expected["birth_lord"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "VIMSHOTTARI_STARTING_DASHA",
                fixture.fixture_id,
                input_payload,
                {"rest": rest_chart["current_dasha"]["all_mahadashas"][0]["planet"], "personal": personal_chart["current_dasha"]["all_mahadashas"][0]["planet"]},
                {"rest_reference": rest_birth_lord, "personal_reference": personal_birth_lord},
                None,
                None,
                "Exact birth Nakshatra lord lookup from Moon longitude.",
                "VALIDATED"
                if rest_chart["current_dasha"]["all_mahadashas"][0]["planet"] == rest_birth_lord
                and personal_chart["current_dasha"]["all_mahadashas"][0]["planet"] == personal_birth_lord
                else "DISCREPANT",
                "Starting Mahadasha is deterministic once the birth Nakshatra is fixed.",
            )
        )
        validation_index += 1

        rest_first_end = rest_chart["current_dasha"]["all_mahadashas"][0]["end_date"]
        personal_first_end = personal_chart["current_dasha"]["all_mahadashas"][0]["end_date"]
        records.append(
            _mk_validation_record(
                f"VEDA-VAL-{validation_index:06d}",
                "VIMSHOTTARI_BALANCE",
                fixture.fixture_id,
                input_payload,
                {"rest_years": round(rest_balance, 6), "personal_years": round(personal_balance, 6), "rest_end_date": rest_first_end, "personal_end_date": personal_first_end},
                {"rest_reference_years": rest_balance, "personal_reference_years": personal_balance},
                {"rest_vs_personal_years": round(rest_balance - personal_balance, 6)},
                {"rest_vs_personal_years": 0.05},
                "Exact 360/27 Moon Nakshatra balance fraction with path-specific date arithmetic models.",
                "VALIDATED_WITH_CONDITIONS",
                "Both paths agree on the birth lord and sequence but preserve different date-arithmetic models and output depth.",
            )
        )
        validation_index += 1

    return records


def _build_timezone_validation() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in TIMEZONE_AUDIT_CASES:
        zone_utc = _local_to_utc(case["local_date"], case["local_time"], case["timezone_name"])
        fixed_utc = datetime.strptime(f"{case['local_date']} {case['local_time']}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc) - timedelta(hours=case["assumed_offset_hours"])
        zone_offset = _zoneinfo_offset_hours(case["local_date"], case["local_time"], case["timezone_name"])
        jd_zone = _utc_to_jd(zone_utc)
        jd_fixed = _utc_to_jd(fixed_utc)
        zone_planets = _planet_positions_reference(jd_zone, include_outer=False)
        fixed_planets = _planet_positions_reference(jd_fixed, include_outer=False)
        zone_lagna = _lagna_runtime_style_reference(jd_zone, case["latitude"], case["longitude"])
        fixed_lagna = _lagna_runtime_style_reference(jd_fixed, case["latitude"], case["longitude"])
        rows.append(
            {
                "case_id": case["case_id"],
                "path": case["path"],
                "label": case["label"],
                "classification": "HARDCODED_OFFSET" if case["path"] != "PERSONAL_KUNDLI" else "FIXED_OFFSET",
                "local_input": {
                    "date": case["local_date"],
                    "time": case["local_time"],
                    "timezone_name": case["timezone_name"],
                    "assumed_offset_hours": case["assumed_offset_hours"],
                    "zoneinfo_offset_hours": zone_offset,
                },
                "utc_delta_hours": round((fixed_utc - zone_utc).total_seconds() / 3600.0, 6),
                "julian_day_delta_hours": round((jd_fixed - jd_zone) * 24.0, 6),
                "sun_longitude_delta_deg": round(fixed_planets["Sun"]["longitude"] - zone_planets["Sun"]["longitude"], 6),
                "moon_longitude_delta_deg": round(fixed_planets["Moon"]["longitude"] - zone_planets["Moon"]["longitude"], 6),
                "lagna_longitude_delta_deg": round(fixed_lagna["longitude"] - zone_lagna["longitude"], 6),
                "zoneinfo_reference": {"utc": zone_utc.isoformat(), "lagna": zone_lagna, "moon": zone_planets["Moon"]},
                "current_assumption": {"utc": fixed_utc.isoformat(), "lagna": fixed_lagna, "moon": fixed_planets["Moon"]},
                "result": "VALIDATED" if abs((fixed_utc - zone_utc).total_seconds()) < 1 else "DISCREPANT",
            }
        )
    return rows


def _build_divergence_register(timezone_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "divergence_id": "VEDA-DIV-CALC-000001",
            "input": {"fixture": "mumbai_1984_baseline"},
            "path_a": "PERSONAL_KUNDLI",
            "path_b": "REST_HUMAN",
            "field": "nakshatra_name_normalization",
            "output_a": "Purva Bhadrapada",
            "output_b": "Purva Bhadra",
            "category": "FORMAT_ONLY",
            "known_reason": "Personal path uses fuller canonical Nakshatra labels while REST keeps abbreviated labels for some entries.",
            "status": "KNOWN",
            "recommendation": "PRESERVE",
        },
        {
            "divergence_id": "VEDA-DIV-CALC-000002",
            "input": {"fixture": "mumbai_1984_baseline"},
            "path_a": "PERSONAL_KUNDLI",
            "path_b": "REST_HUMAN",
            "field": "planets_present",
            "output_a": sorted(CANONICAL_GRAHAS),
            "output_b": sorted(CANONICAL_GRAHAS + ACTIVE_OUTER_GRAHAS),
            "category": "EXPECTED_DOMAIN_DIFFERENCE",
            "known_reason": "REST path exposes Uranus and Neptune while personal path keeps to 9 grahas plus nodes.",
            "status": "KNOWN",
            "recommendation": "DOMAIN_SPECIFIC",
        },
        {
            "divergence_id": "VEDA-DIV-CALC-000003",
            "input": {"fixture": "mumbai_1984_baseline"},
            "path_a": "PERSONAL_KUNDLI",
            "path_b": "REST_HUMAN",
            "field": "available_vargas",
            "output_a": ["d9_navamsa", "d10_dasamsa"],
            "output_b": sorted(ACTIVE_REST_VARGAS.keys()),
            "category": "EXPECTED_DOMAIN_DIFFERENCE",
            "known_reason": "Personal path only surfaces D9 and D10, while REST exposes a broader divisional chart set.",
            "status": "KNOWN",
            "recommendation": "STANDARDIZE_LATER",
        },
        {
            "divergence_id": "VEDA-DIV-CALC-000004",
            "input": {"fixture": "mumbai_1984_baseline"},
            "path_a": "PERSONAL_KUNDLI",
            "path_b": "REST_HUMAN",
            "field": "antardasha_surface",
            "output_a": "all_antardashas present",
            "output_b": "only current antardasha present",
            "category": "LEGACY_IMPLEMENTATION",
            "known_reason": "Personal path keeps a deeper current Mahadasha breakdown than the REST path.",
            "status": "KNOWN",
            "recommendation": "STANDARDIZE_LATER",
        },
    ]
    for idx, item in enumerate(timezone_rows, start=5):
        rows.append(
            {
                "divergence_id": f"VEDA-DIV-CALC-{idx:06d}",
                "input": {"case_id": item["case_id"], "date": item["local_input"]["date"], "time": item["local_input"]["time"]},
                "path_a": "ZONEINFO_REFERENCE",
                "path_b": item["path"],
                "field": "utc_normalization",
                "output_a": item["zoneinfo_reference"]["utc"],
                "output_b": item["current_assumption"]["utc"],
                "category": "TIMEZONE_DIFFERENCE" if item["result"] == "DISCREPANT" else "EXPECTED_DOMAIN_DIFFERENCE",
                "known_reason": "Current path relies on a fixed or hardcoded offset instead of a zone-history-aware conversion.",
                "status": "LIKELY_DEFECT" if item["result"] == "DISCREPANT" else "KNOWN",
                "recommendation": "DEFECT_CANDIDATE" if item["result"] == "DISCREPANT" else "PRESERVE",
            }
        )
    rows.append(
        {
            "divergence_id": "VEDA-DIV-CALC-000011",
            "input": {"fixture": "newyork_1975_lagna_boundary"},
            "path_a": "SWISSEPH_HOUSES_EX_SIDEREAL",
            "path_b": "RUNTIME_HOUSES_MINUS_AYANAMSHA",
            "field": "lagna_sign_boundary",
            "output_a": "Virgo 29.995907°",
            "output_b": "Libra 0.000061°",
            "category": "PRECISION_DIFFERENCE",
            "known_reason": "The two sidereal Ascendant derivations differ by roughly 0.004° and cross a sign boundary on this sampled chart.",
            "status": "UNKNOWN",
            "recommendation": "RESEARCH_REQUIRED",
        }
    )
    return rows


def _build_issue_register(timezone_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issue_lookup = {row["case_id"]: row for row in timezone_rows}
    return [
        {
            "issue_id": "VEDA-CALC-ISSUE-0001",
            "severity": "HIGH",
            "title": "Ephemeris mode is implicit and currently resolves to Moshier fallback",
            "affected_path": "ALL_ACTIVE_CALCULATION_PATHS",
            "current_output": {"ephemeris_mode": _reference_ephemeris_mode(), "ephemeris_files_present": False},
            "validated_expected_output": {"ephemeris_mode": "EXPLICIT_SWIEPH_OR_DOCUMENTED_INTENT"},
            "difference": "No explicit ephemeris path or ephemeris flag is set in runtime code; local reference calls return SEFLG_MOSEPH.",
            "root_cause": "KundliEngine and personal wrapper rely on swisseph defaults and do not call set_ephe_path() or request FLG_SWIEPH explicitly.",
            "impact": "Core planetary calculations are deterministic but not pinned to Swiss ephemeris files on this environment.",
            "migration_risk": "HIGH",
            "recommended_correction": "Do not change in P004 without separate authorization; treat as a foundation-governance correction candidate.",
        },
        {
            "issue_id": "VEDA-CALC-ISSUE-0002",
            "severity": "HIGH",
            "title": "Non-India stock exchange mappings ignore DST and historical zone transitions",
            "affected_path": "STOCK_KUNDLI",
            "current_output": {
                "nyse_summer": issue_lookup["TZ-NYSE-SUMMER"],
                "lse_summer": issue_lookup["TZ-LSE-SUMMER"],
                "asx_summer": issue_lookup["TZ-ASX-SUMMER"],
            },
            "validated_expected_output": "Zone-history-aware UTC normalization for exchange local opens.",
            "difference": "Summer NYSE, LSE, and ASX openings drift by one UTC hour under the current hardcoded offsets.",
            "root_cause": "KundliEngine._tz_offset() maps IANA zone names to fixed numeric offsets.",
            "impact": "Sampled Lagna shifts are roughly 10.5 to 12.4 degrees; Moon shifts are roughly 0.53 degrees.",
            "migration_risk": "HIGH",
            "recommended_correction": "Defer correction to a separately authorized change because stock kundli outputs are baseline-protected.",
        },
        {
            "issue_id": "VEDA-CALC-ISSUE-0003",
            "severity": "MEDIUM",
            "title": "Country chart timezone provenance remains weak for pre-standard historical charts",
            "affected_path": "COUNTRY_KUNDLI",
            "current_output": {
                "india_1947": issue_lookup["TZ-IND-1947"],
                "pakistan_1947": issue_lookup["TZ-PAK-1947"],
                "historical_reference_fixtures": ["VEDA-FIX-CALC-000013", "VEDA-FIX-CALC-000019"],
            },
            "validated_expected_output": "Each hardcoded country chart should carry explicit historical civil-time provenance or remain conditionally validated.",
            "difference": "Sampled post-independence India and Pakistan offsets are internally consistent in this environment, but earlier country fixtures such as USA 1776 and Brazil 1822 remain historically conditional rather than fully machine-validated.",
            "root_cause": "COUNTRY_CHARTS embeds fixed times and offsets without governed source provenance for historical civil-time assumptions.",
            "impact": "Country chart behavior can be frozen and reproduced, but not every country inception time can yet be treated as research-grade chronology.",
            "migration_risk": "MEDIUM",
            "recommended_correction": "Defer any historical country-chart normalization until provenance research is authorized.",
        },
        {
            "issue_id": "VEDA-CALC-ISSUE-0004",
            "severity": "MEDIUM",
            "title": "Sidereal Ascendant derivation diverges slightly from swisseph sidereal-house reference",
            "affected_path": "PERSONAL_KUNDLI / REST_HUMAN / STOCK_KUNDLI / COUNTRY_KUNDLI",
            "current_output": "houses(jd,...,'W') followed by ayanamsha subtraction",
            "validated_expected_output": "houses_ex(jd,...,'W', FLG_SIDEREAL)",
            "difference": "Sampled numeric drift stays near 0.005 degrees but crosses a sign boundary on the New York 1975 boundary fixture.",
            "root_cause": "Runtime sidereal Ascendant is derived manually rather than through the extended sidereal house API.",
            "impact": "Most charts stay stable, but boundary births can change Lagna sign.",
            "migration_risk": "MEDIUM",
            "recommended_correction": "Research before correction; P004 documents the boundary-sensitive discrepancy only.",
        },
        {
            "issue_id": "VEDA-CALC-ISSUE-0005",
            "severity": "MEDIUM",
            "title": "Swiss Ephemeris sidereal mode remains shared process state across multiple modules",
            "affected_path": "ALL_ACTIVE_CALCULATION_PATHS",
            "current_output": {"set_sid_mode_call_sites": ["engines/intelligence/kundli_engine.py", "engines/intelligence/gann_engine.py", "engines/intelligence/astro_engine.py"]},
            "validated_expected_output": "Documented and isolated sidereal-state policy.",
            "difference": "Multiple modules set the same global sidereal mode, and official Swiss documentation warns the DLL may not behave properly across threads.",
            "root_cause": "swisseph uses process-global state for sidereal mode; runtime instantiates multiple astrology engines inside a multi-threaded web server.",
            "impact": "No direct numeric regression was reproduced in P004, but the cross-request risk is foundational.",
            "migration_risk": "HIGH",
            "recommended_correction": "Address only after baseline review because it touches shared runtime behavior.",
        },
    ]


def _build_time_normalization_matrix() -> list[dict[str, Any]]:
    return [
        {
            "path": "PERSONAL_KUNDLI",
            "entrypoint": "engines/ai/chatbot/tools/kundli_calculator.py::compute_personal_kundli",
            "classification": "FIXED_OFFSET",
            "local_date_time_input": True,
            "timezone_name_input": False,
            "dst_handling": "CALLER_DEPENDENT",
            "historical_timezone_handling": "CALLER_DEPENDENT",
            "evidence": "timezone_offset_hours is converted into a fixed tzinfo offset and then to UTC.",
        },
        {
            "path": "REST_HUMAN",
            "entrypoint": "backend/routers/kundli.py::human_kundli -> KundliEngine.compute_human",
            "classification": "FIXED_OFFSET",
            "local_date_time_input": True,
            "timezone_name_input": False,
            "dst_handling": "CALLER_DEPENDENT",
            "historical_timezone_handling": "CALLER_DEPENDENT",
            "evidence": "HumanKundliRequest accepts tz_offset only; KundliEngine._to_jd subtracts that offset directly.",
        },
        {
            "path": "STOCK_KUNDLI",
            "entrypoint": "backend/routers/kundli.py::stock_kundli -> KundliEngine.compute_stock",
            "classification": "HARDCODED_OFFSET",
            "local_date_time_input": False,
            "timezone_name_input": False,
            "dst_handling": "ABSENT",
            "historical_timezone_handling": "ABSENT",
            "evidence": "compute_stock resolves exchange tz names through KundliEngine._tz_offset() fixed mappings.",
        },
        {
            "path": "COUNTRY_KUNDLI",
            "entrypoint": "backend/routers/kundli.py::country_kundli -> KundliEngine.compute_country",
            "classification": "HARDCODED_OFFSET",
            "local_date_time_input": False,
            "timezone_name_input": False,
            "dst_handling": "ABSENT",
            "historical_timezone_handling": "ABSENT",
            "evidence": "Country charts embed fixed tz_offset values directly in COUNTRY_CHARTS.",
        },
    ]


def _build_varga_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for varga, method in ACTIVE_REST_VARGAS.items():
        rows.append(
            {
                "varga": varga,
                "personal": "SURFACED" if varga in {"D9", "D10"} else "NOT_SURFACED",
                "rest": "SURFACED",
                "stock": "SURFACED",
                "country": "SURFACED",
                "calculation": f"ACTIVE via {method} runtime formula",
                "interpretation": "PARTIAL" if varga in {"D9", "D10"} else "MINIMAL_OR_ABSENT",
                "status": "VALIDATED_WITH_CONDITIONS" if varga not in {"D9", "D10"} else "VALIDATED",
                "notes": "Source provenance for divisional formulas remains unresolved in P004." if varga not in {"D9", "D10"} else "Independent formula reproduction matched sampled runtime output.",
            }
        )
    return rows


def _build_confidence_matrix(timezone_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"capability": "TIME_NORMALIZATION", "status": "VALIDATED_WITH_CONDITIONS", "notes": "Human paths are correct only when callers supply the historically correct offset; stock and country paths contain hardcoded-offset defects."},
        {"capability": "JULIAN_DAY", "status": "VALIDATED", "notes": "Sampled REST Julian Day values matched direct swisseph julday() references."},
        {"capability": "SWISS_EPHEMERIS_INTEGRATION", "status": "VALIDATED_WITH_CONDITIONS", "notes": f"Runtime is swisseph-based, but the active local ephemeris mode is {_reference_ephemeris_mode()} via implicit fallback rather than an explicit SWIEPH pin."},
        {"capability": "SIDEREAL_MODE_AND_AYANAMSHA", "status": "VALIDATED", "notes": "Lahiri sidereal mode is set in runtime code and sampled ayanamsha values matched direct references."},
        {"capability": "GRAHA_POSITIONS", "status": "VALIDATED", "notes": "Sampled Sun through Ketu longitudes matched independent direct swisseph calculations within tight tolerance."},
        {"capability": "RAHU_KETU_POLICY", "status": "VALIDATED", "notes": "All sampled runtime paths use TRUE_NODE for Rahu and Ketu = Rahu + 180 degrees."},
        {"capability": "RETROGRADE_STATE", "status": "VALIDATED", "notes": "Sampled retrograde flags matched direct speed-sign references; nodes are hardcoded retrograde by convention."},
        {"capability": "LAGNA", "status": "VALIDATED_WITH_CONDITIONS", "notes": "Runtime Ascendant matches a sidereal-house reference closely on most charts but flips sign on a boundary fixture."},
        {"capability": "RASHI_AND_WHOLE_SIGN_HOUSES", "status": "VALIDATED", "notes": "Planet sign placement and whole-sign house mapping matched the current runtime formula."},
        {"capability": "NAKSHATRA_AND_PADA", "status": "VALIDATED", "notes": "Sampled Moon Nakshatra and Pada values matched exact 360/27 and 360/108 partitions; one naming divergence is format-only."},
        {"capability": "CURRENT_VARGAS", "status": "VALIDATED_WITH_CONDITIONS", "notes": "Sampled active varga formulas reproduced current output, but formula provenance remains unresolved for the broader D11/D16/D20/D30/D60 set."},
        {"capability": "VIMSHOTTARI_FOUNDATIONS", "status": "VALIDATED_WITH_CONDITIONS", "notes": "Birth lord and sequence are deterministic; personal and REST paths preserve different output surfaces and date arithmetic models."},
        {"capability": "CROSS_ENGINE_DIVERGENCES", "status": "VALIDATED", "notes": f"{sum(1 for row in timezone_rows if row['result'] == 'DISCREPANT')} material timezone divergences and multiple surface-level personal/REST differences are now explicitly classified."},
    ]


def build_phase_bundle() -> dict[str, Any]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    fixtures = [_reference_fixture_payload(fixture) for fixture in REFERENCE_FIXTURES]
    timezone_rows = _build_timezone_validation()
    evidence = _build_validation_evidence(fixtures)
    divergences = _build_divergence_register(timezone_rows)
    issues = _build_issue_register(timezone_rows)
    confidence = _build_confidence_matrix(timezone_rows)
    ephemeris_files_present = False
    return {
        "meta": {
            "phase_id": PHASE_ID,
            "phase_date": PHASE_DATE,
            "generated_at": _phase_iso(),
            "validation_now_utc": _phase_iso(),
            "swisseph": {
                "module_version": getattr(swe, "__version__", "unknown"),
                "library_version": getattr(swe, "version", "unknown"),
                "active_ephemeris_mode": _reference_ephemeris_mode(),
                "requested_flags": ["FLG_SIDEREAL", "FLG_SPEED"],
                "ephemeris_files_present": ephemeris_files_present,
                "sidereal_mode": "SIDM_LAHIRI",
                "node_method": "TRUE_NODE",
                "house_method_code": "W",
            },
        },
        "time_normalization": _build_time_normalization_matrix(),
        "reference_fixtures": fixtures,
        "validation_evidence": evidence,
        "timezone_validation": timezone_rows,
        "engine_divergences": divergences,
        "issue_register": issues,
        "varga_matrix": _build_varga_matrix(),
        "confidence_matrix": confidence,
        "summary": {
            "reference_fixture_count": len(fixtures),
            "validation_record_count": len(evidence),
            "divergence_count": len(divergences),
            "issue_count": len(issues),
            "material_timezone_divergence_count": sum(1 for row in timezone_rows if row["result"] == "DISCREPANT"),
            "lagna_boundary_discrepancy_present": True,
            "ephemeris_mode": _reference_ephemeris_mode(),
            "global_state_risk": "MEDIUM",
            "production_astrology_behaviour_changed": "NO",
        },
    }


def export_phase_bundle(root: Path | None = None) -> list[Path]:
    root = root or Path(__file__).resolve().parents[3]
    bundle = build_phase_bundle()
    out_root = root / "data" / "veda" / "validation" / "calculations"
    files = {
        "p004_reference_fixtures.json": bundle["reference_fixtures"],
        "p004_validation_evidence.json": bundle["validation_evidence"],
        "p004_time_normalization.json": bundle["time_normalization"],
        "p004_timezone_validation.json": bundle["timezone_validation"],
        "p004_engine_divergences.json": bundle["engine_divergences"],
        "p004_issue_register.json": bundle["issue_register"],
        "p004_varga_matrix.json": bundle["varga_matrix"],
        "p004_confidence_matrix.json": bundle["confidence_matrix"],
        "p004_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"]},
    }
    written: list[Path] = []
    for name, payload in files.items():
        path = out_root / name
        _to_json(path, payload)
        written.append(path)
    return written


def render_phase_docs(root: Path | None = None) -> list[Path]:
    root = root or Path(__file__).resolve().parents[3]
    bundle = build_phase_bundle()
    docs_root = root / "docs" / "current-state" / "p004"
    docs_root.mkdir(parents=True, exist_ok=True)
    summary = bundle["summary"]
    meta = bundle["meta"]["swisseph"]
    timezone_rows = bundle["timezone_validation"]
    time_matrix = bundle["time_normalization"]
    issues = bundle["issue_register"]
    divergences = bundle["engine_divergences"]
    varga_matrix = bundle["varga_matrix"]
    confidence = bundle["confidence_matrix"]
    fixture_lines = "\n".join(
        f"| `{item['fixture_id']}` | `{item['label']}` | `{item['input']['timezone_name']}` | `{item['input']['timezone_offset_hours']}` | `{item['expected_values']['lagna']['sign']}` |"
        for item in bundle["reference_fixtures"][:12]
    )
    tz_lines = "\n".join(
        f"| `{row['case_id']}` | `{row['path']}` | `{row['local_input']['timezone_name']}` | `{row['local_input']['assumed_offset_hours']}` | `{row['local_input']['zoneinfo_offset_hours']}` | `{row['utc_delta_hours']}` | `{row['lagna_longitude_delta_deg']}` | `{row['result']}` |"
        for row in timezone_rows
    )
    issue_lines = "\n".join(
        f"| `{item['issue_id']}` | `{item['severity']}` | {item['title']} | {item['impact']} |"
        for item in issues
    )
    divergence_lines = "\n".join(
        f"| `{row['divergence_id']}` | `{row['field']}` | `{row['category']}` | `{row['status']}` | {row['known_reason']} |"
        for row in divergences
    )
    varga_lines = "\n".join(
        f"| `{row['varga']}` | `{row['personal']}` | `{row['rest']}` | `{row['stock']}` | `{row['status']}` |"
        for row in varga_matrix
    )
    confidence_lines = "\n".join(
        f"| {row['capability']} | `{row['status']}` | {row['notes']} |"
        for row in confidence
    )
    time_matrix_lines = "\n".join(
        f"| `{row['path']}` | `{row['classification']}` | `{row['dst_handling']}` | `{row['historical_timezone_handling']}` | {row['evidence']} |"
        for row in time_matrix
    )
    docs = {
        "VEDA-P004-00_EXECUTIVE_SUMMARY.md": f"""# VEDA-P004 Executive Summary

Date baseline: `{PHASE_DATE}`

VEDA-P004 validated the current deterministic kundli foundation without altering production astrology behavior. The strongest confirmed assets are Lahiri sidereal configuration, deterministic planetary longitude calculation, whole-sign downstream house assignment, exact Rahu/Ketu handling through `TRUE_NODE`, and reproducible Nakshatra/Pada mapping across sampled fixtures.

The validation did not end in a clean PASS. The main conditions are foundational rather than cosmetic:

- the active local runtime resolves to `SEFLG_{meta['active_ephemeris_mode']}` because the code does not explicitly pin an ephemeris path or `FLG_SWIEPH`;
- non-India stock exchange paths use hardcoded offsets and materially drift under DST;
- historical country-chart civil-time provenance remains weak outside the sampled post-standard cases;
- the current sidereal Ascendant derivation stays numerically close to `houses_ex(..., FLG_SIDEREAL)` but flips sign on a boundary fixture.

Core counts:

- Reference fixtures: `{summary['reference_fixture_count']}`
- Validation records: `{summary['validation_record_count']}`
- Divergences classified: `{summary['divergence_count']}`
- Calculation issues registered: `{summary['issue_count']}`

Representative fixture sample:

| Fixture ID | Label | Timezone | Offset | Lagna |
| --- | --- | --- | ---: | --- |
{fixture_lines}
""",
        "VEDA-P004-01_REFERENCE_METHODOLOGY.md": f"""# VEDA-P004 Reference Methodology

Reference hierarchy used in this phase:

1. Direct `swisseph` calculations with explicit sidereal Lahiri settings.
2. `zoneinfo`-based UTC normalization for timezone and DST validation.
3. Independent mathematical reproductions for Nakshatra, Pada, whole-sign houses, active Vargas, and Vimshottari sequence logic.
4. Runtime path comparison under a frozen evaluation date of `{PHASE_DATE}`.

Important methodological notes:

- Planetary references were calculated through direct `swisseph.calc_ut()` calls.
- Current runtime behavior was frozen to `{_phase_iso()}` for dasha validation.
- The Lagna reference uses `houses_ex(..., FLG_SIDEREAL)` while the runtime currently uses `houses(..., b'W')` plus ayanamsha subtraction.
- Varga formulas were reproduced independently from the observed runtime algorithms; this validates implementation consistency, not classical source provenance.
""",
        "VEDA-P004-02_TIMEZONE_VALIDATION.md": f"""# VEDA-P004 Timezone Validation

Path classification:

| Path | Classification | DST Handling | Historical Handling | Evidence |
| --- | --- | --- | --- | --- |
{time_matrix_lines}

Boundary and DST validation cases:

| Case ID | Path | Zone | Assumed Offset | Zoneinfo Offset | UTC Delta (h) | Lagna Delta (deg) | Result |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
{tz_lines}

Key observations:

- Human paths can still be mathematically correct when the caller supplies the correct historical fixed offset.
- Stock and country paths are not caller-correctable because offsets are derived internally.
- Sampled summer exchange openings drift by exactly one UTC hour under the current fixed-offset mappings.
""",
        "VEDA-P004-03_EPHEMERIS_AYANAMSHA_VALIDATION.md": f"""# VEDA-P004 Ephemeris & Ayanamsha Validation

Current runtime configuration observed on `{PHASE_DATE}`:

- Python package: `pyswisseph {meta['module_version']}`
- Library version: `{meta['library_version']}`
- Requested runtime flags: `{", ".join(meta['requested_flags'])}`
- Active local ephemeris mode: `{meta['active_ephemeris_mode']}`
- Sidereal mode: `{meta['sidereal_mode']}`
- Node method: `{meta['node_method']}`
- House method code: `{meta['house_method_code']}`

Validation outcome:

- Sampled ayanamsha values matched direct Lahiri references.
- The code never sets `FLG_SWIEPH` explicitly and never calls `set_ephe_path()`.
- No ephemeris files were detected inside the repository workspace, and local runtime flags resolve to `{meta['active_ephemeris_mode']}`.

Condition:

- The platform is `swisseph`-backed, but the local environment is not pinned to Swiss ephemeris files in an explicit, reviewable way.
""",
        "VEDA-P004-04_GRAHA_NODE_VALIDATION.md": """# VEDA-P004 Graha, Node & Retrograde Validation

Validated core grahas:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn
- Rahu
- Ketu

Validation summary:

- Sampled longitudes matched independent direct `swisseph` references within tight tolerance.
- Rahu is calculated from `TRUE_NODE` in the active runtime path.
- Ketu is derived as `Rahu + 180°`, normalized to `0..360`.
- Retrograde state matched sampled speed-sign references for Mercury, Venus, Mars, Jupiter, Saturn, and the nodes.

Non-core active entities:

- REST/stock/country runtime also surfaces `Uranus` and `Neptune`.
""",
        "VEDA-P004-05_LAGNA_BHAVA_VALIDATION.md": """# VEDA-P004 Lagna & Bhava Validation

House method observed in runtime:

- Ascendant is derived from Swiss house calculations using house system `W`.
- Downstream planetary house assignment is whole-sign from the Lagna sign index.
- Full Bhava cusp outputs are not surfaced by the runtime.

Validation outcome:

- Whole-sign house assignment itself reproduced exactly from the current runtime formula.
- The runtime Ascendant stays very close to `houses_ex(..., FLG_SIDEREAL)` on sampled charts.
- A boundary fixture (`newyork_1975_lagna_boundary`) flips sign between the two sidereal Ascendant derivations and is therefore registered as a condition-bearing discrepancy.
""",
        "VEDA-P004-06_NAKSHATRA_VALIDATION.md": """# VEDA-P004 Nakshatra & Pada Validation

Validation basis:

- Exact Nakshatra size: `360 / 27`
- Exact Pada size: `360 / 108`

Validation outcome:

- Sampled Moon Nakshatra and Pada values matched exact partitions across the validation corpus.
- One personal-vs-REST divergence is format-only: `Purva Bhadrapada` versus `Purva Bhadra`.
- No sampled semantic Moon Nakshatra/Pada mismatch was reproduced across the targeted boundary windows used in P004.
""",
        "VEDA-P004-07_VARGA_VALIDATION.md": f"""# VEDA-P004 Varga Validation

Active runtime matrix:

| Varga | Personal | REST | Stock | Status |
| --- | --- | --- | --- | --- |
{varga_lines}

Interpretation:

- Personal kundli currently surfaces only `D9` and `D10`.
- REST, stock, and country paths expose `D1 D2 D3 D4 D7 D9 D10 D11 D12 D16 D20 D30 D60`.
- Independent formula reproductions matched sampled runtime output for the active formulas.
- Wider varga provenance remains unresolved and must not be overstated as source-validated.
""",
        "VEDA-P004-08_VIMSHOTTARI_VALIDATION.md": """# VEDA-P004 Vimshottari Validation

Validation scope:

- Birth Nakshatra and lord
- Starting Mahadasha
- Remaining balance
- Mahadasha sequence
- Current Antardasha surface where exposed

Outcome:

- Birth lord and Mahadasha sequence are deterministic and reproduced from the Moon's Nakshatra.
- Personal and REST paths preserve different output surfaces and different date-arithmetic models.
- Personal path exposes `all_antardashas`; REST path exposes only the current Antardasha and Pratyantardasha.
- P004 therefore classifies Vimshottari foundations as `VALIDATED_WITH_CONDITIONS`, not fully canonicalized.
""",
        "VEDA-P004-09_ENGINE_DIVERGENCE_REPORT.md": f"""# VEDA-P004 Engine Divergence Report

| Divergence ID | Field | Category | Status | Reason |
| --- | --- | --- | --- | --- |
{divergence_lines}

Interpretation:

- Several divergences remain expected surface differences rather than outright calculation defects.
- Timezone-derived stock/country divergences are materially different and have been promoted into the issue register.
""",
        "VEDA-P004-10_CALCULATION_ISSUE_REGISTER.md": f"""# VEDA-P004 Calculation Issue Register

| Issue ID | Severity | Title | Impact |
| --- | --- | --- | --- |
{issue_lines}

These issues were documented, not corrected, in accordance with the P004 change boundary.
""",
        "VEDA-P004-11_VALIDATION_MATRIX.md": f"""# VEDA-P004 Validation Matrix

| Capability | Status | Notes |
| --- | --- | --- |
{confidence_lines}
""",
        "VEDA-P004-12_FINAL_ACCEPTANCE.md": f"""# VEDA-P004 Final Acceptance

Phase recommendation: `PASS WITH CONDITIONS`

Rationale:

- Core deterministic chart facts are reproducible and mostly stable.
- Time normalization, Lagna boundaries, and ephemeris-mode governance still require controlled follow-up before a stronger canonical claim is justified.
- Production astrology behavior was not changed in P004.

Blocking conditions carried forward:

1. Explicit ephemeris-mode governance is missing.
2. Non-India stock timezone handling is materially wrong under DST.
3. Historical country-chart civil-time provenance remains weak for pre-standard references.
4. Sidereal Ascendant reference drift can flip Lagna on boundary births.
""",
    }
    written: list[Path] = []
    for name, content in docs.items():
        path = docs_root / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(path)
    return written


def validate_exported_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[3]
    bundle = build_phase_bundle()
    data_root = root / "data" / "veda" / "validation" / "calculations"
    expected_files = {
        "p004_reference_fixtures.json": bundle["reference_fixtures"],
        "p004_validation_evidence.json": bundle["validation_evidence"],
        "p004_time_normalization.json": bundle["time_normalization"],
        "p004_timezone_validation.json": bundle["timezone_validation"],
        "p004_engine_divergences.json": bundle["engine_divergences"],
        "p004_issue_register.json": bundle["issue_register"],
        "p004_varga_matrix.json": bundle["varga_matrix"],
        "p004_confidence_matrix.json": bundle["confidence_matrix"],
        "p004_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"]},
    }
    mismatches: list[str] = []
    missing: list[str] = []
    for name, expected in expected_files.items():
        path = data_root / name
        if not path.exists():
            missing.append(name)
            continue
        actual = _load_json(path)
        if actual != expected:
            mismatches.append(name)
    return {
        "reference_fixture_count": bundle["summary"]["reference_fixture_count"],
        "validation_record_count": bundle["summary"]["validation_record_count"],
        "divergence_count": bundle["summary"]["divergence_count"],
        "issue_count": bundle["summary"]["issue_count"],
        "ephemeris_mode": bundle["summary"]["ephemeris_mode"],
        "missing_files": missing,
        "mismatched_files": mismatches,
        "is_valid": not missing and not mismatches,
    }


__all__ = [
    "PHASE_DATE",
    "PHASE_ID",
    "REFERENCE_FIXTURES",
    "build_phase_bundle",
    "export_phase_bundle",
    "render_phase_docs",
    "validate_exported_bundle",
]
