"""Transition discovery for the bounded Muhurta window-search layer.

The adapter deliberately reuses the canonical Kundli/Swiss Ephemeris
position path and the existing P032 fact boundaries.  It does not contain
Muhurta recommendation rules, scoring, or a second Panchanga implementation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from engines.ai.knowledge.muhurta_foundation import compute_panchanga_facts
from engines.intelligence.kundli_engine import KundliEngine


TRANSITION_SOURCE_ID = "VEDA_CANONICAL_KUNDLI_P032_TRANSITION_ADAPTER"
TRANSITION_SOURCE_VERSION = "1.0.0"
TRANSITION_CLASSIFICATION = "CALCULATED_TRANSITION"
_EPSILON_SECONDS = 1.0
_BISECTION_ITERATIONS = 52


class TransitionSourceError(RuntimeError):
    """The existing astronomical position dependency cannot provide facts."""


_ENGINE: KundliEngine | None = None


def _engine() -> KundliEngine:
    global _ENGINE
    if _ENGINE is None:
        try:
            _ENGINE = KundliEngine()
        except Exception as exc:  # pragma: no cover - environment dependency
            raise TransitionSourceError(f"canonical position engine unavailable: {exc}") from exc
    return _ENGINE


def _julian_day(dt: datetime) -> float:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise TransitionSourceError("transition timestamps must be timezone-aware")
    utc = dt.astimezone(timezone.utc)
    swe = _engine()._swe  # noqa: SLF001 - canonical existing engine surface
    return swe.julday(
        utc.year,
        utc.month,
        utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3_600_000_000.0,
    )


def position_facts(dt: datetime) -> dict[str, Any]:
    """Return canonical sidereal Sun/Moon positions and P032 facts."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise TransitionSourceError("position timestamp must be timezone-aware")
    extended = _engine()._planet_positions_extended(_julian_day(dt))  # noqa: SLF001
    try:
        sun = extended["Sun"]
        moon = extended["Moon"]
        facts = compute_panchanga_facts(sun["longitude"], moon["longitude"], dt)
    except (KeyError, TypeError, ValueError) as exc:
        raise TransitionSourceError(f"P032 facts could not be computed: {exc}") from exc
    return {
        "sun_sidereal_longitude": float(sun["longitude"]),
        "moon_sidereal_longitude": float(moon["longitude"]),
        "sun_speed_deg_per_day": float(sun["longitude_speed_deg_per_day"]),
        "moon_speed_deg_per_day": float(moon["longitude_speed_deg_per_day"]),
        "p032_facts": facts,
        "source": TRANSITION_SOURCE_ID,
        "version": TRANSITION_SOURCE_VERSION,
    }


def _angle(dt: datetime, factor: str) -> float:
    values = position_facts(dt)
    if factor in {"TITHI", "KARANA"}:
        return (values["moon_sidereal_longitude"] - values["sun_sidereal_longitude"]) % 360.0
    if factor == "NAKSHATRA":
        return values["moon_sidereal_longitude"] % 360.0
    raise TransitionSourceError(f"unsupported transition factor: {factor}")


def _speed(values: Mapping[str, Any], factor: str) -> float:
    if factor in {"TITHI", "KARANA"}:
        return float(values["moon_speed_deg_per_day"]) - float(values["sun_speed_deg_per_day"])
    return float(values["moon_speed_deg_per_day"])


def _forward_distance(start: float, current: float) -> float:
    return (current - start) % 360.0


def _next_event(start: datetime, end: datetime, factor: str) -> datetime | None:
    values = position_facts(start)
    current = _angle(start, factor)
    step = {"TITHI": 12.0, "KARANA": 6.0, "NAKSHATRA": 360.0 / 27.0}[factor]
    index = int(current / step)
    boundary = ((index + 1) * step) % 360.0
    distance = (boundary - current) % 360.0
    if distance <= 1e-9:
        distance = step
    speed = _speed(values, factor)
    if speed <= 1e-8:
        return None
    estimate = max(2.0, distance / speed * 86_400.0)
    low = start
    high = min(end, start + timedelta(seconds=estimate * 1.35 + 2.0))
    if high <= low:
        return None

    # Establish a bracket using the already-available motion speed rather than
    # a fixed 15-minute/hourly sampling grid.
    for _ in range(8):
        if _forward_distance(current, _angle(high, factor)) >= distance:
            break
        expanded = high + (high - low)
        if expanded >= end:
            high = end
            break
        high = expanded
    if _forward_distance(current, _angle(high, factor)) + 1e-8 < distance:
        return None

    for _ in range(_BISECTION_ITERATIONS):
        middle = low + (high - low) / 2
        if _forward_distance(current, _angle(middle, factor)) >= distance:
            high = middle
        else:
            low = middle
    event = high
    if not start < event < end:
        return None
    return event


def _factor_events(start: datetime, end: datetime, factor: str) -> list[datetime]:
    events: list[datetime] = []
    cursor = start
    # P032's smallest relevant angular interval is bounded; this guard is a
    # safety limit, not a sampling policy.
    for _ in range(200):
        event = _next_event(cursor, end, factor)
        if event is None:
            break
        events.append(event)
        cursor = event + timedelta(seconds=_EPSILON_SECONDS)
        if cursor >= end:
            break
    return events


def discover_transitions(
    start: datetime,
    end: datetime,
    factors: Iterable[str] = ("TITHI", "KARANA", "NAKSHATRA"),
) -> list[dict[str, Any]]:
    """Discover relevant P032 factor boundaries in a bounded interval."""
    if start.tzinfo is None or end.tzinfo is None or start.utcoffset() is None or end.utcoffset() is None:
        raise TransitionSourceError("transition search requires aware datetimes")
    if end <= start:
        raise TransitionSourceError("transition search end must be after start")
    events: list[dict[str, Any]] = []
    for factor in sorted(set(factors)):
        for event in _factor_events(start, end, factor):
            events.append({
                "at": event.isoformat(),
                "kind": f"{factor}_BOUNDARY",
                "factor": factor,
                "classification": TRANSITION_CLASSIFICATION,
                "source": TRANSITION_SOURCE_ID,
                "source_version": TRANSITION_SOURCE_VERSION,
            })
    events.sort(key=lambda item: (datetime.fromisoformat(item["at"]).astimezone(timezone.utc), item["kind"]))
    return events
