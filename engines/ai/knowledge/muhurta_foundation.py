"""Governed Muhurta foundation primitives.

This module intentionally stops at deterministic date/location and solar-day
facts. It does not select auspicious times, score events, implement Bala
systems, or provide Prashna behavior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
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


def build_muhurta_foundation(request: MuhurtaRequest) -> dict:
    """Return facts and explicit gates without issuing an electional result."""
    solar_day = compute_solar_day(request)
    return {
        "domain": "MUHURTA_FOUNDATION",
        "activation_status": "INACTIVE",
        "recommendation_status": "NOT_IMPLEMENTED",
        "event_type": request.event_type,
        "solar_day": {
            "local_date": solar_day.local_date.isoformat(),
            "timezone_name": solar_day.timezone_name,
            "sunrise_local": solar_day.sunrise_local.isoformat() if solar_day.sunrise_local else None,
            "sunset_local": solar_day.sunset_local.isoformat() if solar_day.sunset_local else None,
            "sunrise_status": solar_day.sunrise_status,
            "sunset_status": solar_day.sunset_status,
        },
        "dependencies": {
            "panchanga_limbs": "BIRTH_TIME_ONLY_REUSED",
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
