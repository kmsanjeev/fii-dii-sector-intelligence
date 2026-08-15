"""Resolve a historical civil-time offset from an IANA timezone snapshot."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def resolve_historical_timezone(zone_id: str, local_date: str) -> dict[str, str]:
    """Return the source-preserving offset and method for a historical date.

    This does not infer a location or silently choose a timezone. Callers must
    supply a governed IANA zone and retain the tzdata version used externally.
    """
    zone = ZoneInfo(zone_id)
    instant = datetime.fromisoformat(f"{local_date}T12:00:00").replace(tzinfo=zone)
    offset = instant.utcoffset()
    if offset is None:
        raise ValueError(f"No historical offset available for {zone_id} on {local_date}")
    seconds = int(offset.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return {
        "timezone_method": "IANA_HISTORICAL_ZONE",
        "timezone_source": zone_id,
        "historical_offset": f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}",
        "confidence": "HIGH",
        "ambiguity": "NOT_ASSESSED_BEYOND_ZONE_RULES",
    }
