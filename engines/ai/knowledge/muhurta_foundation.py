"""Governed Muhurta foundation primitives.

This module intentionally stops at deterministic date/location and solar-day
facts. It does not select auspicious times, score events, implement Bala
systems, or provide Prashna behavior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


METHOD_ID = "MUHURTA_FOUNDATION_SOLAR_DAY_NOAA_APPROX_V1"
METHOD_VERSION = "1.0"
ZENITH_DEGREES = 90.833

EVENT_TYPES = (
    "MARRIAGE",
    "TRAVEL",
    "EDUCATION",
    "CONSTRUCTION_PROPERTY",
    "NAMING",
    "INITIATION",
    "MEDICAL_PROCEDURE",
    "BUSINESS_CONTRACT",
)

# These are calculation facts, not auspiciousness labels.  The names mirror
# the existing birth-time Panchanga surface so that P032 can validate and
# reuse the same five-limb vocabulary without importing chatbot internals.
TITHI_NAMES = (
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi",
    "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima", "Pratipada",
    "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi",
    "Chaturdashi", "Amavasya",
)
YOGA_NAMES = (
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
)
KARANA_MOVABLE = ("Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti")
VARA_DAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
VARA_LORDS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
NAKSHATRA_NAMES = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)
NAKSHATRA_LORDS = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
)

P032_CALCULATION_METHOD_ID = "MUHURTA_PANCHANGA_SIDEREAL_FACTS_V1"
P032_CALCULATION_METHOD_VERSION = "1.0"
P032_SOURCE_STATUS = "CALCULATION_FOUNDATION;EVENT_SELECTION_DISABLED"

EVENT_TAXONOMY: dict[str, dict[str, Any]] = {
    "MARRIAGE": {"family": "RELATIONSHIP", "status": "SCOPED_RULES_AVAILABLE", "production": "DISABLED"},
    "TRAVEL": {"family": "MOVEMENT", "status": "SCOPED_RULES_AVAILABLE", "production": "DISABLED"},
    "EDUCATION": {"family": "LEARNING", "status": "SCOPED_RULES_AVAILABLE", "production": "DISABLED"},
    "CONSTRUCTION_PROPERTY": {"family": "PROPERTY", "status": "SCOPED_RULES_AVAILABLE", "production": "DISABLED"},
    "NAMING": {"family": "LIFE_CYCLE", "status": "SCOPED_RULES_AVAILABLE", "production": "DISABLED"},
    "INITIATION": {"family": "RITUAL", "status": "SCOPED_RULES_AVAILABLE", "production": "DISABLED"},
    "MEDICAL_PROCEDURE": {"family": "HEALTH", "status": "HIGH_RISK_INACTIVE", "production": "DISABLED"},
    "BUSINESS_CONTRACT": {"family": "COMMERCE", "status": "SCOPED_RULES_AVAILABLE", "production": "DISABLED"},
    "PROPERTY_PURCHASE": {"family": "PROPERTY", "status": "TAXONOMY_ONLY", "production": "DISABLED"},
    "HOUSE_ENTRY": {"family": "PROPERTY", "status": "TAXONOMY_ONLY", "production": "DISABLED"},
    "RELIGIOUS_RITUAL": {"family": "RITUAL", "status": "TAXONOMY_ONLY", "production": "DISABLED"},
    "VEHICLE": {"family": "PROPERTY", "status": "TAXONOMY_ONLY", "production": "DISABLED"},
    "FINANCIAL_TRANSACTION": {"family": "COMMERCE", "status": "TAXONOMY_ONLY", "production": "DISABLED"},
    "OTHER": {"family": "UNSPECIFIED", "status": "TAXONOMY_ONLY", "production": "DISABLED"},
}


@dataclass(frozen=True)
class MuhurtaRequest:
    local_date: date
    latitude: float
    longitude: float
    timezone_name: str
    event_type: str | None = None

    def validate(self) -> None:
        if not isinstance(self.local_date, date):
            raise TypeError("local_date must be a date")
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        try:
            ZoneInfo(self.timezone_name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"invalid timezone_name: {self.timezone_name}") from exc
        if self.event_type is not None and self.event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported event_type: {self.event_type}")


@dataclass(frozen=True)
class SolarDay:
    local_date: date
    timezone_name: str
    sunrise_local: datetime | None
    sunset_local: datetime | None
    sunrise_status: str
    sunset_status: str
    method_id: str = METHOD_ID
    method_version: str = METHOD_VERSION


def _normalise_degrees(value: float) -> float:
    return value % 360.0


def _solar_event_utc(day: date, latitude: float, longitude: float, rising: bool) -> datetime | None:
    """Return an approximate UTC solar event using the NOAA low-precision model."""
    day_of_year = day.timetuple().tm_yday
    longitude_hour = longitude / 15.0
    hour = 6.0 if rising else 18.0
    approximate_time = day_of_year + ((hour - longitude_hour) / 24.0)
    mean_anomaly = (0.9856 * approximate_time) - 3.289
    true_longitude = _normalise_degrees(
        mean_anomaly
        + (1.916 * math.sin(math.radians(mean_anomaly)))
        + (0.020 * math.sin(math.radians(2 * mean_anomaly)))
        + 282.634
    )
    right_ascension = math.degrees(math.atan(0.91764 * math.tan(math.radians(true_longitude))))
    right_ascension = _normalise_degrees(right_ascension)
    longitude_quadrant = math.floor(true_longitude / 90.0) * 90.0
    right_ascension_quadrant = math.floor(right_ascension / 90.0) * 90.0
    right_ascension = (right_ascension + longitude_quadrant - right_ascension_quadrant) / 15.0

    sin_declination = 0.39782 * math.sin(math.radians(true_longitude))
    cos_declination = math.cos(math.asin(sin_declination))
    cos_hour_angle = (
        math.cos(math.radians(ZENITH_DEGREES))
        - (sin_declination * math.sin(math.radians(latitude)))
    ) / (cos_declination * math.cos(math.radians(latitude)))
    if cos_hour_angle > 1.0:
        return None
    if cos_hour_angle < -1.0:
        return None

    hour_angle = math.degrees(math.acos(cos_hour_angle))
    if rising:
        hour_angle = 360.0 - hour_angle
    hour_angle /= 15.0
    local_mean_time = hour_angle + right_ascension - (0.06571 * approximate_time) - 6.622
    universal_time = (local_mean_time - longitude_hour) % 24.0
    return datetime.combine(day, time.min, tzinfo=timezone.utc) + timedelta(hours=universal_time)


def compute_solar_day(request: MuhurtaRequest) -> SolarDay:
    request.validate()
    tz = ZoneInfo(request.timezone_name)
    sunrise_utc = _solar_event_utc(request.local_date, request.latitude, request.longitude, True)
    sunset_utc = _solar_event_utc(request.local_date, request.latitude, request.longitude, False)

    def align_to_local_date(event_utc: datetime | None) -> datetime | None:
        if event_utc is None:
            return None
        local = event_utc.astimezone(tz)
        day_delta = request.local_date - local.date()
        return event_utc + day_delta

    sunrise_utc = align_to_local_date(sunrise_utc)
    sunset_utc = align_to_local_date(sunset_utc)
    return SolarDay(
        local_date=request.local_date,
        timezone_name=request.timezone_name,
        sunrise_local=sunrise_utc.astimezone(tz) if sunrise_utc else None,
        sunset_local=sunset_utc.astimezone(tz) if sunset_utc else None,
        sunrise_status="AVAILABLE" if sunrise_utc else "NO_SUNRISE_FOR_DATE",
        sunset_status="AVAILABLE" if sunset_utc else "NO_SUNSET_FOR_DATE",
    )


def _decimal_degrees(value: float | int | Decimal, field: str) -> Decimal:
    """Convert an input without inheriting binary float boundary drift."""
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TypeError(f"{field} must be numeric") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result % Decimal("360")


def _rounded_decimal(value: Decimal, places: str = "0.0000000001") -> float:
    return float(value.quantize(Decimal(places)))


def compute_panchanga_facts(
    sun_sidereal_longitude: float | int | Decimal,
    moon_sidereal_longitude: float | int | Decimal,
    local_datetime: datetime,
) -> dict[str, Any]:
    """Return deterministic five-limb facts for a local, aware datetime.

    This is a calculation layer only.  It deliberately emits no auspicious,
    inauspicious, score, ranking, or recommendation field.  Half-open angular
    intervals are used: a value exactly on a boundary belongs to the next
    segment, while 360 degrees wraps to zero.
    """
    if not isinstance(local_datetime, datetime) or local_datetime.tzinfo is None:
        raise ValueError("local_datetime must be timezone-aware")
    sun = _decimal_degrees(sun_sidereal_longitude, "sun_sidereal_longitude")
    moon = _decimal_degrees(moon_sidereal_longitude, "moon_sidereal_longitude")
    full_circle = Decimal("360")
    tithi_size = Decimal("12")
    karana_size = Decimal("6")
    limb_size = full_circle / Decimal("27")
    elongation = (moon - sun) % full_circle
    combined = (moon + sun) % full_circle
    tithi_index = min(int(elongation / tithi_size), 29)
    karana_number = min(int(elongation / karana_size) + 1, 60)
    yoga_index = min(int(combined / limb_size), 26)
    nakshatra_index = min(int(moon / limb_size), 26)
    within_nakshatra = moon - (Decimal(nakshatra_index) * limb_size)
    pada_size = limb_size / Decimal("4")
    pada = min(int(within_nakshatra / pada_size) + 1, 4)

    if karana_number == 1:
        karana_name, karana_type = "Kimstughna", "fixed"
    elif karana_number <= 57:
        karana_name, karana_type = KARANA_MOVABLE[(karana_number - 2) % 7], "movable"
    elif karana_number == 58:
        karana_name, karana_type = "Shakuni", "fixed"
    elif karana_number == 59:
        karana_name, karana_type = "Chatushpada", "fixed"
    else:
        karana_name, karana_type = "Naga", "fixed"

    vara_index = (local_datetime.weekday() + 1) % 7
    return {
        "calculation_method": {
            "method_id": P032_CALCULATION_METHOD_ID,
            "version": P032_CALCULATION_METHOD_VERSION,
            "source_status": P032_SOURCE_STATUS,
            "boundary_policy": "HALF_OPEN_NEXT_SEGMENT;360_WRAP_TO_ZERO",
            "source_rule_ids": [
                "P032-CALC-VARA-001",
                "P032-CALC-TITHI-001",
                "P032-CALC-NAKSHATRA-001",
                "P032-CALC-YOGA-001",
                "P032-CALC-KARANA-001",
            ],
        },
        "local_datetime": local_datetime.isoformat(),
        "longitudes": {
            "sun_sidereal": _rounded_decimal(sun),
            "moon_sidereal": _rounded_decimal(moon),
            "moon_sun_elongation": _rounded_decimal(elongation),
            "sun_moon_sum": _rounded_decimal(combined),
        },
        "vara": {
            "index": vara_index,
            "name": VARA_DAYS[vara_index],
            "lord": VARA_LORDS[vara_index],
        },
        "tithi": {
            "index": tithi_index,
            "number": tithi_index + 1,
            "name": TITHI_NAMES[tithi_index],
            "phase": "Shukla (waxing)" if tithi_index < 15 else "Krishna (waning)",
            "boundary_start_degrees": _rounded_decimal(Decimal(tithi_index) * tithi_size),
            "boundary_end_degrees": _rounded_decimal(Decimal(tithi_index + 1) * tithi_size),
        },
        "nakshatra": {
            "index": nakshatra_index,
            "number": nakshatra_index + 1,
            "name": NAKSHATRA_NAMES[nakshatra_index],
            "pada": pada,
            "lord": NAKSHATRA_LORDS[nakshatra_index],
            "boundary_start_degrees": _rounded_decimal(Decimal(nakshatra_index) * limb_size),
            "boundary_end_degrees": _rounded_decimal(Decimal(nakshatra_index + 1) * limb_size),
        },
        "yoga": {
            "index": yoga_index,
            "number": yoga_index + 1,
            "name": YOGA_NAMES[yoga_index],
            "boundary_start_degrees": _rounded_decimal(Decimal(yoga_index) * limb_size),
            "boundary_end_degrees": _rounded_decimal(Decimal(yoga_index + 1) * limb_size),
        },
        "karana": {
            "number": karana_number,
            "name": karana_name,
            "type": karana_type,
            "boundary_start_degrees": _rounded_decimal(Decimal(karana_number - 1) * karana_size),
            "boundary_end_degrees": _rounded_decimal(Decimal(karana_number) * karana_size),
        },
    }


def event_taxonomy() -> dict[str, dict[str, Any]]:
    """Return event families without asserting universal auspiciousness."""
    return {key: dict(value) for key, value in EVENT_TAXONOMY.items()}


def atomic_rule_registry() -> list[dict[str, Any]]:
    """Return source/trust metadata for executable calculation primitives."""
    return [
        {
            "rule_id": "P032-CALC-VARA-001",
            "concept": "LOCAL_WEEKDAY",
            "rule_type": "CALCULATION_FACT",
            "classification": "CLASSICAL_DERIVED",
            "source": "EXISTING_PANCHANGA_RUNTIME_CONTRACT",
            "status": "VALIDATED_KNOWLEDGE",
            "production_activation": "FACTS_ONLY",
        },
        {
            "rule_id": "P032-CALC-TITHI-001",
            "concept": "MOON_SUN_ELONGATION_12_DEGREE_SEGMENTS",
            "rule_type": "CALCULATION_FACT",
            "classification": "CLASSICAL_DERIVED",
            "source": "BRIHAT_SAMHITA_CH99;EXISTING_PANCHANGA_RUNTIME_CONTRACT",
            "status": "VALIDATED_KNOWLEDGE",
            "production_activation": "FACTS_ONLY",
        },
        {
            "rule_id": "P032-CALC-NAKSHATRA-001",
            "concept": "MOON_27_LUNAR_MANSIONS_AND_PADA",
            "rule_type": "CALCULATION_FACT",
            "classification": "CLASSICAL_DERIVED",
            "source": "P016_NAKSHATRA_CONTRACT;EXISTING_PANCHANGA_RUNTIME_CONTRACT",
            "status": "VALIDATED_KNOWLEDGE",
            "production_activation": "FACTS_ONLY",
        },
        {
            "rule_id": "P032-CALC-YOGA-001",
            "concept": "SUN_MOON_SUM_27_SEGMENTS",
            "rule_type": "CALCULATION_FACT",
            "classification": "CLASSICAL_DERIVED",
            "source": "EXISTING_PANCHANGA_RUNTIME_CONTRACT",
            "status": "VALIDATED_KNOWLEDGE",
            "production_activation": "FACTS_ONLY",
        },
        {
            "rule_id": "P032-CALC-KARANA-001",
            "concept": "SIX_DEGREE_HALF_TITHI_SEQUENCE",
            "rule_type": "CALCULATION_FACT",
            "classification": "CLASSICAL_DERIVED",
            "source": "BRIHAT_SAMHITA_CH99;EXISTING_PANCHANGA_RUNTIME_CONTRACT",
            "status": "VALIDATED_KNOWLEDGE",
            "production_activation": "FACTS_ONLY",
        },
        {
            "rule_id": "P032-RULE-EVENT-SCOPED-001",
            "concept": "SCOPED_EVENT_ACTION_FAMILIES",
            "rule_type": "EVENT_RULE_REFERENCE",
            "classification": "CLASSICAL_EXPLICIT",
            "source": "BRIHAT_SAMHITA_CH97_06_12;CH98_02_03;CH99_03_08",
            "status": "VALIDATED_KNOWLEDGE",
            "production_activation": "DISABLED",
        },
        {
            "rule_id": "P032-RULE-TARABALA-001",
            "concept": "TARA_BALA",
            "rule_type": "PERSONAL_RULE",
            "classification": "UNRESOLVED",
            "source": "MUHURTA_CHINTAMANI_CANDIDATE_SCAN",
            "status": "RESEARCH_CANDIDATE",
            "production_activation": "DISABLED",
        },
        {
            "rule_id": "P032-RULE-CHANDRABALA-001",
            "concept": "CHANDRA_BALA",
            "rule_type": "PERSONAL_RULE",
            "classification": "UNRESOLVED",
            "source": "MUHURTA_CHINTAMANI_CANDIDATE_SCAN",
            "status": "RESEARCH_CANDIDATE",
            "production_activation": "DISABLED",
        },
        {
            "rule_id": "P032-RULE-SCORE-001",
            "concept": "GENERAL_AUSPICIOUSNESS_SCORE",
            "rule_type": "COMPOSITE_SCORE",
            "classification": "UNRESOLVED",
            "source": "NO_SINGLE_VERIFIED_METHOD",
            "status": "DEFERRED",
            "production_activation": "DISABLED",
        },
    ]


def evaluate_atomic_rules(facts: Mapping[str, Any], event_type: str | None = None) -> list[dict[str, Any]]:
    """Evaluate only structural validity and applicability; never score or recommend."""
    results = []
    fact_keys = {
        "LOCAL_WEEKDAY": "vara",
        "MOON_SUN_ELONGATION_12_DEGREE_SEGMENTS": "tithi",
        "MOON_27_LUNAR_MANSIONS_AND_PADA": "nakshatra",
        "SUN_MOON_SUM_27_SEGMENTS": "yoga",
        "SIX_DEGREE_HALF_TITHI_SEQUENCE": "karana",
    }
    for rule in atomic_rule_registry()[:6]:
        if rule["rule_type"] == "EVENT_RULE_REFERENCE":
            applicable = event_type in EVENT_TYPES if event_type is not None else False
            status = "REFERENCE_ONLY" if applicable else "NOT_APPLICABLE"
        else:
            applicable = fact_keys.get(rule["concept"]) in facts
            status = "FACT_VALID" if applicable else "FACT_NOT_PRESENT"
        results.append({
            "rule_id": rule["rule_id"],
            "status": status,
            "applicable": applicable,
            "source_status": rule["status"],
            "recommendation": "NOT_AUTHORIZED",
            "score": None,
        })
    return results


def build_candidate_windows(
    start: datetime,
    end: datetime,
    transition_points: Iterable[datetime | Mapping[str, Any]],
    interval_evidence: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Split a research interval at explicit transitions without ranking it."""
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("window boundaries must be timezone-aware")
    if end <= start:
        raise ValueError("window end must be after start")
    points: list[tuple[datetime, dict[str, Any]]] = []
    for item in transition_points:
        if isinstance(item, datetime):
            point, metadata = item, {}
        else:
            point, metadata = item["at"], dict(item)
        if point.tzinfo is None:
            raise ValueError("transition points must be timezone-aware")
        if start < point < end:
            points.append((point, metadata))
    points.sort(key=lambda item: item[0].astimezone(timezone.utc))
    boundaries = [start] + [item[0] for item in points] + [end]
    evidence = list(interval_evidence or [])
    windows = []
    for index, (left, right) in enumerate(zip(boundaries, boundaries[1:])):
        transition = points[index][1] if index < len(points) else {}
        windows.append({
            "window_id": f"P032-WINDOW-{index + 1:03d}",
            "start": left.isoformat(),
            "end": right.isoformat(),
            "transition": transition,
            "evidence": dict(evidence[index]) if index < len(evidence) else {},
            "selection_status": "INACTIVE",
            "recommendation_status": "NOT_AUTHORIZED",
            "score": None,
        })
    return windows


def build_muhurta_foundation(request: MuhurtaRequest) -> dict:
    """Return facts and explicit gates without issuing an electional result."""
    solar_day = compute_solar_day(request)
    return {
        "domain": "MUHURTA_FOUNDATION",
        "activation_status": "INACTIVE",
        "recommendation_status": "NOT_IMPLEMENTED",
        "event_type": request.event_type,
        "panchanga_calculation_contract": {
            "status": "AVAILABLE_AS_SEPARATE_FACT_LAYER",
            "method_id": P032_CALCULATION_METHOD_ID,
            "method_version": P032_CALCULATION_METHOD_VERSION,
            "requires_sidereal_sun_moon_longitudes": True,
        },
        "solar_day": {
            "local_date": solar_day.local_date.isoformat(),
            "timezone_name": solar_day.timezone_name,
            "sunrise_local": solar_day.sunrise_local.isoformat() if solar_day.sunrise_local else None,
            "sunset_local": solar_day.sunset_local.isoformat() if solar_day.sunset_local else None,
            "sunrise_status": solar_day.sunrise_status,
            "sunset_status": solar_day.sunset_status,
        },
        "dependencies": {
            "panchanga_limbs": "FACT_LAYER_AVAILABLE;NO_SELECTION",
            "event_rules": "NOT_IMPLEMENTED",
            "tarabala": "NOT_IMPLEMENTED",
            "chandrabala": "NOT_IMPLEMENTED",
            "electional_scoring": "NOT_IMPLEMENTED",
            "prashna": "OUT_OF_SCOPE",
        },
        "provenance": {
            "method_id": METHOD_ID,
            "method_version": METHOD_VERSION,
            "calculation_scope": "SOLAR_DAY_FACTS_ONLY",
            "source_status": "CLASSICAL_EVENT_RULES_SCOPED; PERSONAL_BALA_UNVERIFIED",
        },
    }
